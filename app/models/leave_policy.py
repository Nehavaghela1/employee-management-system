from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base

class LeavePolicy(Base):
    __tablename__ = "leave_policies"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    annual_allowance = Column(Integer, default=20)
    sick_allowance = Column(Integer, default=10)
    casual_allowance = Column(Integer, default=5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
