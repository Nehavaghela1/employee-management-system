from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    position = Column(String, nullable=False)
    salary = Column(Integer, nullable=True)
    hire_date = Column(Date, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_code = Column(String, unique=True, nullable=True)   
    is_active = Column(Boolean, default=True)
    resignation_status = Column(String, default="none")
    resignation_reason = Column(String, nullable=True)
    level = Column(String, default="L3")
    notice_period_days = Column(Integer, default=30)
    requested_notice_days = Column(Integer, nullable=True)
    notice_action = Column(String, default="none")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    department = relationship("Department", backref="employees")
    user = relationship("User", backref="employee") 
    