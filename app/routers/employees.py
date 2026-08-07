from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse
from app.utils.auth import get_current_user, get_admin_user
from app.models.user import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.get("/", response_model=List[AttendanceResponse])
def get_attendance(
    employee_id: Optional[int] = None,
    date_filter: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if date_filter:
        query = query.filter(Attendance.date == date_filter)
    return query.all()

@router.post("/", response_model=AttendanceResponse)
def mark_attendance(
    att: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Employee must exist
    emp = db.query(Employee).filter(Employee.id == att.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # 2. Non-admin can only mark own attendance
    if not current_user.is_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp:
            raise HTTPException(status_code=403, detail="No employee record linked to your account. Contact admin.")
        if linked_emp.id != att.employee_id:
            raise HTTPException(status_code=403, detail="You can only mark your own attendance")

    # 3. Status must be valid
    valid_statuses = ["present", "absent", "half_day", "work_from_home", "on_leave"]
    if att.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")

    # 4. Date must be today
    today = date.today()
    if att.date != today:
        raise HTTPException(status_code=400, detail="Can only mark attendance for today")

    # 5. Check-in time validation
    if att.check_in:
        now = datetime.now().time()
        now_dt = datetime.now()
        checkin_dt = datetime.combine(today, att.check_in)
        diff_minutes = (now_dt - checkin_dt).total_seconds() / 60
        if att.check_in > now:
            raise HTTPException(status_code=400, detail="Check-in time cannot be in the future")
        if not current_user.is_admin and diff_minutes > 15:
            raise HTTPException(status_code=400, detail="Check-in cannot be more than 15 minutes in the past")

    # 6. No duplicate for same day
    existing = db.query(Attendance).filter(
        Attendance.employee_id == att.employee_id,
        Attendance.date == today
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for today")

    new_att = Attendance(
        employee_id=att.employee_id,
        date=today,
        check_in=att.check_in,
        check_out=att.check_out,
        status=att.status
    )
    db.add(new_att)
    db.commit()
    db.refresh(new_att)
    return new_att

@router.get("/{att_id}", response_model=AttendanceResponse)
def get_attendance_record(att_id: int, db: Session = Depends(get_db)):
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return att

@router.put("/{att_id}", response_model=AttendanceResponse)
def update_attendance(
    att_id: int,
    att_data: AttendanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    # Owner check
    if not current_user.is_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp or linked_emp.id != att.employee_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this attendance")

    # Check-out time validation
    if att_data.check_out:
        if not current_user.is_admin:
            now = datetime.now().time()
            if att_data.check_out > now:
                raise HTTPException(status_code=400, detail="Check-out time cannot be in the future")
        if att.check_in and att_data.check_out <= att.check_in:
            raise HTTPException(status_code=400, detail="Check-out must be after check-in")

    if att_data.check_in: att.check_in = att_data.check_in
    if att_data.check_out: att.check_out = att_data.check_out
    if att_data.status: att.status = att_data.status
    db.commit()
    db.refresh(att)
    return att

@router.delete("/{att_id}")
def delete_attendance(
    att_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(att)
    db.commit()
    return {"message": "Attendance deleted successfully"}