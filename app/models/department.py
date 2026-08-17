from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Department Manager / Head
    head_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    head_employee = relationship("Employee", foreign_keys=[head_employee_id], backref="managed_departments")

    created_at = Column(DateTime(timezone=True), server_default=func.now())