from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Detected, Report, ESG
from schemas import UserUpdate
#from login_auth_api import verify_token
from login_auth_api import get_current_user
from schemas import UserResponse, UserUpdate


router = APIRouter()

# 인증된 사용자 프로필 조회
@router.get("/user/profile")
def get_user_profile(user=Depends(get_current_user)):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "username": user.username,
        "message": "인증된 사용자입니다."
    }

# 사용자 정보 조회 API
@router.get("/user/info", response_model=UserResponse)
def get_user_info(user=Depends(get_current_user), db:Session = Depends(get_db)):

    # 블랙박스 영상 목록 조회
    videos = [video.original_video_oath for video in db.query(Detected).filter(Detected.user_id==user.user_id).all()]

    # 신고 내역 갯수 조회
    report_count = db.query(Report).filter(Report.user_id == user.user_id).count()

    # ESG 점수 조회
    esg_score = db.query(ESG).filter(ESG.user_id == user.user_id).first()
    esg_value = esg_score.esg_score if esg_score else None

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        site_id=user.site_id,
        esg_score=esg_value,
        report_count=report_count,
        videos=videos
    )



# 사용자 정보 수정
@router.put("/user/update")
def update_user(
    user_update: UserUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.user_id == user.user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail = "사용자를 찾을 수 없습니다.")
    
    if user_update.username is not None:
        db_user.username = user_update.username
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.phone is not None:
        db_user.phone = user_update.phone
    
    db.commit()
    db.refresh(db_user)

    return {"message": "회원정보가 성공적으로 수정되었습니다.", "user_id": db_user.user_id}

# 로그인한 사용자의 안전신문고 계정 정보 반환
@router.get("/user/safety-account")
def get_safety_account(user=Depends(get_current_user)):
    if not user.site_id or not user.site_pw:
        raise HTTPException(status_code = 404, detail = "안전신문고 계정 정보가 등록되지 않았습니다.")
    return {"site_id": user.site_id, "site_pw": user.site_pw}