from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.utils.auth import get_current_user, get_admin_user
from app.models.user import User
from datetime import date as date_today
from app.models.attendance import Attendance
from app.models.leave import Leave
from datetime import timedelta

router = APIRouter(prefix="/employees", tags=["Employees"])
@router.get("/", response_model=List[EmployeeResponse])
def get_employees(
    department_id: Optional[int] = None,
    name: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    order: Optional[str] = "desc",
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Employee)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if name:
        query = query.filter(
            Employee.first_name.ilike(f"%{name}%") |
            Employee.last_name.ilike(f"%{name}%")
        )
    if sort_by == "salary":
        query = query.order_by(Employee.salary.desc() if order == "desc" else Employee.salary.asc())
    elif sort_by == "first_name":
        query = query.order_by(Employee.first_name.desc() if order == "desc" else Employee.first_name.asc())
    else:
        query = query.order_by(Employee.created_at.desc())
    skip = (page - 1) * limit
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=EmployeeResponse)
def create_employee(
    emp: EmployeeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Employee).filter(Employee.email == emp.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    existing_name = db.query(Employee).filter(
        Employee.first_name == emp.first_name,
        Employee.last_name == emp.last_name
    ).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Employee with same name already exists")
    if emp.salary and emp.salary < 0:
         raise HTTPException(status_code=400, detail="Salary cannot be negative")
    if emp.hire_date:
        if not current_user.is_admin:
            thirty_days_ago = date_today.today() - timedelta(days=30)
            if emp.hire_date < thirty_days_ago:
                raise HTTPException(
                    status_code=400, 
                    detail="Hire date cannot be more than 30 days in the past. Contact admin for older dates."
                )
            if emp.hire_date > date_today.today():
                raise HTTPException(
                    status_code=400,
                    detail="Hire date cannot be in the future. Contact admin for future joining dates."
                )
    if emp.position and len(emp.position.strip()) == 0:
        raise HTTPException(status_code=400, detail="Position cannot be empty")
    if emp.department_id:
        dept = db.query(Department).filter(Department.id == emp.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")

    new_emp = Employee(
        first_name=emp.first_name,
        last_name=emp.last_name,
        email=emp.email,
        phone=emp.phone,
        position=emp.position,
        salary=emp.salary,
        hire_date=emp.hire_date,
        department_id=emp.department_id,
        user_id=emp.user_id  
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp

@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    emp_id: int,
    emp_data: EmployeeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not current_user.is_admin and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own employee record")
    if emp_data.department_id:
        dept = db.query(Department).filter(Department.id == emp_data.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
    if emp_data.hire_date and not current_user.is_admin:
        if emp_data.hire_date > date_today.today():
            raise HTTPException(status_code=400, detail="Hire date cannot be in the future")            
    if emp_data.first_name: emp.first_name = emp_data.first_name
    if emp_data.last_name: emp.last_name = emp_data.last_name
    if emp_data.email: emp.email = emp_data.email
    if emp_data.phone: emp.phone = emp_data.phone
    if emp_data.position: emp.position = emp_data.position
    if emp_data.salary:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Only admin can change salary")
        emp.salary = emp_data.salary
    if emp_data.hire_date: emp.hire_date = emp_data.hire_date
    if emp_data.department_id: emp.department_id = emp_data.department_id
    db.commit()
    db.refresh(emp)
    return emp
@router.delete("/{emp_id}")
def delete_employee(
    emp_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    # Delete related attendance records first
    db.query(Attendance).filter(Attendance.employee_id == emp_id).delete()
    db.query(Leave).filter(Leave.employee_id == emp_id).delete()
    
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted successfully"}