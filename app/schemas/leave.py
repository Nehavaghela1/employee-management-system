from pydantic import BaseModel
from typing import Optional
from datetime import datetime,date
class LeaveCreate(BaseModel):
    employee_id:int
    leave_type :str
    start_date: date
    end_date:date
    reason:Optional[str]=None
class LeaveUpdate(BaseModel):
    status:Optional[str]=None
    reason:Optional[str]=None
class LeaveResponse(BaseModel):
    id:int
    employee_id:int
    leave_type:str
    start_date:date
    end_date :date 
    reason:Optional[str]
    status:str
    created_at:datetime
    class Config:
        from_attributes=True