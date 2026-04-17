from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    hashed_password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    hashed_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type:str = "bearer"

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True