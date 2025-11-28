from typing import List
from pydantic import BaseModel

class AttendanceMultipleStudentId(BaseModel):
    student_ids: dict[str, str]
    date: str
    timestamp: str
    hours: List[str]
    group_id: str