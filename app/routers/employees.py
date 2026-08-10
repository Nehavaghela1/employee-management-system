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

import logging
logger = logging.getLogger(__name__)

def resequence_employee_codes(db: Session):
    try:
        employees = db.query(Employee).order_by(Employee.id.asc()).all()
        if not employees:
            return
        for idx, emp in enumerate(employees, start=1):
            emp.employee_code = f"TMP_RESYNC_{emp.id}_{idx}"
        db.flush()
        for idx, emp in enumerate(employees, start=1):
            emp.employee_code = f"EMP{str(idx).zfill(3)}"
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error resequencing employee codes: {e}")

router = APIRouter(prefix="/employees", tags=["Employees"])
@router.get("/", response_model=List[EmployeeResponse])
def get_employees(
    department_id: Optional[int] = None,
    name: Optional[str] = None,
    employee_code: Optional[str] = None,
    sort_by: Optional[str] = "employee_code",
    order: Optional[str] = "asc",
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
    if employee_code:
        code_str = employee_code.strip()
        if code_str.isdigit():
            padded = f"EMP{code_str.zfill(3)}"
            query = query.filter(
                (Employee.employee_code.ilike(f"%{code_str}%")) |
                (Employee.employee_code.ilike(f"%{padded}%"))
            )
        else:
            query = query.filter(Employee.employee_code.ilike(f"%{code_str}%"))

    if sort_by == "salary":
        if order == "desc":
            query = query.order_by(Employee.salary.desc().nullslast())
        else:
            query = query.order_by(Employee.salary.asc().nullslast())
    elif sort_by == "first_name":
        query = query.order_by(Employee.first_name.desc() if order == "desc" else Employee.first_name.asc())
    elif sort_by == "created_at":
        query = query.order_by(Employee.created_at.desc() if order == "desc" else Employee.created_at.asc())
    else:
        query = query.order_by(Employee.employee_code.asc() if order == "asc" else Employee.employee_code.desc())

    skip = (page - 1) * limit
    employees = query.offset(skip).limit(limit).all()
    for emp in employees:
        if not emp.employee_code:
            emp.employee_code = f"EMP{str(emp.id).zfill(3)}"
    return employees

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

    resequence_employee_codes(db)
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

import calendar

@router.get("/{emp_id}/payslip")
def generate_payslip(
    emp_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not current_user.is_admin and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own payslip")

    today = date_today.today()
    if not month: month = today.month
    if not year: year = today.year

    _, days_in_month = calendar.monthrange(year, month)
    working_days_in_month = 0
    for day_num in range(1, days_in_month + 1):
        if date_today(year, month, day_num).weekday() < 5:
            working_days_in_month += 1

    base_salary = float(emp.salary or 0)
    daily_rate = round(base_salary / max(1, working_days_in_month), 2) if base_salary else 0.0

    att_records = db.query(Attendance).filter(
        Attendance.employee_id == emp_id
    ).all()

    present_days = 0
    half_days = 0
    absent_days = 0

    for a in att_records:
        if a.date.year == year and a.date.month == month:
            st = (a.status or "").lower()
            if "present" in st:
                present_days += 1
            elif "half" in st:
                half_days += 1
            elif "absent" in st:
                absent_days += 1

    leaves = db.query(Leave).filter(
        Leave.employee_id == emp_id,
        Leave.status == "approved"
    ).all()

    approved_leave_days_in_month = 0
    ytd_approved_leave_days = 0

    for l in leaves:
        if l.start_date.year == year:
            duration = (l.end_date - l.start_date).days + 1
            duration = max(1, duration)
            if l.start_date.month == month:
                approved_leave_days_in_month += duration
            if l.start_date.month <= month:
                ytd_approved_leave_days += duration

    annual_allowance = 30
    unpaid_leave_days = max(0, ytd_approved_leave_days - annual_allowance)

    half_day_deduction = round(half_days * (daily_rate / 2.0), 2)
    absent_deduction = round(absent_days * daily_rate, 2)
    unpaid_leave_deduction = round(min(approved_leave_days_in_month, unpaid_leave_days) * daily_rate, 2)

    total_deductions = round(half_day_deduction + absent_deduction + unpaid_leave_deduction, 2)
    net_salary = max(0.0, round(base_salary - total_deductions, 2))

    return {
        "employee_id": emp.id,
        "employee_code": emp.employee_code,
        "employee_name": f"{emp.first_name} {emp.last_name or ''}".strip(),
        "position": emp.position,
        "month": month,
        "year": year,
        "days_in_month": days_in_month,
        "base_salary": base_salary,
        "daily_rate": daily_rate,
        "present_days": present_days,
        "half_days": half_days,
        "absent_days": absent_days,
        "approved_leave_days": approved_leave_days_in_month,
        "unpaid_leave_days": unpaid_leave_days,
        "half_day_deduction": half_day_deduction,
        "absent_deduction": absent_deduction,
        "unpaid_leave_deduction": unpaid_leave_deduction,
        "total_deductions": total_deductions,
        "net_salary": net_salary
    }

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
    resequence_employee_codes(db)
    return {"message": "Employee deleted successfully"}