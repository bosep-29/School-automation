from pydantic import BaseModel, Field
from typing import List

class Class(BaseModel):
    class_tag: str
    class_strength: int
    class_supervisor: str
    year_or_sem: str
    custom_attributes: List[dict] = []