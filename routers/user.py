from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
#from database import SessionLocal
from crud import create_user
from schemas import UserCreate
import crud
import schemas
import database
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemas=["bcrypt"], deprecated="auto")
@router.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(database.SessionLocal)):
    """
    회원가입 API
    """
    existing_user = crud.get_user_by_user_id(db, user.user_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    new_user = crud.create_user(db, user)
    return {"message": "회원가입이 완료되었습니다.", "user_id": new_user.user_id}

@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(database.SessionLocal)):
    """
    특정 유저 조회 API
    """
    user = crud.get_user_by_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user