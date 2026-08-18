from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.leave import Leave
from app.models.employee import Employee
from app.models.leave_policy import LeavePolicy
from app.schemas.leave import LeaveCreate, LeaveUpdate, LeaveResponse
from app.utils.auth import get_current_user, get_admin_user, get_hr_admin, get_super_admin
from app.models.user import User
from datetime import date

router = APIRouter(prefix="/leaves", tags=["Leaves"])

@router.get("/", response_model=List[LeaveResponse])
def get_leaves(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Leave)
    if not current_user.is_super_admin:
        query = query.filter(Leave.company_id == current_user.company_id)

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if linked_emp:
            query = query.filter(Leave.employee_id == linked_emp.id)

    if employee_id:
        query = query.filter(Leave.employee_id == employee_id)
    if status:
        query = query.filter(Leave.status == status)

    skip = (page - 1) * limit
    leaves = query.offset(skip).limit(limit).all()

    for l in leaves:
        if l.employee:
            l.employee_code = l.employee.employee_code
            l.employee_name = f"{l.employee.first_name} {l.employee.last_name or ''}".strip()
    return leaves

@router.post("/", response_model=LeaveResponse)
def create_leave(
    leave: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = None
    if leave.employee_code:
        query_emp = db.query(Employee).filter(Employee.employee_code.ilike(leave.employee_code.strip()))
        if not current_user.is_super_admin:
            query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
        emp = query_emp.first()
    elif leave.employee_id:
        query_emp = db.query(Employee).filter(Employee.id == leave.employee_id)
        if not current_user.is_super_admin:
            query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
        emp = query_emp.first()

    if not emp:
        query_emp = db.query(Employee).filter(Employee.user_id == current_user.id)
        if not current_user.is_super_admin:
            query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
        emp = query_emp.first()

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp or linked_emp.id != emp.id:
            raise HTTPException(status_code=403, detail="You can only apply leave for yourself")

    if leave.end_date < leave.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    valid_leave_types = ["sick", "casual", "annual", "maternity", "paternity"]
    if leave.leave_type not in valid_leave_types:
        raise HTTPException(status_code=400, detail=f"leave type must be one of: {valid_leave_types}")

    if leave.start_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot apply for leave in the past")

    overlapping = db.query(Leave).filter(
        Leave.employee_id == emp.id,
        Leave.status != "rejected",
        Leave.start_date <= leave.end_date,
        Leave.end_date >= leave.start_date
    ).first()
    if overlapping:
        raise HTTPException(
            status_code=400,
            detail=f"Employee already has a leave from {overlapping.start_date} to {overlapping.end_date}"
        )

    new_leave = Leave(
        employee_id=emp.id,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status="pending",
        company_id=current_user.company_id
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave

@router.get("/balance/{employee_id}")
def get_leave_balance(
    employee_id: int,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not year:
        year = date.today().year

    query_emp = db.query(Employee).filter(Employee.id == employee_id)
    if not current_user.is_super_admin:
        query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
    emp = query_emp.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp or linked_emp.id != emp.id:
            raise HTTPException(status_code=403, detail="You can only view your own leave balance")

    policy = db.query(LeavePolicy).filter(LeavePolicy.company_id == current_user.company_id).first()
    annual_allowance = policy.annual_allowance if policy else 30

    leaves = db.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.status == "approved"
    ).all()

    used_days = 0
    for l in leaves:
        if l.start_date.year == year:
            days = (l.end_date - l.start_date).days + 1
            used_days += max(1, days)

    remaining_days = max(0, annual_allowance - used_days)
    unpaid_days = max(0, used_days - annual_allowance)

    return {
        "employee_id": employee_id,
        "employee_code": emp.employee_code,
        "year": year,
        "annual_allowance": annual_allowance,
        "used_days": used_days,
        "remaining_days": remaining_days,
        "unpaid_days": unpaid_days
    }

@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Leave).filter(Leave.id == leave_id)
    if not current_user.is_super_admin:
        query = query.filter(Leave.company_id == current_user.company_id)
    leave = query.first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp or linked_emp.id != leave.employee_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this leave request")

    return leave

@router.put("/{leave_id}", response_model=LeaveResponse)
def update_leave(
    leave_id: int,
    leave_data: LeaveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Leave).filter(Leave.id == leave_id)
    if not current_user.is_super_admin:
        query = query.filter(Leave.company_id == current_user.company_id)
    leave = query.first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]

    if leave_data.status and not is_hr_or_admin:
        raise HTTPException(status_code=403, detail="Only HR admin can approve or reject leave")

    if leave_data.status and leave_data.status not in ["pending", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be pending, approved or rejected")

    if leave_data.status: leave.status = leave_data.status
    if leave_data.reason: leave.reason = leave_data.reason

    if leave.status == "approved":
        from app.models.attendance import Attendance
        from datetime import timedelta
        cur_date = leave.start_date
        while cur_date <= leave.end_date:
            att = db.query(Attendance).filter(
                Attendance.employee_id == leave.employee_id,
                Attendance.date == cur_date
            ).first()
            if not att:
                att = Attendance(
                    employee_id=leave.employee_id,
                    date=cur_date,
                    status="on_leave",
                    company_id=current_user.company_id
                )
                db.add(att)
            else:
                att.status = "on_leave"
            cur_date += timedelta(days=1)

    db.commit()
    db.refresh(leave)
    return leave

@router.delete("/{leave_id}")
def delete_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Leave).filter(Leave.id == leave_id)
    if not current_user.is_super_admin:
        query = query.filter(Leave.company_id == current_user.company_id)
    leave = query.first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp or linked_emp.id != leave.employee_id:
            raise HTTPException(status_code=403, detail="you can only cancel your own leave")
        if leave.status != "pending":
            raise HTTPException(status_code=400, detail="you can only cancel pending leaves")
    db.delete(leave)
    db.commit()
    return {"message": "Leave request deleted"}