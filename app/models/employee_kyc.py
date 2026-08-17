from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class EmployeeKYC(Base):
    __tablename__ = "employee_kyc"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, unique=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    # Personal KYC Info
    gender = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    # Document Numbers
    aadhaar_number = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)

    # Emergency Contact
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_contact_relation = Column(String, nullable=True)

    # KYC Verification Workflow
    aadhaar_verified = Column(Boolean, default=False)
    pan_verified = Column(Boolean, default=False)
    kyc_submitted_at = Column(DateTime(timezone=True), nullable=True)
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    kyc_verified_by = Column(Integer, nullable=True)  # HR User ID who approved

    created_at = Column(DateTime(timezone=True), server_default=func.now())
