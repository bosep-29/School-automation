from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from api.models.user import User
from api.database.mongodb import db
from bson.objectid import ObjectId
from fastapi import Depends, HTTPException, Header
from api.utils.revoked_tokens import revoked_tokens

SECRET_KEY = "$2b$12$at3fr7r9HQWGQ0pJNoyqvuu7Q5YvuB01QIAsIycQ1wv14mAy1rG1C"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(user: User, user_id: str, org_id: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"user_id": user_id, "role":user.user_type, "org_id": org_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user: User, user_id: str, org_id: str):
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"user_id": user_id, "role":user.user_type, "org_id": org_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

class TokenExpiredError(Exception):
    pass

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get('exp')
        current_time = datetime.utcnow().timestamp()
        if exp and current_time > exp:
            raise TokenExpiredError("Token has expired")
        return payload
    except jwt.JWTError:
        return None

async def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    try:
        if(token in revoked_tokens):
            raise HTTPException(status_code=401, detail="Access token has been revoked")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        collection = db["users"]
        user_data = collection.find_one({"_id": ObjectId(user_id)})
        if user_data is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user_data)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def authorize_user(user: User = Depends(get_current_user), required_user_type: int = 1):
    if user.user_type < required_user_type:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return True