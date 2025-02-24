import sys
import os

# 현재 프로젝트의 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from models import User, Detected
from schemas import UserCreate, UserUpdate, BlackboxCreate, DetectedCreate
from passlib.context import CryptContext
from datetime import datetime


bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

def create_user(db: Session, user: UserCreate):
    # 이메일 중복 검사
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        return "email_exists"  # 이미 존재하는 이메일

    # 아이디 중복 검사
    db_user_id = db.query(User).filter(User.user_id == user.user_id).first()
    if db_user_id:
        return "user_id_exists"  # 이미 존재하는 아이디
    
    # 비밀번호 해싱 (데이터 무결성을 위해)
    hased_password = bcrypt_context.hash(user.user_pw)


    # 새 사용자 추가
    new_user = User(
        user_id=user.user_id,
        user_pw=user.user_pw,
        username=user.username,
        site_id=user.site_id,
        site_pw=user.site_pw,
        phone=user.phone,
        email=user.email
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 로그인 시 사용자 조회 - user_id를 기준으로 검색
def get_user_by_user_id(db: Session, user_id: str):
    return db.query(User).filter(User.user_id == user_id).first()


# 사용자 정보 업데이트트
def update_user(db: Session, user_id: str, user_update: UserUpdate):
    db_user = db.query(User).filter(User.user_id==user_id).first()

    if not db_user:
        return None  # 사용자가 존재하지 않으면 None 반환

    # 사용자가 입력한 값이 있을 경우에만 업데이트
    if user_update.username is not None:
        db_user.username = user_update.username
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.phone is not None:
        db_user.phone = user_update.phone


    db.commit()
    db.refresh(db_user)
    
    return db_user


def create_detected_entry(
        db: Session, detected_id: int, video_id: int,
        car_num: str, place: str, violation: str,
        time: datetime, user_id: str
        ):
    """
    검출된 차량 정보 생성
    """
    new_detected = Detected(
        detected_id=detected_id,
        video_id=video_id,
        car_num=car_num,
        place=place,
        violation = violation,
        time = time,
        user_id = user_id

    )
    db.add(new_detected)
    db.commit()
    db.refresh(new_detected)

    return new_detected

def get_detected_by_id(db:Session, detected_id: int):
    """
    detected_id를 기반으로 검출된 차량 정보를 조회하는 함수 
    """
    return db.query(Detected).filter(Detected.detected_id==detected_id).first()

