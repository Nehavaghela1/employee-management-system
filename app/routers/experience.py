from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.work_experience import WorkExperience
from app.models.employee import Employee
from app.schemas.experience import WorkExperienceCreate, WorkExperienceResponse
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/experience", tags=["Work Experience"])

@router.post("/", response_model=WorkExperienceResponse)
def add_work_experience(
    exp_data: WorkExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query_emp = db.query(Employee).filter(Employee.id == exp_data.employee_id)
    if not current_user.is_super_admin:
        query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
    emp = query_emp.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add work experience to your own record")

    new_exp = WorkExperience(
        employee_id=exp_data.employee_id,
        company_name=exp_data.company_name,
        designation=exp_data.designation,
        start_date=exp_data.start_date,
        end_date=exp_data.end_date,
        reason_for_leaving=exp_data.reason_for_leaving,
        certificate_url=exp_data.certificate_url,
        company_id=current_user.company_id
    )
    db.add(new_exp)
    db.commit()
    db.refresh(new_exp)
    return new_exp

@router.get("/{employee_id}", response_model=List[WorkExperienceResponse])
def get_work_experiences(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query_emp = db.query(Employee).filter(Employee.id == employee_id)
    if not current_user.is_super_admin:
        query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
    emp = query_emp.first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view work experience")

    experiences = db.query(WorkExperience).filter(WorkExperience.employee_id == employee_id).all()
    return experiences
