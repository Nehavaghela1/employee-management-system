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

from fastapi.responses import Response

@router.get("/export")
def export_attendance_csv(
    employee_id: Optional[int] = None,
    employee_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    records = query.all()

    filtered = []
    for att in records:
        if month and att.date.month != month:
            continue
        if year and att.date.year != year:
            continue
        if employee_code:
            emp_code = att.employee.employee_code if att.employee else ""
            if employee_code.lower() not in emp_code.lower():
                continue
        filtered.append(att)

    csv_lines = ["ID,Date,Day of Week,Employee Code,Employee Name,Check In,Check Out,Hours Worked,Status"]
    for r in filtered:
        emp_code = r.employee.employee_code if r.employee else f"EMP{str(r.employee_id).zfill(3)}"
        emp_name = f"{r.employee.first_name} {r.employee.last_name or ''}".strip() if r.employee else f"Employee #{r.employee_id}"
        cin = r.check_in.strftime("%H:%M:%S") if r.check_in else "-"
        cout = r.check_out.strftime("%H:%M:%S") if r.check_out else "-"
        day_name = r.date.strftime("%A")
        hrs = 0.0
        if r.check_in and r.check_out:
            cin_dt = datetime.combine(r.date, r.check_in)
            cout_dt = datetime.combine(r.date, r.check_out)
            hrs = round((cout_dt - cin_dt).total_seconds() / 3600.0, 2)
        line = f'"{r.id}","{r.date}","{day_name}","{emp_code}","{emp_name}","{cin}","{cout}","{hrs}","{r.status}"'
        csv_lines.append(line)

    csv_content = "\n".join(csv_lines)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_export.csv"}
    )

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
    records = query.all()
    for att in records:
        if att.employee:
            att.employee_code = att.employee.employee_code
            att.employee_name = f"{att.employee.first_name} {att.employee.last_name or ''}".strip()
        att.day_name = att.date.strftime("%A")
        if att.check_in and att.check_out:
            cin_dt = datetime.combine(att.date, att.check_in)
            cout_dt = datetime.combine(att.date, att.check_out)
            hrs = round((cout_dt - cin_dt).total_seconds() / 3600.0, 2)
            att.hours_worked = hrs
            if hrs < 8.0 and hrs > 0 and att.status == "present":
                att.status = "half_day"
        else:
            att.hours_worked = 0.0
    return records

@router.post("/", response_model=AttendanceResponse)
def mark_attendance(
    att: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.id == att.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="employee not found")

    if not current_user.is_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp:
            raise HTTPException(status_code=403, detail="no employee record linked to your account. contact admin.")
        if linked_emp.id != att.employee_id:
            raise HTTPException(status_code=403, detail="you can only mark your own attendance")

    valid_statuses = ["present", "absent", "half_day", "work_from_home", "on_leave"]
    if att.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of: {valid_statuses}")

    today = date.today()
    if att.date != today:
        raise HTTPException(status_code=400, detail="attendance can only be marked for today")

    if att.check_in:
        now = datetime.now().time()
        now_dt = datetime.now()
        checkin_dt = datetime.combine(today, att.check_in)
        diff_minutes = (now_dt - checkin_dt).total_seconds() / 60
        if att.check_in > now:
            raise HTTPException(status_code=400, detail="check-in time cannot be in the future")
        if not current_user.is_admin and diff_minutes > 15:
            raise HTTPException(status_code=400, detail="check-in cannot be more than 15 minutes in the past")

    existing = db.query(Attendance).filter(
        Attendance.employee_id == att.employee_id,
        Attendance.date == today
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="attendance already marked for today")

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
        raise HTTPException(status_code=404, detail="attendance record not found")
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
        raise HTTPException(status_code=404, detail="attendance record not found")

    if not current_user.is_admin:
        linked_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not linked_emp or linked_emp.id != att.employee_id:
            raise HTTPException(status_code=403, detail="not authorized to update this attendance")

    if att_data.check_out:
        if not current_user.is_admin:
            now = datetime.now().time()
            if att_data.check_out > now:
                raise HTTPException(status_code=400, detail="check-out time cannot be in the future")
        if att.check_in and att_data.check_out <= att.check_in:
            raise HTTPException(status_code=400, detail="check-out must be after check-in")
    if att_data.check_out and att.check_in:
        checkin_dt = datetime.combine(date.today(), att.check_in)
        checkout_dt = datetime.combine(date.today(), att_data.check_out)
        diff_hours = (checkout_dt - checkin_dt).total_seconds() / 3600
        if diff_hours < 1 and not current_user.is_admin:
            raise HTTPException(status_code=400, detail="minimum 1 hour required before checkout")

    if att_data.check_in: att.check_in = att_data.check_in
    if att_data.check_out: att.check_out = att_data.check_out
    if att_data.status:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="only admin can change attendance status")
        att.status = att_data.status
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
        raise HTTPException(status_code=404, detail="attendance record not found")
    db.delete(att)
    db.commit()
    return {"message": "attendance deleted successfully"}