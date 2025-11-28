from pydantic import BaseModel

class MarksUpdateAssessmentDict(BaseModel):
    assessments: dict[str, float] = {}