from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
import schemas.user_schemas as schemas
import controllers.user_controller as crud

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    if users is None:
        raise HTTPException(status_code=404, detail="user tidak ditemukan atau kosong")
    return users

@router.get("/{id}", response_model=schemas.UserResponse)
def read_user_by_id(id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, id=id)
    if user is None:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user

@router.post("/create", response_model=schemas.UserResponse, status_code=201)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.TokenResponse, status_code=201)
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    return crud.login_user(db=db, user=user)

@router.put("/{id}", response_model=schemas.UserResponse)
def update_user(id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    updated_user = crud.update_user(db, user_id=id, user_update=user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return updated_user

@router.delete("/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    deleted_user = crud.delete_user(db, user_id=id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return {"detail": "User berhasil dihapus"}
