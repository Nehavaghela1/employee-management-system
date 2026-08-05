from fastapi import APIRouter,Depends ,HTTPException
from sqlalchemy.orm import Session
from typing  import List ,Optional
from datetime import date
from app.database import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate,AttendanceUpdate,AttendanceResponse
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
def mark_attendance(att: AttendanceCreate, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == att.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
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
def update_attendance(att_id: int, att_data: AttendanceUpdate, db: Session = Depends(get_db)):
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    if att_data.check_in: att.check_in = att_data.check_in
    if att_data.check_out: att.check_out = att_data.check_out
    if att_data.status: att.status = att_data.status
    db.commit()
    db.refresh(att)
    return att

@router.delete("/{att_id}")
def delete_attendance(att_id: int, db: Session = Depends(get_db)):
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(att)
    db.commit()
    return {"message": "Attendance record deleted"}