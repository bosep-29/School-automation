from pydantic import BaseModel

class Assessment(BaseModel):
    assessment_type: str
    assessment_id: str
    assessment_date: str
    assessment_tag: str
    assessment_max_marks: int
    assessment_mandatory_pass: bool
    subject_id: str
    contribution_percentage: str