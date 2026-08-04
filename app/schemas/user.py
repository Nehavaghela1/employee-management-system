from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# What user sends when registering
class UserRegister(BaseModel):
    email: EmailStr        # validates it's real email format
    username: str
    password: str          

# What user sends when logging in
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# What we send BACK to user (never send password back)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True  # allows SQLAlchemy model → Pydantic schema conversion

# What we send back after successful login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str