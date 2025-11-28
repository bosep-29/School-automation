from fastapi import APIRouter, HTTPException, Depends, Body
from api.database.mongodb import db
from bson.objectid import ObjectId
from api.models.marks import Marks
from api.models.marks_update_assessment_dist import MarksUpdateAssessmentDict
from fastapi_pagination import Page, paginate, Params
from api.utils.user_utils import authorize_user
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/", response_model=Page[Marks])
async def get_marks(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["marks"]
    marks_cursor = collection.find()
    marks = [marks for marks in marks_cursor]
    return paginate(marks, params)

@router.post("/")
async def create_marks(marks: Marks, authorized: bool = Depends(authorize_user)):
    try:
        subject_collection = db["subjects"]
        existing_subject = subject_collection.find_one({"subject_id": marks.subject_id})
        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject with the ID not found")
        student_collection = db["students"]
        existing_student = student_collection.find_one({"_id": ObjectId(marks.student_id)})
        if not existing_student:
            raise HTTPException(status_code=404, detail="Student with the ID not found")
        collection = db["marks"]
        existing_marks = collection.find_one({"subject_id": marks.subject_id, "student_id": marks.student_id})
        if existing_marks:
            raise HTTPException(status_code=400, detail="Marks already present")
        assessment_collection = db["assessment"]
        total = 0.0
        for assessment in marks.assessments:
            for key, value in assessment.items():
                existing_assessment = assessment_collection.find_one({"_id": ObjectId(str(key))})
                if not existing_assessment:
                    raise HTTPException(status_code=404, detail="Assessment with the ID not found")
                if existing_assessment["subject_id"] != marks.subject_id:
                    raise HTTPException(status_code=400, detail="Assessment is not of the same subject")
                assessment_score = float(value)
                if existing_assessment["assessment_max_marks"] < assessment_score:
                    raise HTTPException(status_code=400, detail="Assessment marks exceeding maximum marks")
                total += (assessment_score / existing_assessment["assessment_max_marks"]) * int(existing_assessment["contribution_percentage"])
        marks.total = total
        result = collection.insert_one(marks.dict())
        return {"message": "Marks created successfully", "marks_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.get("/{marks_id}")
async def read_marks(marks_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["marks"]
        marks = collection.find_one({"_id": ObjectId(marks_id)})
        if marks:
            marks["_id"] = str(marks["_id"])
            return marks
        raise HTTPException(status_code=404, detail="Marks not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.put("/{marks_id}")
async def update_marks(marks_id: str, marks_data: Marks, authorized: bool = Depends(authorize_user)):
    try:
        subject_collection = db["subjects"]
        existing_subject = subject_collection.find_one({"subject_id": marks_data.subject_id})
        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject with the ID not found")
        student_collection = db["students"]
        existing_student = student_collection.find_one({"_id": ObjectId(marks_data.student_id)})
        if not existing_student:
            raise HTTPException(status_code=404, detail="Student with the ID not found")
        collection = db["marks"]
        old_marks = collection.find_one({"_id": ObjectId(marks_id)})
        if old_marks["subject_id"] != marks_data.subject_id or old_marks["student_id"] != marks_data.student_id:
            existing_marks = collection.find_one({"student_id": marks_data.student_id, "subject_id": marks_data.subject_id})
            if existing_marks:
                raise HTTPException(status_code=400, detail="Marks already present")
        assessment_collection = db["assessment"]
        total = 0.0
        for assessment in marks_data.assessments:
            for key, value in assessment.items():
                existing_assessment = assessment_collection.find_one({"_id": ObjectId(str(key))})
                if not existing_assessment:
                    raise HTTPException(status_code=404, detail="Assessment with the ID not found")
                if existing_assessment["subject_id"] != marks_data.subject_id:
                    raise HTTPException(status_code=400, detail="Assessment is not of the same subject")
                assessment_score = float(value)
                if existing_assessment["assessment_max_marks"] < assessment_score:
                    raise HTTPException(status_code=400, detail="Assessment marks exceeding maximum marks")
                total += (assessment_score / existing_assessment["assessment_max_marks"]) * int(existing_assessment["contribution_percentage"])
        marks_data.total = total
        result = collection.update_one({"_id": ObjectId(marks_id)}, {"$set": marks_data.dict()})
        if result.modified_count == 1:
            return {"message": "Marks updated successfully"}
        raise HTTPException(status_code=404, detail="Marks not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.put("/{marks_id}/update_assessments")
async def update_marks(marks_id: str, assessments_data: MarksUpdateAssessmentDict, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["marks"]
        existing_marks = collection.find_one({"_id": ObjectId(marks_id)})
        if not existing_marks:
            raise HTTPException(status_code=404, detail="Marks with Id not found")
        assessment_collection = db["assessment"]
        total = existing_marks["total"]
        for key in assessments_data.assessments:
            value = assessments_data.assessments[key]
            if key in existing_marks["assessments"]:
                continue
            existing_assessment = assessment_collection.find_one({"_id": ObjectId(str(key))})
            if not existing_assessment:
                raise HTTPException(status_code=404, detail="Assessment with the ID not found")
            if existing_assessment["subject_id"] != existing_marks["subject_id"]:
                raise HTTPException(status_code=400, detail="Assessment is not of the same subject")
            assessment_score = float(value)
            if existing_assessment["assessment_max_marks"] < assessment_score:
                raise HTTPException(status_code=400, detail="Assessment marks exceeding maximum marks")
            total += (assessment_score / existing_assessment["assessment_max_marks"]) * int(existing_assessment["contribution_percentage"])
            existing_marks["assessments"].append({key: value})
        existing_marks["total"] = total
        result = collection.update_one({"_id": ObjectId(marks_id)}, {"$set": existing_marks})
        if result.modified_count == 1:
            return {"message": "Marks updated successfully"}
        raise HTTPException(status_code=404, detail="Marks not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)
    
@router.delete("/{marks_id}")
async def delete_marks(marks_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["marks"]
        result = collection.delete_one({"_id": ObjectId(marks_id)})
        if result.deleted_count == 1:
            return {"message": "Marks deleted successfully"}
        raise HTTPException(status_code=404, detail="Marks not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)