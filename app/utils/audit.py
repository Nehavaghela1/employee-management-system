from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from typing import Optional

def log_activity(
    db: Session,
    action: str,
    user_email: Optional[str] = None,
    employee_code: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    company_id: Optional[int] = None
):
    try:
        log_entry = AuditLog(
            user_email=user_email,
            employee_code=employee_code,
            action=action,
            details=details,
            ip_address=ip_address,
            company_id=company_id
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
