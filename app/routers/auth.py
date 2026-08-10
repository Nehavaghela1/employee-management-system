from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.utils.auth import hash_password, verify_password, create_access_token, get_admin_user, get_current_user
from datetime import timedelta
import logging
from app.models.employee import Employee
from datetime import datetime, timedelta, timezone
import random

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

def sync_employees_and_users(db: Session):
    try:
        employees = db.query(Employee).all()
        for emp in employees:
            if not emp.employee_code:
                emp.employee_code = generate_unique_employee_code(db, emp.id)
            if not emp.user_id:
                matching_user = db.query(User).filter(User.email == emp.email).first()
                if matching_user:
                    emp.user_id = matching_user.id

        users = db.query(User).all()
        for usr in users:
            matching_emp = db.query(Employee).filter(
                (Employee.user_id == usr.id) | (Employee.email == usr.email)
            ).first()
            if matching_emp:
                if not matching_emp.user_id:
                    matching_emp.user_id = usr.id
                if not matching_emp.employee_code:
                    matching_emp.employee_code = generate_unique_employee_code(db, usr.id)
            else:
                employee_code = generate_unique_employee_code(db, usr.id)
                new_emp = Employee(
                    first_name=usr.username,
                    last_name="",
                    email=usr.email,
                    position="employee",
                    employee_code=employee_code,
                    user_id=usr.id
                )
                db.add(new_emp)
        db.commit()
    except Exception as e:
        logger.error(f"Error syncing employees and users: {e}")
        db.rollback()

def find_user_by_identifier(db: Session, identifier: str) -> User:
    if not identifier:
        return None
    identifier = identifier.strip()

    # 1. Search in User table (email or username)
    user = db.query(User).filter(
        (User.email.ilike(identifier)) | (User.username.ilike(identifier))
    ).first()
    if user:
        return user

    # 2. Search in Employee table (email or employee_code)
    emp = db.query(Employee).filter(
        (Employee.email.ilike(identifier)) | (Employee.employee_code.ilike(identifier))
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

    # 3. Sync and attempt final lookup
    sync_employees_and_users(db)

    user = db.query(User).filter(
        (User.email.ilike(identifier)) | (User.username.ilike(identifier))
    ).first()
    if user:
        return user

    emp = db.query(Employee).filter(
        (Employee.email.ilike(identifier)) | (Employee.employee_code.ilike(identifier))
    ).first()
    if emp and emp.user_id:
        return db.query(User).filter(User.id == emp.user_id).first()

    return None

@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):

    # Check duplicate email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check duplicate username
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        logger.warning(f"Registration failed - username taken: {user_data.username}")
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    hashed = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate employee code
    employee_code = generate_unique_employee_code(db, new_user.id)

    # Check if employee with same email already exists (admin pre-created)
    existing_emp = db.query(Employee).filter(
        Employee.email == user_data.email
    ).first()

    if existing_emp:
        # Link existing employee to new user
        existing_emp.user_id = new_user.id
        if not existing_emp.employee_code:
            existing_emp.employee_code = employee_code
        db.commit()
        db.refresh(existing_emp)
        employee_id = existing_emp.id
        employee_code = existing_emp.employee_code
    else:
        # Auto-create new employee record
        new_emp = Employee(
            first_name=user_data.username,
            last_name="",
            email=user_data.email,
            position="employee",
            employee_code=employee_code,
            user_id=new_user.id
        )
        db.add(new_emp)
        db.commit()
        db.refresh(new_emp)
        employee_id = new_emp.id

    logger.info(f"New user registered: {user_data.email} — employee code: {employee_code}")

    # Add employee info to response
    new_user.employee_code = employee_code
    new_user.employee_id = employee_id

    return new_user

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    
    user = find_user_by_identifier(db, user_data.email)
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt: {user_data.email}")
        raise HTTPException(status_code=401, detail="Invalid email, username, employee code or password")
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=30)
    )
    
    logger.info(f"User logged in successfully: {user.email}")
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

    # Find user by email, username, or employee_code
    user = find_user_by_identifier(db, identifier)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="no employee or account found with this details"
        )

    # Generate 6-digit OTP (overwrites any previous token)
    otp = str(random.randint(100000, 999999))

    # Store OTP with 30 minute expiry (stored as naive UTC)
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

    # Validate all fields present
    if not identifier or not reset_code or not new_password:
        raise HTTPException(
            status_code=400,
            detail="email or employee code, reset code and new password are all required"
        )

    # Validate password length
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="password must be at least 8 characters"
        )

    # Find user by email, username or employee_code
    user = find_user_by_identifier(db, identifier)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="no employee or account found with this details"
        )

    # Check OTP exists
    if not user.reset_token:
        raise HTTPException(
            status_code=400,
            detail="no reset code found. please request a new one"
        )

    # Check OTP matches (single attempt: invalidate token if invalid)
    if user.reset_token != reset_code:
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="invalid reset code. please request a new one"
        )

    # Check OTP not expired (normalize tzinfo to compare naive UTC)
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

    # Check new password is not the same as old password
    if verify_password(new_password, user.hashed_password):
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="new password cannot be the same as current password"
        )

    # Update password and clear OTP
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

@router.post("/make-admin/{identifier}")
def make_admin(
    identifier: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = find_user_by_identifier(db, identifier)
    if not user and identifier.isdigit():
        user = db.query(User).filter(User.id == int(identifier)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="User is already an admin")

    user.is_admin = True
    db.commit()
    db.refresh(user)

    emp_code_str = ""
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if emp and emp.employee_code:
        emp_code_str = f" ({emp.employee_code})"

    logger.info(f"User promoted to admin: {user.email} by {current_user.email}")
    return {"message": f"{user.email}{emp_code_str} is now an admin"}

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find or sync linked employee
    emp = db.query(Employee).filter(
        (Employee.user_id == current_user.id) | (Employee.email == current_user.email)
    ).first()

    if not emp:
        # Auto-create linked employee record if missing
        employee_code = f"EMP{str(current_user.id).zfill(3)}"
        emp = Employee(
            first_name=current_user.username,
            last_name="",
            email=current_user.email,
            position="employee",
            employee_code=employee_code,
            user_id=current_user.id
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
    elif not emp.user_id or not emp.employee_code:
        if not emp.user_id:
            emp.user_id = current_user.id
        if not emp.employee_code:
            emp.employee_code = f"EMP{str(emp.id).zfill(3)}"
        db.commit()

    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at,
        "employee_id": emp.id,
        "employee_code": emp.employee_code
    }