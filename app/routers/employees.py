from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.utils.auth import get_current_user, get_admin_user, get_hr_admin, get_super_admin
from app.models.user import User
from datetime import date as date_today
from app.models.attendance import Attendance
from app.models.leave import Leave
from datetime import timedelta
import calendar
import logging

logger = logging.getLogger(__name__)

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
    offset: Optional[int] = None,
    skip: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Employee)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)

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

    if offset is not None:
        skip_val = offset
    elif skip is not None:
        skip_val = skip
    else:
        skip_val = (page - 1) * limit

    employees = query.offset(skip_val).limit(limit).all()
    for emp in employees:
        if not emp.employee_code:
            emp.employee_code = f"EMP{str(emp.id).zfill(3)}"
    return employees

@router.post("/", response_model=EmployeeResponse)
def create_employee(
    emp: EmployeeCreate,
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    query_existing = db.query(Employee).filter(Employee.email == emp.email)
    if not current_user.is_super_admin:
        query_existing = query_existing.filter(Employee.company_id == current_user.company_id)
    if query_existing.first():
        raise HTTPException(status_code=400, detail="Email already exists in your company")

    if emp.salary and emp.salary < 0:
         raise HTTPException(status_code=400, detail="Salary cannot be negative")
    if emp.hire_date:
        if current_user.role not in ["hr_admin", "super_admin"] and not current_user.is_admin:
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
        dept_query = db.query(Department).filter(Department.id == emp.department_id)
        if not current_user.is_super_admin:
            dept_query = dept_query.filter(Department.company_id == current_user.company_id)
        if not dept_query.first():
            raise HTTPException(status_code=404, detail="Department not found")

    emp_level = (emp.level or "L3").upper()
    notice_days = 90 if emp_level == "L1" else 60 if emp_level == "L2" else 30

    new_emp = Employee(
        first_name=emp.first_name,
        last_name=emp.last_name,
        email=emp.email,
        phone=emp.phone,
        position=emp.position,
        salary=emp.salary,
        hire_date=emp.hire_date,
        department_id=emp.department_id,
        user_id=emp.user_id,
        level=emp_level,
        notice_period_days=notice_days,
        company_id=current_user.company_id
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp

@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(
    emp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
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
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role not in ["hr_admin", "super_admin"] and not current_user.is_admin and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own employee record")

    if emp_data.department_id:
        dept_query = db.query(Department).filter(Department.id == emp_data.department_id)
        if not current_user.is_super_admin:
            dept_query = dept_query.filter(Department.company_id == current_user.company_id)
        if not dept_query.first():
            raise HTTPException(status_code=404, detail="Department not found")

    if emp_data.hire_date and current_user.role not in ["hr_admin", "super_admin"] and not current_user.is_admin:
        if emp_data.hire_date > date_today.today():
            raise HTTPException(status_code=400, detail="Hire date cannot be in the future")

    if emp_data.first_name: emp.first_name = emp_data.first_name
    if emp_data.last_name: emp.last_name = emp_data.last_name
    if emp_data.email: emp.email = emp_data.email
    if emp_data.phone: emp.phone = emp_data.phone
    if emp_data.position: emp.position = emp_data.position
    if emp_data.salary is not None:
        if current_user.role not in ["hr_admin", "super_admin"] and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Only HR admin can change salary")
        emp.salary = emp_data.salary
    if emp_data.hire_date: emp.hire_date = emp_data.hire_date
    if emp_data.department_id: emp.department_id = emp_data.department_id
    db.commit()
    db.refresh(emp)
    return emp

@router.get("/{emp_id}/payslip")
def generate_payslip(
    emp_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role not in ["hr_admin", "super_admin"] and not current_user.is_admin and emp.user_id != current_user.id:
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
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    from app.utils.audit import log_activity
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.is_active = False
    user = None
    if emp.user_id:
        user = db.query(User).filter(User.id == emp.user_id).first()
    elif emp.email:
        user = db.query(User).filter(User.email.ilike(emp.email)).first()

    if user:
        user.is_active = False

    db.commit()
    log_activity(db, "DEACTIVATE_EMPLOYEE", user_email=current_user.email, employee_code=emp.employee_code, details=f"Deactivated employee {emp.first_name}")
    return {"message": f"Employee {emp.employee_code} deactivated successfully. All history preserved."}

@router.post("/{emp_id}/toggle-active")
def toggle_employee_active(
    emp_id: int,
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    from app.utils.audit import log_activity
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    new_status = not emp.is_active
    emp.is_active = new_status

    user = None
    if emp.user_id:
        user = db.query(User).filter(User.id == emp.user_id).first()
    elif emp.email:
        user = db.query(User).filter(User.email.ilike(emp.email)).first()

    if user:
        user.is_active = new_status

    db.commit()
    action_text = "REACTIVATE_EMPLOYEE" if new_status else "DEACTIVATE_EMPLOYEE"
    log_activity(db, action_text, user_email=current_user.email, employee_code=emp.employee_code, details=f"Set active={new_status}")
    return {"message": f"Employee {emp.employee_code} active status updated to {new_status}", "is_active": new_status}

@router.post("/{emp_id}/resign")
def resign_employee(
    emp_id: int,
    payload: Optional[dict] = None,
    reason: Optional[str] = None,
    requested_notice_days: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.utils.audit import log_activity
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role not in ["hr_admin", "super_admin"] and not current_user.is_admin and current_user.email != emp.email and current_user.id != emp.user_id:
        raise HTTPException(status_code=403, detail="You can only submit resignation for your own account")

    res_reason = (payload.get("reason") if payload and isinstance(payload, dict) else None) or reason
    req_notice = (payload.get("requested_notice_days") if payload and isinstance(payload, dict) else None) or requested_notice_days

    emp.resignation_status = "pending"
    if hasattr(emp, "resignation_reason"):
        emp.resignation_reason = res_reason
    if hasattr(emp, "requested_notice_days") and req_notice is not None:
        emp.requested_notice_days = int(req_notice)

    db.commit()

    detail_str = f"Employee {emp.employee_code} ({emp.first_name} {emp.last_name or ''}) submitted resignation request."
    if res_reason:
        detail_str += f" Reason: {res_reason}"
    if req_notice is not None:
        detail_str += f" Requested Notice: {req_notice} days"

    log_activity(
        db,
        "EMPLOYEE_RESIGNED",
        user_email=current_user.email,
        employee_code=emp.employee_code,
        details=detail_str
    )
    return {
        "message": f"Resignation request submitted for {emp.employee_code}. Awaiting admin approval.",
        "employee_code": emp.employee_code,
        "resignation_status": "pending",
        "resignation_reason": res_reason,
        "requested_notice_days": req_notice
    }

@router.post("/{emp_id}/approve-resignation")
def approve_resignation(
    emp_id: int,
    payload: Optional[dict] = None,
    notice_action: Optional[str] = "waived",
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    from app.utils.audit import log_activity
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    n_action = (payload.get("notice_action") if payload and isinstance(payload, dict) else None) or notice_action or "waived"

    emp.resignation_status = "approved"
    if hasattr(emp, "notice_action"):
        emp.notice_action = n_action
    emp.is_active = False

    user = None
    if emp.user_id:
        user = db.query(User).filter(User.id == emp.user_id).first()
    elif emp.email:
        user = db.query(User).filter(User.email.ilike(emp.email)).first()

    if user:
        user.is_active = False

    db.commit()
    log_activity(
        db,
        "RESIGNATION_APPROVED",
        user_email=current_user.email,
        employee_code=emp.employee_code,
        details=f"Admin approved resignation for {emp.employee_code}. Notice Action: {n_action}. Account deactivated."
    )
    return {"message": f"Resignation approved for {emp.employee_code}. Notice Action: {n_action}."}

@router.post("/{emp_id}/reject-resignation")
def reject_resignation(
    emp_id: int,
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    from app.utils.audit import log_activity
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.resignation_status = "rejected"
    db.commit()
    log_activity(
        db,
        "RESIGNATION_REJECTED",
        user_email=current_user.email,
        employee_code=emp.employee_code,
        details=f"Admin rejected resignation for {emp.employee_code}."
    )
    return {"message": f"Resignation rejected for {emp.employee_code}."}

@router.get("/{emp_id}/fnf-settlement")
def get_fnf_settlement(
    emp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.leave import Leave
    query = db.query(Employee).filter(Employee.id == emp_id)
    if not current_user.is_super_admin:
        query = query.filter(Employee.company_id == current_user.company_id)
    emp = query.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role not in ["hr_admin", "super_admin"] and not current_user.is_admin and current_user.email != emp.email and current_user.id != emp.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view FnF settlement statement")

    base_salary = emp.salary or 0
    daily_rate = round(base_salary / 30.0, 2)

    leaves = db.query(Leave).filter(Leave.employee_id == emp.id, Leave.status == "approved").all()
    used_leave_days = 0
    for l in leaves:
        if l.start_date and l.end_date:
            used_leave_days += (l.end_date - l.start_date).days + 1

    annual_allowance = 30
    unused_leaves = max(0, annual_allowance - used_leave_days)
    excess_leaves = max(0, used_leave_days - annual_allowance)

    leave_encashment = round(unused_leaves * daily_rate, 2)
    excess_leave_deduction = round(excess_leaves * daily_rate, 2)

    required_notice = getattr(emp, 'notice_period_days', None) or (90 if (getattr(emp, 'level', 'L3') == 'L1') else 60 if (getattr(emp, 'level', 'L3') == 'L2') else 30)
    served_notice = getattr(emp, 'requested_notice_days', None)
    if served_notice is None:
        served_notice = required_notice
    shortfall_days = max(0, required_notice - served_notice)

    notice_action = getattr(emp, 'notice_action', 'none') or 'none'
    if notice_action == 'charged':
        shortfall_penalty = round(shortfall_days * daily_rate, 2)
    else:
        shortfall_penalty = 0.0

    net_fnf = round(base_salary + leave_encashment - excess_leave_deduction - shortfall_penalty, 2)

    return {
        "employee_id": emp.id,
        "employee_code": emp.employee_code,
        "employee_name": f"{emp.first_name} {emp.last_name or ''}".strip(),
        "level": "Senior / Leadership Role (L1)" if (getattr(emp, 'level', 'L3') == 'L1') else "Executive / Mid-Level Role (L2)" if (getattr(emp, 'level', 'L3') == 'L2') else "Junior Role (L3)",
        "base_salary": base_salary,
        "daily_rate": daily_rate,
        "used_leave_days": used_leave_days,
        "annual_leave_allowance": annual_allowance,
        "unused_leaves": unused_leaves,
        "excess_leaves": excess_leaves,
        "leave_encashment": leave_encashment,
        "excess_leave_deduction": excess_leave_deduction,
        "required_notice_days": required_notice,
        "served_notice_days": served_notice,
        "shortfall_days": shortfall_days,
        "notice_action": notice_action,
        "shortfall_penalty": shortfall_penalty,
        "net_fnf_settlement": net_fnf
    }