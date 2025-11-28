from fastapi import APIRouter, HTTPException, Depends, Header, Body
from fastapi.responses import JSONResponse
from api.database.mongodb import db
from api.models.attendance import Attendance
from api.models.attendance_multiple_student_id import AttendanceMultipleStudentId
from api.utils.user_utils import authorize_user, verify_token
from bson.objectid import ObjectId
from typing import Optional
from fastapi_pagination import Page, paginate, Params

router = APIRouter()

@router.get("/", response_model=Page[Attendance])
async def get_attendance(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["attendance"]
    attendance_cursor = collection.find()
    attendance = [attendance for attendance in attendance_cursor]
    return paginate(attendance, params)

@router.post("/")
async def create_attendance(multiple_attendance: AttendanceMultipleStudentId, authorization: str = Header(...), authorized: bool = Depends(authorize_user)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = verify_token(token)
        marked_by = payload.get('org_id')
        collection = db["attendance"]
        employee_collection = db["employees"]
        existing_employee = employee_collection.find_one({"_id": ObjectId(marked_by)})
        if not existing_employee:
            raise HTTPException(status_code=404, detail="Employee does not exists")
        group_collection = db["groups"]
        existing_group = group_collection.find_one({"_id": ObjectId(multiple_attendance.group_id)})
        if not existing_group:
            raise HTTPException(status_code=404, detail="Group does not exists")
        student_collection = db["students"]
        for student_id, attendance_type in multiple_attendance.student_ids.items():
            existing_student = student_collection.find_one({"_id": ObjectId(student_id)})
            if not existing_student:
                raise HTTPException(status_code=404, detail="Student does not exists")
            for hour in multiple_attendance.hours:
                existing_record = collection.find_one({"student_id": student_id, "hours": multiple_attendance.hours})
                if existing_record:
                    raise HTTPException(status_code=400, detail="Attendance record for this student and hours already exists")
                attendance_data = {
                    "student_id": student_id,
                    "date": multiple_attendance.date,
                    "timestamp": multiple_attendance.timestamp,
                    "marked_by": marked_by,
                    "hours": hour,
                    "type_of_attendance": attendance_type,
                    "group_id": multiple_attendance.group_id
                }
                result = collection.insert_one(attendance_data)
        return {"message": "Attendance created successfully", "attendance_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)
    
@router.get("/search")
async def get_filtered_attendance(filters: dict = Body(...), authorized: bool = Depends(authorize_user)):
    try:
        collection = db["attendance"]
        attendance_records = list(collection.find(filters))
        for record in attendance_records:
            record["_id"] = str(record["_id"])
        return list(attendance_records)
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.get("/{attendance_id}")
async def read_attendance(attendance_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["attendance"]
        attendance = collection.find_one({"_id": ObjectId(attendance_id)})
        if attendance:
            attendance["_id"] = str(attendance["_id"])
            return attendance
        raise HTTPException(status_code=404, detail="Attendance not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.put("/{attendance_id}")
async def update_attendance(attendance_id: str, updated_attendance: Attendance, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["attendance"]
        attendance = collection.find_one({"_id": ObjectId(attendance_id)})
        if attendance["marked_by"] != updated_attendance.marked_by:
            raise HTTPException(status_code=400, detail="Only the same employee can update the attendance")
        group_collection = db["groups"]
        existing_group = group_collection.find_one({"_id": ObjectId(updated_attendance.group_id)})
        if not existing_group:
            raise HTTPException(status_code=404, detail="Group does not exists")
        result = collection.update_one({"_id": ObjectId(attendance_id)}, {"$set": updated_attendance.dict()})
        if result.modified_count == 1:
            return {"message": "Attendance updated successfully"}
        raise HTTPException(status_code=404, detail="Attendance not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.delete("/{attendance_id}")
async def delete_attendance(attendance_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["attendance"]
        result = collection.delete_one({"_id": ObjectId(attendance_id)})
        if result.deleted_count == 1:
            return {"message": "Attendance deleted successfully"}
        raise HTTPException(status_code=404, detail="Attendance not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)