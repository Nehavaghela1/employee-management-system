# pyrefly: ignore [missing-import]
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
    level: Optional[str] = "L3"

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
    is_active: Optional[bool] = None
    level: Optional[str] = None

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
    is_active: bool = True
    resignation_status: Optional[str] = "none"
    resignation_reason: Optional[str] = None
    level: Optional[str] = "L3"
    notice_period_days: Optional[int] = 30
    requested_notice_days: Optional[int] = None
    notice_action: Optional[str] = "none"
    created_at: datetime

    class Config:
        from_attributes = True