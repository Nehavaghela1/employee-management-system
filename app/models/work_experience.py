from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base

class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    previous_company_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    duration_description = Column(String, nullable=True)  # e.g., "2 Years 4 Months"
    reason_for_leaving = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
