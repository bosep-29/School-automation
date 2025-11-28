from typing import List, Dict
from pydantic import BaseModel

class Marks(BaseModel):
    student_id: str
    subject_id: str
    assessments: List[Dict[str, float]] = []
    total: float = 0.0