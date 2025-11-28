from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from api.database.mongodb import db
from api.utils.user_utils import authorize_user
from api.models.employee import Employee, UpdateEmployee
from fastapi_pagination import Page, paginate, Params

router = APIRouter()

@router.get("/", response_model=Page[Employee])
async def get_employees(params: Params = Depends(), authorized: bool = Depends(authorize_user)):
    collection = db["employees"]
    employees_cursor = collection.find()
    employees = [user for user in employees_cursor]
    return paginate(employees, params)

@router.post("/")
async def create_employee(employee: Employee):
    try:
        user_collection = db["users"]
        existing_user = user_collection.find_one({"_id": ObjectId(employee.user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User does not exists")
        if existing_user["user_type"] is not 2:
            raise HTTPException(status_code=400, detail="User is not an employee")
        collection = db["employees"]
        existing_employee = collection.find_one({"user_id": employee.user_id})
        if existing_employee:
            raise HTTPException(status_code=400, detail="Employee with the same user ID already exists")
        
        result = collection.insert_one(employee.dict())
        return {"message": "Employee created successfully"}
    
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.get("/{employee_id}")
async def read_employee(employee_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["employees"]
        employee = collection.find_one({"_id": ObjectId(employee_id)})
        if employee:
            employee["_id"] = str(employee["_id"])
            return employee
        raise HTTPException(status_code=404, detail="Employee not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.put("/{employee_id}")
async def update_employee(employee_id: str, updated_employee: UpdateEmployee, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["employees"]
        result = collection.update_one({"_id": ObjectId(employee_id)}, {"$set": updated_employee.dict()})
        if result.modified_count == 1:
            return {"message": "Employee updated successfully"}
        raise HTTPException(status_code=404, detail="Employee not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)

@router.delete("/{employee_id}")
async def delete_employee(employee_id: str, authorized: bool = Depends(authorize_user)):
    try:
        collection = db["employees"]
        result = collection.delete_one({"_id": ObjectId(employee_id)})
        if result.deleted_count == 1:
            return {"message": "Employee deleted successfully"}
        raise HTTPException(status_code=404, detail="Employee not found")
    except HTTPException as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={ "message" : str(e)}, status_code=500)