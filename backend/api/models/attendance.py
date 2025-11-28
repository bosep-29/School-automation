from pydantic import BaseModel

class Attendance(BaseModel):
    student_id: str
    date: str
    timestamp: str
    marked_by: str
    hours: str
    group_id: str
    type_of_attendance: str