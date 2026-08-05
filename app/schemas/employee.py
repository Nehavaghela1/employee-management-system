from pydantic import BaseModel,EmailStr
from typing import Optional 
from datetime import datetime ,date
 
class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    position: str
    salary: Optional[int] = None
    hire_date: Optional[date] = None
    department_id: Optional[int] = None
class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[int] = None
    hire_date: Optional[date] = None
    department_id: Optional[int] = None
class EmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    position: str
    salary: Optional[int]
    hire_date: Optional[date]
    department_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True