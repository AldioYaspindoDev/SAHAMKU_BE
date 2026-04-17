from sqlalchemy.orm import Session
import models.user_model as user_model
import schemas.user_schemas as user_schemas
from fastapi import HTTPException
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

pwd_argon2 = CryptContext(schemes=["argon2"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    return db.query(user_model.User).filter(user_model.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(user_model.User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, id:int):
    return db.query(user_model.User).filter(user_model.User.id == id).first()

def create_user(db: Session, user: user_schemas.UserCreate):
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    hash_pwd = pwd_argon2.hash(user.hashed_password)
    db_user = user_model.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def login_user(db: Session, user: user_schemas.UserLogin):
    db_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if not pwd_argon2.verify(user.hashed_password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Password salah")
    access_token = create_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

def update_user(db: Session, user_id: int, user_update: user_schemas.UserUpdate):
    db_user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not db_user:
        return None
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = pwd_argon2.hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return db_user