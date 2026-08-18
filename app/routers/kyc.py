from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.employee_kyc import EmployeeKYC
from app.models.employee import Employee
from app.schemas.kyc import EmployeeKYCCreate, EmployeeKYCResponse
from app.utils.auth import get_current_user, get_hr_admin
from app.models.user import User

router = APIRouter(prefix="/kyc", tags=["Employee KYC"])

@router.post("/", response_model=EmployeeKYCResponse)
def create_or_update_kyc(
    kyc_data: EmployeeKYCCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query_emp = db.query(Employee).filter(Employee.id == kyc_data.employee_id)
    if not current_user.is_super_admin:
        query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
    emp = query_emp.first()

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    is_hr_or_admin = current_user.is_admin or current_user.role in ["hr_admin", "super_admin"]
    if not is_hr_or_admin and emp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only submit your own KYC")

    kyc = db.query(EmployeeKYC).filter(EmployeeKYC.employee_id == kyc_data.employee_id).first()
    if not kyc:
        kyc = EmployeeKYC(
            employee_id=kyc_data.employee_id,
            company_id=current_user.company_id
        )
        db.add(kyc)

    if kyc_data.aadhaar_number: kyc.aadhaar_number = kyc_data.aadhaar_number
    if kyc_data.pan_number: kyc.pan_number = kyc_data.pan_number
    if kyc_data.dob: kyc.dob = kyc_data.dob
    if kyc_data.gender: kyc.gender = kyc_data.gender
    if kyc_data.address: kyc.address = kyc_data.address
    if kyc_data.emergency_contact_name: kyc.emergency_contact_name = kyc_data.emergency_contact_name
    if kyc_data.emergency_contact_phone: kyc.emergency_contact_phone = kyc_data.emergency_contact_phone
    if kyc_data.emergency_contact_relation: kyc.emergency_contact_relation = kyc_data.emergency_contact_relation

    db.commit()
    db.refresh(kyc)
    return kyc

@router.get("/{employee_id}", response_model=EmployeeKYCResponse)
def get_employee_kyc(
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
        raise HTTPException(status_code=403, detail="Not authorized to view this KYC record")

    kyc = db.query(EmployeeKYC).filter(EmployeeKYC.employee_id == employee_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC record not found for this employee")
    return kyc

@router.post("/{employee_id}/verify")
def verify_employee_kyc(
    employee_id: int,
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    kyc = db.query(EmployeeKYC).filter(EmployeeKYC.employee_id == employee_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC record not found")

    if not current_user.is_super_admin and kyc.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to verify KYC in other companies")

    kyc.is_aadhaar_verified = True
    kyc.is_pan_verified = True
    db.commit()
    db.refresh(kyc)
    return {"message": "Employee KYC verified successfully", "is_aadhaar_verified": True, "is_pan_verified": True}
