'''
검출된 영상의 조회 및 스트리밍 API
'''

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models import Detected, User
import os
from login_auth_api import get_current_user
import traceback
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter()
VIDEO_DIR = r"C:\project\backend\videos"

# ✅ DB 연결
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# ✅ 1. 특정 사용자(user_id)의 검출 영상 목록 조회
@router.get("/detected-videos/me", response_model=list)
def get_detected_videos_by_user(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)):
    try:
        user_id = user.user_id  # 로그인한 사용자의 user_id 가져오기
        print(f"로그인한 user_id: {user_id}")

        detected_videos = (
            db.query(Detected)
            .filter(Detected.user_id == user_id)  # 로그인한 사용자(user_id)의 검출 영상만 조회
            .all()
        )
        if not detected_videos:
            print("검출 영상 없음")
            raise HTTPException(status_code=404, detail="해당 사용자의 검출 영상이 없습니다.")
        return [
            {
                "detected_id": video.detected_id,
                "user_id": video.user_id,
                "car_num": video.car_num,
                "video_path": video.d_video_path,
                "location": video.place,
                "violation": video.violation,
                "time": video.time
            }
            for video in detected_videos
        ]
    except Exception as e:
        error_trace = traceback.format_exc()  # 🔹 오류 추적 로그
        print(f"사용자의 검출 영상 조회 중 오류 발생: {e}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"사용자의 검출 영상 조회 중 오류 발생: {str(e)}")


# ✅ 로그인한 사용자의 동영상 스트리밍 (detected_id 모를 때)
@router.get("/video-stream/me")
def stream_user_video(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 로그인한 사용자의 가장 최신 영상 가져오기
    latest_video = db.query(Detected).filter(Detected.user_id == user.user_id).order_by(Detected.time.desc()).first()

    if not latest_video:
        raise HTTPException(status_code=404, detail="사용자의 동영상이 없습니다.")

    video_path = os.path.join(VIDEO_DIR, f"{latest_video.detected_id}.mp4")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="비디오 파일을 찾을 수 없습니다.")

    return StreamingResponse(open(video_path, "rb"), media_type="video/mp4")


SECRET_KEY = "0c1f65cf7317cf95dc42c7b748f17d66dc6ae034d1cf6f50e09a39602f944b66"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/user")



@router.get("/video-stream/{detected_id}")
def stream_video_chunk(
    detected_id: int,
    db: Session = Depends(get_db)
):

    # 파일 존재 여부
    video_path = os.path.join(VIDEO_DIR, f"{detected_id}.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="비디오 파일을 찾을 수 없습니다.")

    # chunk generator
    def iterfile(path: str, chunk_size: int = 1024 * 1024):
        with open(path, mode="rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(iterfile(video_path), media_type="video/mp4")



# ✅ 4. 위반 유형 별 동영상 검색
@router.get("/detected-videos/type", response_model=list)
def get_videos_by_violation(
    violation: str = Query(..., description="검색할 위반 유형 (no helmet, overloading, weaving, stealth)"),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = user.user_id  # 로그인한 사용자의 user_id 가져오기
        print(f"로그인한 user_id: {user_id}, 검색 위반 유형: {violation}")

        # 🚨 위반 유형 검증
        valid_violations = ["no helmet", "overloading", "weaving", "stealth"]
        if violation.lower() not in valid_violations:
            raise HTTPException(status_code=400, detail=f"잘못된 위반 유형입니다. 지원하는 값: {valid_violations}")

        detected_videos = (
            db.query(Detected)
            .filter(Detected.user_id == user_id, Detected.violation.ilike(f"%{violation}%"))
            .all()
        )

        if not detected_videos:
            print(f" 위반 영상 없음")
            raise HTTPException(status_code=404, detail=f"{violation} 위반 영상이 없습니다.")

        return [
            {
                "detected_id": video.detected_id,
                "user_id": video.user_id,
                "car_num": video.car_num,
                "video_path": video.d_video_path,
                "location": video.place,
                "violation": video.violation,
                "time": video.time
            }
            for video in detected_videos
        ]
    except Exception as e:
        error_trace = traceback.format_exc()  # 🔹 오류 추적 로그
        print(f"위반 유형별 영상 조회 중 오류 발생: {e}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"위반 유형별 영상 조회 중 오류 발생: {str(e)}")
