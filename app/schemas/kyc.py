from pydantic import BaseModel
from typing import Optional
from datetime import date

class EmployeeKYCCreate(BaseModel):
    employee_id: int
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

class EmployeeKYCResponse(EmployeeKYCCreate):
    id: int
    company_id: int
    is_aadhaar_verified: bool
    is_pan_verified: bool

    class Config:
        from_attributes = True
