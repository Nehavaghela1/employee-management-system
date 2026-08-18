from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CompanyRegister(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    industry: str = "IT & Software"
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    registered_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    website: Optional[str] = None
    employee_count_range: Optional[str] = None

class CompanyRejectRequest(BaseModel):
    reason: Optional[str] = "Application does not meet platform requirements"

class LeavePolicyUpdate(BaseModel):
    annual_allowance: Optional[int] = None
    sick_allowance: Optional[int] = None
    casual_allowance: Optional[int] = None

class LeavePolicyResponse(BaseModel):
    id: int
    company_id: int
    annual_allowance: int
    sick_allowance: int
    casual_allowance: int

    class Config:
        from_attributes = True
