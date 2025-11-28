from fastapi import APIRouter, HTTPException, Depends, Body
from api.database.mongodb import db
from bson.objectid import ObjectId
from api.models.assessment import Assessment
from fastapi_pagination import Page, paginate, Params
from api.utils.user_utils import authorize_user
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/", response_model=Page[Assessment])
async def get_assessment(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["assessment"]
    assessment_cursor = collection.find()
    assessment = [assessment for assessment in assessment_cursor]
    return paginate(assessment, params)

@router.post("/")
async def create_assessment(assessment: Assessment, authorized: bool = Depends(authorize_user)):
    try:
        subject_collection = db["subjects"]
        existing_subject = subject_collection.find_one({"subject_id": assessment.subject_id})
        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject with the ID not found")
        collection = db["assessment"]
        existing_assessment = collection.find_one({"assessment_id": assessment.assessment_id, "subject_id": assessment.subject_id})
        if existing_assessment:
            raise HTTPException(status_code=400, detail="Assessment already present")
        same_subject_assessments = list(collection.find({"subject_id": assessment.subject_id}))
        total_contribution = sum(float(record["contribution_percentage"]) for record in same_subject_assessments)
        if total_contribution + float(assessment.contribution_percentage) > 100:
            raise HTTPException(status_code=400, detail="Total Contribution exceeds 100%")
        result = collection.insert_one(assessment.dict())
        return {"message": "Assessment created successfully", "assessment_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.get("/search")
async def get_filtered_assessment(filters: dict = Body(...), authorized: bool = Depends(authorize_user)):
    try:
        collection = db["assessment"]
        assessment_records = list(collection.find(filters))
        for record in assessment_records:
            record["_id"] = str(record["_id"])
        return list(assessment_records)
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.get("/{assessment_id}")
async def read_assessment(assessment_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["assessment"]
        assessment = collection.find_one({"_id": ObjectId(assessment_id)})
        if assessment:
            assessment["_id"] = str(assessment["_id"])
            return assessment
        raise HTTPException(status_code=404, detail="Assessment not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)
    
@router.get("/search/{subject_id}")
async def read_assessments_by_subject_id(subject_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["assessment"]
        assessment_records = list(collection.find({"subject_id": subject_id}))
        total_contribution = 0.00
        for record in assessment_records:
            record["_id"] = str(record["_id"])
            total_contribution += float(record["contribution_percentage"])
        result = {"assessment_records": assessment_records,"total_contribution": total_contribution}
        return result
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)
    
@router.put("/{assessment_id}")
async def update_assessment(assessment_id: str, assessment_data: Assessment, authorized: bool = Depends(authorize_user)):
    try:
        subject_collection = db["subjects"]
        existing_subject = subject_collection.find_one({"subject_id": assessment_data.subject_id})
        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject with the ID not found")
        collection = db["assessment"]
        old_assessment = collection.find_one({"_id": ObjectId(assessment_id)})
        if old_assessment["assessment_id"] != assessment_data.assessment_id or old_assessment["subject_id"] != assessment_data.subject_id:
            existing_assessment = collection.find_one({"assessment_id": assessment_data.assessment_id, "subject_id": assessment_data.subject_id})
            if existing_assessment:
                raise HTTPException(status_code=400, detail="Assessment already present")
        same_subject_assessments = list(collection.find({"subject_id": assessment_data.subject_id}))
        total_contribution = sum(
            float(record["contribution_percentage"])
            for record in same_subject_assessments
            if str(record["_id"]) != assessment_id)
        if total_contribution + float(assessment_data.contribution_percentage) > 100:
            raise HTTPException(status_code=400, detail="Total Contribution exceeds 100%")
        result = collection.update_one({"_id": ObjectId(assessment_id)}, {"$set": assessment_data.dict()})
        if result.modified_count == 1:
            return {"message": "Assessment updated successfully"}
        raise HTTPException(status_code=404, detail="Assessment not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)
    
@router.delete("/{assessment_id}")
async def delete_assessment(assessment_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["assessment"]
        result = collection.delete_one({"_id": ObjectId(assessment_id)})
        if result.deleted_count == 1:
            return {"message": "Assessment deleted successfully"}
        raise HTTPException(status_code=404, detail="Assessment not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)