from pydantic import BaseModel

class GroupUpdateStudentDict(BaseModel):
    students: dict[str, str] = {}