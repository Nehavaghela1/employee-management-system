from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.utils.auth import hash_password, verify_password, create_access_token, get_admin_user, get_current_user, get_hr_admin, get_super_admin
from app.utils.audit import log_activity
from datetime import datetime, timedelta, timezone
from typing import Optional
import random
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

def generate_unique_employee_code(db: Session, base_id: int) -> str:
    code = f"EMP{str(base_id).zfill(3)}"
    existing = db.query(Employee).filter(Employee.employee_code == code).first()
    if not existing:
        return code
    idx = base_id + 1
    while True:
        candidate = f"EMP{str(idx).zfill(3)}"
        if not db.query(Employee).filter(Employee.employee_code == candidate).first():
            return candidate
        idx += 1

def find_user_by_identifier(db: Session, identifier: str) -> User:
    if not identifier:
        return None
    identifier = identifier.strip()

    identifiers_to_try = [identifier]
    if identifier.isdigit():
        identifiers_to_try.append(f"EMP{identifier.zfill(3)}")
    elif identifier.upper().startswith("EMP") and identifier[3:].isdigit():
        num_part = identifier[3:]
        identifiers_to_try.append(f"EMP{num_part.zfill(3)}")

    for ident in identifiers_to_try:
        user = db.query(User).filter(
            (User.email.ilike(ident)) | (User.username.ilike(ident))
        ).first()
        if user:
            return user

        emp = db.query(Employee).filter(
            (Employee.email.ilike(ident)) | (Employee.employee_code.ilike(ident))
        ).first()
        if emp:
            if emp.user_id:
                user = db.query(User).filter(User.id == emp.user_id).first()
                if user:
                    return user
            user = db.query(User).filter(User.email.ilike(emp.email)).first()
            if user:
                emp.user_id = user.id
                db.commit()
                return user

    return None

@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        logger.warning(f"Registration failed - username taken: {user_data.username}")
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    employee_code = generate_unique_employee_code(db, new_user.id)

    existing_emp = db.query(Employee).filter(
        Employee.email == user_data.email
    ).first()

    if existing_emp:
        existing_emp.user_id = new_user.id
        if not existing_emp.employee_code:
            existing_emp.employee_code = employee_code
        if user_data.department_id:
            existing_emp.department_id = user_data.department_id
        db.commit()
        db.refresh(existing_emp)
        employee_id = existing_emp.id
        employee_code = existing_emp.employee_code
    else:
        new_emp = Employee(
            first_name=user_data.username,
            last_name="",
            email=user_data.email,
            position="employee",
            employee_code=employee_code,
            user_id=new_user.id,
            department_id=user_data.department_id
        )
        db.add(new_emp)
        db.commit()
        db.refresh(new_emp)
        employee_id = new_emp.id

    logger.info(f"New user registered: {user_data.email} — employee code: {employee_code}")

    new_user.employee_code = employee_code
    new_user.employee_id = employee_id

    return new_user

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = find_user_by_identifier(db, user_data.email)

    if not user or not verify_password(user_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt: {user_data.email}")
        log_activity(db, "LOGIN_FAILED", user_email=user_data.email, details="Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid email, username, employee code or password")

    if user.is_active is False:
        logger.warning(f"Blocked login attempt for deactivated user: {user.email}")
        log_activity(db, "LOGIN_BLOCKED", user_email=user.email, details="Account deactivated by admin")
        raise HTTPException(status_code=403, detail="Your account has been deactivated by admin. Please contact support.")

    emp = db.query(Employee).filter(
        (Employee.user_id == user.id) | (Employee.email == user.email)
    ).first()
    if emp and emp.is_active is False:
        logger.warning(f"Blocked login attempt for deactivated employee: {user.email}")
        log_activity(db, "LOGIN_BLOCKED", user_email=user.email, employee_code=emp.employee_code, details="Employee account deactivated")
        raise HTTPException(status_code=403, detail="Your employee account has been deactivated by admin. Please contact support.")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=30)
    )

    logger.info(f"User logged in successfully: {user.email}")
    log_activity(db, "LOGIN_SUCCESS", user_email=user.email, employee_code=emp.employee_code if emp else None, company_id=user.company_id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/forgot-password")
def forgot_password(
    request: dict,
    db: Session = Depends(get_db)
):
    identifier = request.get("email") or request.get("identifier")

    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="email or employee code is required"
        )

    user = find_user_by_identifier(db, identifier)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="no employee or account found with this details"
        )

    otp = str(random.randint(100000, 999999))

    user.reset_token = otp
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)
    db.commit()

    logger.info(f"Password reset requested for: {user.email}")

    return {
        "message": "reset code generated successfully",
        "reset_code": otp,
        "email": user.email,
        "note": "in production this would be sent via email"
    }

@router.post("/reset-password")
def reset_password(
    request: dict,
    db: Session = Depends(get_db)
):
    identifier = request.get("email") or request.get("identifier")
    reset_code = request.get("reset_code")
    new_password = request.get("new_password")

    if not identifier or not reset_code or not new_password:
        raise HTTPException(
            status_code=400,
            detail="email or employee code, reset code and new password are all required"
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="password must be at least 8 characters"
        )

    user = find_user_by_identifier(db, identifier)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="no employee or account found with this details"
        )

    if not user.reset_token:
        raise HTTPException(
            status_code=400,
            detail="no reset code found. please request a new one"
        )

    if user.reset_token != reset_code:
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="invalid reset code. please request a new one"
        )

    now_utc = datetime.utcnow()
    token_exp = user.reset_token_expires
    if token_exp and getattr(token_exp, 'tzinfo', None) is not None:
        token_exp = token_exp.replace(tzinfo=None)

    if not token_exp or now_utc > token_exp:
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="reset code has expired. please request a new one"
        )

    if verify_password(new_password, user.hashed_password):
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="new password cannot be the same as current password"
        )

    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    logger.info(f"Password reset successful for: {user.email}")

    return {
        "message": "password reset successfully. please login with your new password"
    }

@router.post("/change-password")
def change_password(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_password = request.get("current_password")
    new_password = request.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=400,
            detail="current password and new password are required"
        )

    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="current password is incorrect"
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="new password must be at least 8 characters"
        )

    if verify_password(new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="new password cannot be the same as current password"
        )

    current_user.hashed_password = hash_password(new_password)
    db.commit()

    logger.info(f"Password changed successfully for user: {current_user.email}")
    return {"message": "password updated successfully"}

@router.post("/activate-account")
def activate_account(
    request: dict,
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="You are not authorized to activate users in other companies")

    user.is_active = True
    db.commit()
    return {"message": f"Account for {user.email} activated successfully"}

@router.post("/deactivate-account")
def deactivate_account(
    request: dict,
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="You are not authorized to deactivate users in other companies")

    user.is_active = False
    db.commit()
    return {"message": f"Account for {user.email} deactivated successfully"}

@router.post("/make-admin/{identifier}")
def make_admin(
    identifier: str,
    role: Optional[str] = "hr_admin",
    current_user: User = Depends(get_hr_admin),
    db: Session = Depends(get_db)
):
    user = find_user_by_identifier(db, identifier)
    if not user and identifier.isdigit():
        user = db.query(User).filter(User.id == int(identifier)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to promote users in other companies")

    valid_roles = ["hr_admin", "manager"]
    if current_user.is_super_admin or current_user.role == "super_admin":
        valid_roles.append("super_admin")

    target_role = (role or "hr_admin").lower()
    if target_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    user.role = target_role
    if target_role in ["hr_admin", "super_admin"]:
        user.is_admin = True
    if target_role == "super_admin":
        user.is_super_admin = True

    db.commit()
    db.refresh(user)

    emp_code_str = ""
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if emp and emp.employee_code:
        emp_code_str = f" ({emp.employee_code})"

    logger.info(f"User promoted to {target_role}: {user.email} by {current_user.email}")
    return {"message": f"{user.email}{emp_code_str} is now a {target_role}"}

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query_emp = db.query(Employee).filter(
        (Employee.user_id == current_user.id) | (Employee.email == current_user.email)
    )
    if not current_user.is_super_admin:
        query_emp = query_emp.filter(Employee.company_id == current_user.company_id)
    emp = query_emp.first()

    if not emp:
        employee_code = f"EMP{str(current_user.id).zfill(3)}"
        emp = Employee(
            first_name=current_user.username,
            last_name="",
            email=current_user.email,
            position="employee",
            employee_code=employee_code,
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
    elif not emp.user_id or not emp.employee_code or not emp.company_id:
        if not emp.user_id:
            emp.user_id = current_user.id
        if not emp.employee_code:
            emp.employee_code = f"EMP{str(emp.id).zfill(3)}"
        if not emp.company_id:
            emp.company_id = current_user.company_id
        db.commit()

    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role or ("super_admin" if current_user.is_super_admin else "hr_admin" if current_user.is_admin else "employee"),
        "company_id": current_user.company_id,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "is_super_admin": current_user.is_super_admin,
        "created_at": current_user.created_at,
        "employee_id": emp.id,
        "employee_code": emp.employee_code
    }