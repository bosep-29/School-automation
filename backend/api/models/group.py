from pydantic import BaseModel

class Group(BaseModel):
    group_id: str
    group_tag: str
    subject_id: str
    faculty_ids: list
    students: dict[str, str] = {}