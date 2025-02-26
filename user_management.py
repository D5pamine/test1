from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Detected, Report, ESG
from schemas import UserUpdate
#from login_auth_api import verify_token
from login_auth_api import get_current_user
from schemas import UserResponse, UserUpdate
from login_auth_api import get_current_user
from video_routers import get_detected_videos_by_user
import traceback

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



# 로그인한 사용자의 전체 정보 조회 API
@router.get("/user/info", response_model=UserResponse)
def get_user_info(user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # 🔹 인증된 사용자 확인
        if not user:
            raise HTTPException(status_code=401, detail="인증되지 않은 사용자입니다.")

        # 🔹 블랙박스 영상 목록 조회
        detected_videos = db.query(Detected).filter(Detected.user_id == user.user_id).all()

        if detected_videos is None or len(detected_videos) == 0:
            videos = "저장된 영상이 없습니다."
        else:
            videos = [
                {
                    "detected_id": getattr(video, "detected_id", None),
                    "user_id": getattr(video, "user_id", None),
                    "car_num": getattr(video, "car_num", None),
                    "video_path": getattr(video, "d_video_path", None),
                    "location": getattr(video, "place", None),
                    "violation": getattr(video, "violation", None),
                    "time": getattr(video, "time", None)
                }
                for video in detected_videos if video is not None
            ]
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            site_id=user.site_id,
            videos=videos
        )

    except Exception as e:
        db.rollback()
        error_trace = traceback.format_exc()  # 🔹 오류 추적
        print(f"사용자 정보 조회 중 오류 발생: {e}\n{error_trace}")  # 로그 출력
        raise HTTPException(status_code=500, detail=f"사용자 정보 조회 중 오류 발생: {str(e)}")




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