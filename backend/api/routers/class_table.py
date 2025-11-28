from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from api.database.mongodb import db
from api.utils.user_utils import authorize_user
from api.models.class_table import Class
from fastapi_pagination import Page, paginate, Params

router = APIRouter()

@router.get("/", response_model=Page[Class])
async def get_classes(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["classes"]
    classes_cursor = collection.find()
    classes = [user for user in classes_cursor]
    return paginate(classes, params)

@router.post("/")
async def create_class(class_data: Class, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["classes"]
        existing_class = collection.find_one({"class_tag": class_data.class_tag})
        if existing_class:
            raise HTTPException(status_code=400, detail="Class with the same tag already exists")
        result = collection.insert_one(class_data.dict())
        return {"message": "Class created successfully", "class_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.get("/{class_id}")
async def read_class(class_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["classes"]
        class_data = collection.find_one({"_id": ObjectId(class_id)})
        if class_data:
            class_data["_id"] = str(class_data["_id"])
            return class_data
        raise HTTPException(status_code=404, detail="Class not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.put("/{class_id}")
async def update_class(class_id: str, class_data: Class, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["classes"]
        result = collection.update_one({"_id": ObjectId(class_id)}, {"$set": class_data.dict()})
        if result.modified_count == 1:
            return {"message": "Class updated successfully"}
        raise HTTPException(status_code=404, detail="Class not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.delete("/{class_id}")
async def delete_class(class_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["classes"]
        result = collection.delete_one({"_id": ObjectId(class_id)})
        if result.deleted_count == 1:
            return {"message": "Class deleted successfully"}
        raise HTTPException(status_code=404, detail="Class not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)