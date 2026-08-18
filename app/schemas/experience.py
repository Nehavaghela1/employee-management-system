from pydantic import BaseModel
from typing import Optional
from datetime import date

class WorkExperienceCreate(BaseModel):
    employee_id: int
    company_name: str
    designation: str
    start_date: date
    end_date: Optional[date] = None
    reason_for_leaving: Optional[str] = None
    certificate_url: Optional[str] = None

class WorkExperienceResponse(WorkExperienceCreate):
    id: int
    company_id: int

    class Config:
        from_attributes = True
