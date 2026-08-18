from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from app.models.department import Department
from app.models.leave_policy import LeavePolicy
from app.utils.auth import get_super_admin, get_current_user, get_hr_admin
from app.utils.industry_presets import get_preset_departments, INDUSTRY_DEPARTMENT_PRESETS
from app.schemas.company import CompanyRegister, CompanyRejectRequest, LeavePolicyUpdate, LeavePolicyResponse
from datetime import datetime
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["Companies"])

def genrate_company_code(db: Session, company_name: str) -> str:
    if not company_name or not company_name.strip():
        company_name = "Company"
    first_word = company_name.split()[0]
    code = re.sub(r'[^A-Z0-9]', '', first_word.upper())
    if not code: 
        code = "COMPANY"
    existing = db.query(Company).filter(Company.code == code).first()
    if not existing:
        return code
    counter = 1
    while True:
        candidate = f"{code}{str(counter).zfill(3)}"
        if not db.query(Company).filter(Company.code == candidate).first():
            return candidate
        counter += 1

@router.post("/register")
def register_company(
    company_data: CompanyRegister,
    db: Session = Depends(get_db)
):
    existing = db.query(Company).filter(
        Company.email == company_data.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="company with this email already registered"
        )

    valid_industries = list(INDUSTRY_DEPARTMENT_PRESETS.keys())
    if company_data.industry not in valid_industries:
        raise HTTPException(
            status_code=400,
            detail=f"industry must be one of: {valid_industries}"
        )

    if company_data.phone and (not company_data.phone.isdigit() or len(company_data.phone) != 10):
        raise HTTPException(
            status_code=400,
            detail="phone must be exactly 10 digits"
        )

    code = genrate_company_code(db, company_data.name)

    new_company = Company(
        name=company_data.name,
        code=code,
        email=company_data.email,
        phone=company_data.phone,
        industry=company_data.industry,
        city=company_data.city,
        state=company_data.state,
        address=company_data.registered_address or company_data.address,
        gst_number=company_data.gst_number,
        pan_number=company_data.pan_number,
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

@router.get("/pending")
def get_pending_companies(
    admin_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    pending = db.query(Company).filter(Company.is_approved == False, Company.rejected_at == None).all()
    return pending

@router.post("/{company_id}/approve")
def approve_company(
    company_id: int,
    admin_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="company not found")

    if company.is_approved:
        raise HTTPException(status_code=400, detail="company already approved")

    company.is_approved = True
    company.is_active = True

    dept_names = get_preset_departments(company.industry)
    for dept_name in dept_names:
        new_dept = Department(
            name=dept_name,
            company_id=company.id
        )
        db.add(new_dept)

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

@router.post("/{company_id}/reject")
def reject_request(
    company_id: int,
    reject_data: Optional[CompanyRejectRequest] = None,
    admin_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="company not found")
    if company.rejected_at:
        raise HTTPException(status_code=400, detail="company already rejected")

    reason = reject_data.reason if reject_data and reject_data.reason else "Application rejected by super admin"
    company.is_approved = False
    company.is_active = False
    company.rejection_reason = reason
    company.rejected_at = datetime.utcnow()
    company.rejected_by = admin_user.id
    db.commit()
    db.refresh(company)
    return {
        "message": f"company {company.name} rejected successfully",
        "company_code": company.code,
        "reason": reason
    }

@router.get("/{company_id}/policy", response_model=LeavePolicyResponse)
def get_company_policy(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_super_admin and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this company policy")

    policy = db.query(LeavePolicy).filter(LeavePolicy.company_id == company_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Leave policy not found for this company")
    return policy

@router.put("/{company_id}/policy", response_model=LeavePolicyResponse)
def update_company_policy(
    company_id: int,
    policy_data: LeavePolicyUpdate,
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    if not current_user.is_super_admin and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this company policy")

    policy = db.query(LeavePolicy).filter(LeavePolicy.company_id == company_id).first()
    if not policy:
        policy = LeavePolicy(company_id=company_id)
        db.add(policy)

    if policy_data.annual_allowance is not None:
        policy.annual_allowance = policy_data.annual_allowance
    if policy_data.sick_allowance is not None:
        policy.sick_allowance = policy_data.sick_allowance
    if policy_data.casual_allowance is not None:
        policy.casual_allowance = policy_data.casual_allowance

    db.commit()
    db.refresh(policy)
    return policy