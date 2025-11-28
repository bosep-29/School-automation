from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.utils.user_utils import authorize_user
from api.models.client import Client
from api.database.mongodb import db
from bson.objectid import ObjectId
from fastapi_pagination import Page, paginate, Params

router = APIRouter()

@router.get("/", response_model=Page[Client])
async def get_clients(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["clients"]
    clients_cursor = collection.find()
    clients = [user for user in clients_cursor]
    return paginate(clients, params)

@router.post("/")
async def create_client(client: Client, authorized: bool = Depends(authorize_user)):
    try:    
        collection = db["clients"]
        existing_client = collection.find_one({"name": client.name, "address": client.address})
        if existing_client:
            raise HTTPException(status_code=400, detail="Client with same name and address already exists")
        result = collection.insert_one(client.dict())
        return {"message": "Client created successfully", "client_id": str(result.inserted_id)}
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.get("/{client_id}")
async def read_client(client_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["clients"]
        client = collection.find_one({"_id": ObjectId(client_id)})
        if client:
            client["_id"] = str(client["_id"])
            return client
        raise HTTPException(status_code=404, detail="Client not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.put("/{client_id}")
async def update_client(client_id: str, updated_client: Client, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["clients"]
        result = collection.update_one({"_id": ObjectId(client_id)}, {"$set": updated_client.dict()})
        if result.modified_count == 1:
            return {"message": "Client updated successfully"}
        raise HTTPException(status_code=404, detail="Client not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.delete("/{client_id}")
async def delete_client(client_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["clients"]
        result = collection.delete_one({"_id": ObjectId(client_id)})
        if result.deleted_count == 1:
            return {"message": "Client deleted successfully"}
        raise HTTPException(status_code=404, detail="Client not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)