from pydantic import BaseModel
from typing import Optional
from datetime import datetime ,date ,time

class AttendanceCreate(BaseModel):
    employee_id:int
    date:date
    check_in :Optional[time]=None 
    check_out:Optional[time]=None
    status:Optional[str]="present"
class AttendanceUpdate(BaseModel):
    check_in:Optional[time]=None
    check_out:Optional[time]=None
    status:Optional[str]=None
class AttendanceResponse(BaseModel):
    id:int
    employee_id:int
    date:date
    check_in:Optional[time]
    check_out:Optional[time]
    status:str
    created_at:datetime

    class Config:
        from_attributes=True