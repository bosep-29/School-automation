from typing import List
from pydantic import BaseModel

class Student(BaseModel):
    user_id: str
    full_name: str
    dob: str
    address: str
    address_proof: bytes
    current_class_id: str
    groups: List[str] = []
    subjects: List[str] = []
    results: dict = {}