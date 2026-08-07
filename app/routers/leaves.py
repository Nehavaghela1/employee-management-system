from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.leave import Leave
from app.models.employee import Employee
from app.schemas.leave import LeaveCreate, LeaveUpdate, LeaveResponse
from app.utils.auth import get_current_user, get_admin_user
from app.models.user import User
from datetime import date

router = APIRouter(prefix="/leaves", tags=["Leaves"])

@router.get("/", response_model=List[LeaveResponse])
def get_leaves(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Leave)
    if employee_id:
        query = query.filter(Leave.employee_id == employee_id)
    if status:
        query = query.filter(Leave.status == status)
    skip = (page - 1) * limit
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=LeaveResponse)
def create_leave(
    leave: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Employee must exist
    emp = db.query(Employee).filter(Employee.id == leave.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # 2. Non-admin can only apply for own leave
    if not current_user.is_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp:
            raise HTTPException(status_code=403, detail="No employee record linked to your account")
        if linked_emp.id != leave.employee_id:
            raise HTTPException(status_code=403, detail="You can only apply leave for yourself")

    # 3. End date must be after start date
    if leave.end_date < leave.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    valid_leave_types = ["sick", "casual", "annual", "maternity", "paternity"]
    if leave.leave_type not in valid_leave_types:
        raise HTTPException(status_code=400, detail=f"leave type must be one of: {valid_leave_types}")

    # 4. Cannot apply for past leave
    if leave.start_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot apply for leave in the past")

    # 5. No overlapping leaves
    overlapping = db.query(Leave).filter(
        Leave.employee_id == leave.employee_id,
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
        employee_id=leave.employee_id,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status="pending"
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave

@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave

@router.put("/{leave_id}", response_model=LeaveResponse)
def update_leave(
    leave_id: int,
    leave_data: LeaveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Only admin can change status
    if leave_data.status and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can approve or reject leave")

    # Status must be valid value
    if leave_data.status and leave_data.status not in ["pending", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be pending, approved or rejected")

    if leave_data.status: leave.status = leave_data.status
    if leave_data.reason: leave.reason = leave_data.reason
    db.commit()
    db.refresh(leave)
    return leave

@router.delete("/{leave_id}")
def delete_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),  # ← change from get_admin_user
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if not current_user.is_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp or linked_emp.id != leave.employee_id:
            raise HTTPException(status_code=403, detail="you can only cancel your own leave")
        if leave.status != "pending":
            raise HTTPException(status_code=400, detail="you can only cancel pending leaves")
    db.delete(leave)
    db.commit()
    return {"message": "Leave request deleted"}