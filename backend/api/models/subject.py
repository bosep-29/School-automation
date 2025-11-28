from pydantic import BaseModel

class Subject(BaseModel):
    subject_id: str
    subject_name: str
    department: str