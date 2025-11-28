from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.utils.user_utils import authorize_user
from api.models.subject import Subject
from api.database.mongodb import db
from bson.objectid import ObjectId
from fastapi_pagination import Page, paginate, Params

router = APIRouter()

@router.get("/", response_model=Page[Subject])
async def get_subjects(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["subjects"]
    subjects_cursor = collection.find()
    subjects = [subject for subject in subjects_cursor]
    return paginate(subjects, params)

@router.post("/")
async def create_subject(subject: Subject, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["subjects"]
        existing_subject = collection.find_one({"subject_id": subject.subject_id})
        if existing_subject:
            raise HTTPException(status_code=400, detail="Subject with the same ID already exists")
        result = collection.insert_one(subject.dict())
        return {"message": "Subject created successfully", "subject_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.get("/{subject_id}")
async def read_subject(subject_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["subjects"]
        subject = collection.find_one({"_id": ObjectId(subject_id)})
        if subject:
            subject["_id"] = str(subject["_id"])
            return subject
        raise HTTPException(status_code=404, detail="Subject not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.put("/{subject_id}")
async def update_subject(subject_id: str, updated_subject: Subject, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["subjects"]
        existing_subject = collection.find_one({"subject_id": updated_subject.subject_id})
        if existing_subject:
            raise HTTPException(status_code=400, detail="Subject with same subject ID already exists")
        result = collection.update_one({"_id": ObjectId(subject_id)}, {"$set": updated_subject.dict()})
        if result.modified_count > 0:
            return {"message": "Subject updated successfully"}
        raise HTTPException(status_code=404, detail="Subject not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.delete("/{subject_id}")
async def delete_subject(subject_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["subjects"]
        result = collection.delete_one({"_id": ObjectId(subject_id)})
        if result.deleted_count == 1:
            return {"message": "Subject deleted successfully"}
        raise HTTPException(status_code=404, detail="Subject not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)