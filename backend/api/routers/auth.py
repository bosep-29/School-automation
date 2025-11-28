from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordRequestForm
from api.utils.user_utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from api.models.user import User
from api.database.mongodb import db
from api.utils.revoked_tokens import revoked_tokens

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user_collection = db["users"]
        user_data = user_collection.find_one({"username": form_data.username})
        if not user_data or not verify_password(form_data.password, user_data["password"]):
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        user_data["_id"] = str(user_data["_id"])
        user = User(**user_data)
        if user.user_type == 2:
            employee_collection = db["employees"]
            org_data = employee_collection.find_one({"user_id": user_data["_id"]})
            if not org_data:
                raise HTTPException(status_code=404, detail="Employee not found")
        elif user.user_type == 1:
            student_collection = db["students"]
            org_data = student_collection.find_one({"user_id": user_data["_id"]})
            if not org_data:
                raise HTTPException(status_code=404, detail="Student not found")
        org_data["_id"] = str(org_data["_id"])
        access_token = create_access_token(user, user_data["_id"], org_data["_id"])
        refresh_token = create_refresh_token(user, user_data["_id"], org_data["_id"])
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.post("/logout")
async def logout(access_token: str = Body(...), refresh_token: str = Body(...)):
    try:
        revoked_tokens.add(access_token)
        revoked_tokens.add(refresh_token)
        return {"message": "Logout successful"}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.post("/register")
async def register(user: User):
    try:
        collection = db["users"]
        existing_user = collection.find_one({"username": user.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with the same username already exists")
        user.password = hash_password(user.password)
        result = collection.insert_one(user.dict())
        return {"message": "User created successfully", "user_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.post("/refresh")
async def refresh(access_token: str = Body(...), refresh_token: str = Body(...)):
    try:
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token not found")
        if refresh_token in revoked_tokens:
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")
        username: str = verify_token(refresh_token)
        access_token = create_access_token(User(username=username))
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)