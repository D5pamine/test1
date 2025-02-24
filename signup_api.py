from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User
from schemas import UserCreate
from schemas import SafetyAccountUpdate
from crud import create_user
from passlib.context import CryptContext 

router = APIRouter(prefix = "/auth", tags = ["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ 회원가입 API
@router.post("/signup", tags = ["Authentication"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    
    hashed_password = pwd_context.hash(user.user_pw)
    user.user_pw = hashed_password
    
    result = create_user(db, user)

    # 중복 검사 응답 처리
    if result == "email_exists":
        raise HTTPException(status_code=400, detail = "이미 가입된 이메일입니다.")
    elif result == "user_id_exists":
        raise HTTPException(status_code=400, detail="사용중인 아이디입니다.")
    return {"message" : "회원가입 성공!", "user_id" : result.user_id}


# ✅ 안전신문고 계정 등록 API
@router.patch("/register-safety-account")
def register_safety_account(data: SafetyAccountUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 안전신문고 계정 업데이트
    user.site_id = data.site_id
    user.site_pw = data.site_pw

    db.commit()
    return {"message": "안전신문고 계정 등록 성공!"}
