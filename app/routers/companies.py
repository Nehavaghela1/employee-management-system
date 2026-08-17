from app import routers
from app.models.user import User
from app import routers
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from app.models.department import Department
from app.models.leave_policy import LeavePolicy
from app.utils.auth import get_super_admin,get_current_user
from app.utils.industry_presets import get_preset_departments, INDUSTRY_DEPARTMENT_PRESETS
from app.schemas.company import CompanyRegister
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["Companies"])
def genrate_company_code(db:Session,company_name: str) -> str:
    if not company_name or not company_name.strip():
        company_name= "Company"
    first_word = company_name.split()[0]
    code=re.sub(r'[^A-Z0-9]', '', first_word.upper())
    if not code: 
        code = "COMPANY"
    existing=db.query(Company).filter(Company.code==code).first()
    if not existing:
        return code
    counter=1
    while True:
        candidate= f"{code}{str(counter).zfill(3)}"
        if not db.query(Company).filter(Company.code==candidate).first():
            return candidate
        counter+=1
@router.post("/register")
def register_company(
    company_data: CompanyRegister,
    db: Session = Depends(get_db)
):
    # 1. Check email not already registered
    existing = db.query(Company).filter(
        Company.email == company_data.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="company with this email already registered"
        )

    # 2. Validate industry is in our list
    valid_industries = list(INDUSTRY_DEPARTMENT_PRESETS.keys())
    if company_data.industry not in valid_industries:
        raise HTTPException(
            status_code=400,
            detail=f"industry must be one of: {valid_industries}"
        )

    # 3. Validate phone
    if not company_data.phone.isdigit() or len(company_data.phone) != 10:
        raise HTTPException(
            status_code=400,
            detail="phone must be exactly 10 digits"
        )

    # 4. Generate company code
    code = genrate_company_code(db, company_data.name)

    # 5. Create company
    new_company = Company(
        name=company_data.name,
        code=code,
        email=company_data.email,
        phone=company_data.phone,
        industry=company_data.industry,
        city=company_data.city,
        state=company_data.state,
        address=company_data.address,
        gst_number=company_data.gst_number,
        website=company_data.website,
        employee_count_range=company_data.employee_count_range,
        is_approved=False,
        is_active=False
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    logger.info(f"New company registered: {new_company.name} ({new_company.code})")

    return {
        "message": "company registration submitted successfully",
        "company_code": new_company.code,
        "status": "pending approval from super admin"
    }
@router.post("/pending")
def get_pending_companies(
    admin_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    pending=db.query(Company).filter(Company.is_approved==False).all()
    return pending

@router.post("/{company_id}/approve")
def approve_company(
    company_id: int,
    admin_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    # 1. Find company
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="company not found")

    # 2. Check not already approved
    if company.is_approved:
        raise HTTPException(status_code=400, detail="company already approved")

    # 3. Approve company
    company.is_approved = True
    company.is_active = True
    company.approved_at = datetime.utcnow()
    company.approved_by = admin_user.id

    # 4. Create departments from industry presets
    dept_names = get_preset_departments(company.industry)
    for dept_name in dept_names:
        new_dept = Department(
            name=dept_name,
            company_id=company.id
        )
        db.add(new_dept)

    # 5. Create default leave policy
    leave_policy = LeavePolicy(
        company_id=company.id,
        annual_allowance=20,
        sick_allowance=10,
        casual_allowance=5
    )
    db.add(leave_policy)

    db.commit()
    db.refresh(company)

    logger.info(f"Company approved: {company.name} ({company.code})")

    return {
        "message": f"company {company.name} approved successfully",
        "company_code": company.code,
        "departments_created": len(dept_names)
    }