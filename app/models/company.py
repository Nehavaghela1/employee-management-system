from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    
    # Registration & Tax Details
    gst_number = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)
    registered_address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    website = Column(String, nullable=True)
    employee_count_range = Column(String, nullable=True)  # "1-10", "11-50", "51-200", etc.

    # Branding & Custom Styling
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, nullable=True, default="#1e40af")

    # Industry & Approval Status
    industry = Column(String, nullable=False, default="IT & Software")
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Rejection Audit Trail
    rejection_reason = Column(String, nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
