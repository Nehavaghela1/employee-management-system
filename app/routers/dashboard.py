from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.leave import Leave
from datetime import date
from app.utils.auth import get_current_user
from app.models.user import User

router =APIRouter(prefix="/dashboard",tags=["Dashboard"])

@router.get("/")
def get_dashboar(
    current_user:User=Depends(get_current_user),
    db:Session=Depends(get_db)):
    return {
        "total_employees": db.query(Employee).count(),
        "total_departments": db.query(Department).count(),
        "pending_leaves": db.query(Leave).filter(Leave.status == "pending").count(),
        "approved_leaves": db.query(Leave).filter(Leave.status == "approved").count(),
        "present_today": db.query(Attendance).filter(
            Attendance.date == date.today(),
            Attendance.status == "present"
        ).count(),
        "total_attendance_records": db.query(Attendance).count()
    }

    
