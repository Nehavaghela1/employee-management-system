from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# What user sends when registering
from pydantic import BaseModel, EmailStr, field_validator

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    department_id: Optional[int] = None

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('password must be at least 8 characters')
        return v

    @field_validator('username')
    @classmethod
    def username_min_length(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v
# What user sends when logging in (email or employee code or username)
class UserLogin(BaseModel):
    email: str
    password: str

# What we send BACK to user (never send password back)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    employee_code: Optional[str] = None  # ← must have this
    employee_id: Optional[int] = None    # ← must have this

    class Config:
        from_attributes = True  # allows SQLAlchemy model → Pydantic schema conversion

# What we send back after successful login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str