from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class AdminBase(BaseModel):
    username: str
    email: EmailStr

class CreateAdmin(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UpdateAdmin(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class AdminLogin(BaseModel):
    email: EmailStr
    password: str