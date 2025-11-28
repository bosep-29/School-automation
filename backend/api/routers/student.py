from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.utils.user_utils import authorize_user
from api.models.student import Student
from api.database.mongodb import db
from bson.objectid import ObjectId
from fastapi_pagination import Page, paginate, Params

router = APIRouter()

@router.get("/", response_model=Page[Student])
async def get_students(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["students"]
    students_cursor = collection.find()
    students = [user for user in students_cursor]
    return paginate(students, params)

@router.post("/")
async def create_student(student: Student, authorized: bool = Depends(authorize_user)):
    try:
        user_collection = db["users"]
        existing_user = user_collection.find_one({"_id": ObjectId(student.user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User with the user ID does not exists")
        if existing_user["user_type"] is not 1:
            raise HTTPException(status_code=400, detail="User is not a student")
        group_collection = db["students"]
        existing_groups = group_collection.find({"group_id": {"$in": student.groups}})
        existing_group_ids = {group['group_id'] for group in existing_groups}
        missing_group_ids = set(student.groups) - existing_group_ids

        if missing_group_ids:
            raise HTTPException(status_code=404,
                                detail=f"One or more groups with the following IDs do not exist: {missing_group_ids}")

        
        collection = db["students"]
        existing_employee = collection.find_one({"user_id": student.user_id})
        if existing_employee:
            raise HTTPException(status_code=400, detail="Employee with the same user ID already exists")
        result = collection.insert_one(student.dict())
        return {"message": "Student created successfully", "student_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.get("/{student_id}")
async def read_student(student_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["students"]
        student = collection.find_one({"_id": ObjectId(student_id)})
        if student:
            student["_id"] = str(student["_id"])
            return student
        raise HTTPException(status_code=404, detail="Student not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.put("/{student_id}")
async def update_student(student_id: str, student_data: Student, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["students"]
        result = collection.update_one({"_id": ObjectId(student_id)}, {"$set": student_data.dict()})
        if result.modified_count == 1:
            return {"message": "Student updated successfully"}
        raise HTTPException(status_code=404, detail="Student not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.delete("/{student_id}")
async def delete_student(student_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["students"]
        result = collection.delete_one({"_id": ObjectId(student_id)})
        if result.deleted_count == 1:
            return {"message": "Student deleted successfully"}
        raise HTTPException(status_code=404, detail="Student not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)