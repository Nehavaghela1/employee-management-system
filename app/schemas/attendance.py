from pydantic import BaseModel
from typing import Optional
from datetime import datetime ,date ,time

class AttendanceCreate(BaseModel):
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    date: date
    check_in: Optional[time] = None 
    check_out: Optional[time] = None
    status: Optional[str] = "present"
class AttendanceUpdate(BaseModel):
    check_in:Optional[time]=None
    check_out:Optional[time]=None
    status:Optional[str]=None
class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    date: date
    day_name: Optional[str] = None
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    hours_worked: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True