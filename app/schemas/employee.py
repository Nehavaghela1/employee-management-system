from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, date

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    position: str
    salary: Optional[int] = None
    hire_date: Optional[date] = None
    department_id: Optional[int] = None
    user_id: Optional[int] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        digits = v.replace('+', '').replace('-', '').replace(' ', '')
        if not digits.isdigit():
            raise ValueError('phone must contain only numbers')
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError('phone must be between 10 and 15 digits')
        return v

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[int] = None
    hire_date: Optional[date] = None
    department_id: Optional[int] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        digits = v.replace('+', '').replace('-', '').replace(' ', '')
        if not digits.isdigit():
            raise ValueError('phone must contain only numbers')
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError('phone must be between 10 and 15 digits')
        return v

class EmployeeResponse(BaseModel):
    id: int
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    position: str
    salary: Optional[int]
    hire_date: Optional[date]
    department_id: Optional[int]
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True