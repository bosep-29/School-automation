from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.utils.user_utils import authorize_user
from api.models.group import Group
from api.models.group_update_student_dict import GroupUpdateStudentDict
from api.database.mongodb import db
from bson.objectid import ObjectId
from fastapi_pagination import Page, paginate, Params

router = APIRouter()

@router.get("/", response_model=Page[Group])
async def get_groups(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["groups"]
    groups_cursor = collection.find()
    groups = [group for group in groups_cursor]
    return paginate(groups, params)

@router.post("/")
async def create_group(group: Group, authorized: bool = Depends(authorize_user)):
    try:
        subject_collection = db["groups"]
        existing_subject = subject_collection.find_one({"subject_id": group.subject_id})
        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject with the specified ID does not exist")
        collection = db["groups"]
        student_collection = db["students"]
        existing_group = collection.find_one({"group_id": group.group_id})
        if existing_group:
            raise HTTPException(status_code=400, detail="Group with the same ID already exists")
        if group.students:
            for student_id, student_name in group.students.items():
                existing_student = student_collection.find_one({"_id": ObjectId(student_id)})
                if not existing_student:
                    raise HTTPException(status_code=404, detail="Student with ID not found")
                if not existing_student["full_name"] == student_name:
                    raise HTTPException(status_code=400, detail="Student ID and name does not match")
        result = collection.insert_one(group.dict())
        return {"message": "Group created successfully", "group_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.get("/{group_id}")
async def read_group(group_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["groups"]
        group = collection.find_one({"_id": ObjectId(group_id)})
        if group:
            group["_id"] = str(group["_id"])
            return group
        raise HTTPException(status_code=404, detail="Group not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.put("/{group_id}")
async def update_group(group_id: str, updated_group: Group, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["groups"]
        student_collection = db["students"]
        if updated_group.students:
            for student_id, student_name in updated_group.students.items():
                existing_student = student_collection.find_one({"_id": ObjectId(student_id)})
                if not existing_student:
                    raise HTTPException(status_code=404, detail="Student with ID not found")
                if not existing_student["full_name"] == student_name:
                    raise HTTPException(status_code=400, detail="Student ID and name does not match")
        result = collection.update_one({"_id": ObjectId(group_id)}, {"$set": updated_group.dict()})
        if result.modified_count == 1:
            return {"message": "Group updated successfully"}
        raise HTTPException(status_code=404, detail="Group not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.put("/{group_id}/update-students")
async def update_students_for_group(group_id: str, student_data: GroupUpdateStudentDict, authorized: bool = Depends(authorize_user)):
    try:
        group_collection = db["groups"]
        group = group_collection.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        for student_id, student_name in student_data.students.items():
            if student_id not in group['students']:
                group['students'][student_id] = student_name
        result = group_collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"students": group['students']}}
        )
        if result.modified_count == 1:
            return {"message": f"Students updated successfully for group {group_id}"}
        raise HTTPException(status_code=400, detail="Group not updated")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)

@router.delete("/{group_id}")
async def delete_group(group_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["groups"]
        result = collection.delete_one({"_id": ObjectId(group_id)})
        if result.deleted_count == 1:
            return {"message": "Group deleted successfully"}
        raise HTTPException(status_code=404, detail="Group not found")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)