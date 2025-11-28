from pydantic import BaseModel
from typing import List
from fastapi import APIRouter, FastAPI
from pymongo import MongoClient
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId

class Employee(BaseModel):
    user_id: str
    full_name: str
    dob: str
    address: str
    address_proof: bytes
    type_of_employment: str
    designation: str
    subjects: List[str] = []
    qualification_details: List[dict] = []
    date_of_joining_org: str

class UpdateEmployee(BaseModel):
    #user_id: str
    full_name: str
    dob: str
    address: str
    address_proof: bytes
    type_of_employment: str
    designation: str
    subjects: List[str] = []
    qualification_details: List[dict] = []
    date_of_joining_org: str


