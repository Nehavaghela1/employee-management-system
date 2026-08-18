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
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp_q = db.query(Employee)
    dept_q = db.query(Department)
    leave_q = db.query(Leave)
    att_q = db.query(Attendance)

    if not current_user.is_super_admin:
        emp_q = emp_q.filter(Employee.company_id == current_user.company_id)
        dept_q = dept_q.filter(Department.company_id == current_user.company_id)
        leave_q = leave_q.filter(Leave.company_id == current_user.company_id)
        att_q = att_q.filter(Attendance.company_id == current_user.company_id)

    return {
        "total_employees": emp_q.count(),
        "total_departments": dept_q.count(),
        "pending_leaves": leave_q.filter(Leave.status == "pending").count(),
        "approved_leaves": leave_q.filter(Leave.status == "approved").count(),
        "present_today": att_q.filter(
            Attendance.date == date.today(),
            Attendance.status == "present"
        ).count(),
        "total_attendance_records": att_q.count()
    }
