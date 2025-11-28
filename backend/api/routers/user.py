from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.utils.user_utils import authorize_user
from api.models.user import User
from api.database.mongodb import db
from api.utils.user_utils import hash_password
from bson.objectid import ObjectId
from fastapi_pagination import Page, paginate, Params

router = APIRouter()


@router.get("/", response_model=Page[User])
async def get_users(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["users"]
    users_cursor = collection.find()
    users = [user for user in users_cursor]
    return paginate(users, params)

@router.post("/")
async def create_user(user: User, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["users"]
        existing_user = collection.find_one({"username": user.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with the same username already exists")
        user.password = hash_password(user.password)
        print(user)
        result = collection.insert_one(user.dict())
        return {"message": "User created successfully", "user_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.get("/{user_id}")
async def read_user(user_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["users"]
        print("ID: " + user_id)
        user = collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            return user
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.put("/{user_id}")
async def update_user(user_id: str, updated_user: User, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["users"]
        result = collection.update_one({"_id": ObjectId(user_id)}, {"$set": updated_user.dict()})
        if result.modified_count == 1:
            return {"message": "User updated successfully"}
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.delete("/{user_id}")
async def delete_user(user_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["users"]
        result = collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 1:
            return {"message": "User deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)