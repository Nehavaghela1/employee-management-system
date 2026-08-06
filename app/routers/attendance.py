from fastapi import APIRouter,Depends ,HTTPException
from sqlalchemy.orm import Session
from typing  import List ,Optional
from datetime import datetime,date
from app.database import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate,AttendanceUpdate,AttendanceResponse
from datetime import date as date_today,timedelta
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
    emp = db.query(Employee).filter(Employee.id == att.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if att.date != date.today():
        raise HTTPException(status_code=400, detail="Can only mark attendance for today")
    if att.date > date_today.today():
        raise HTTPException(status_code=400, detail="Cannot mark attendance for future date")
    if att.date == date.today():
        current_time = datetime.now().time()
        if att.check_in and att.check_in > current_time:
            raise HTTPException(400, "Cannot mark future check-in time")
    existing = db.query(Attendance).filter(
        Attendance.employee_id == att.employee_id,
        Attendance.date == att.date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this date")
    new_att = Attendance(
        employee_id=att.employee_id,
        date=att.date,
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
    
    # owner check — only admin or the employee themselves
    if not current_user.is_admin and att.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this attendance")
    
    if att_data.check_out and att.check_in:
        if att_data.check_out <= att.check_in:
            raise HTTPException(status_code=400, detail="Check out time must be after check in time")
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