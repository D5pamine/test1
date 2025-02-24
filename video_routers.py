from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Detected, User
import os
from login_auth_api import get_current_user

router = APIRouter()

# ✅ DB 연결
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# ✅ 1. 특정 사용자(user_id)의 검출 영상 목록 조회
@router.get("/detected-videos/user/{user_id}", response_model=list)
def get_detected_videos_by_user(user: User =Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user.user_id
    print(f"요청된 user_id: {user_id}")
    detected_videos = (
        db.query(Detected)
        .filter(Detected.user_id == user_id)
        .all()
    )
    if not detected_videos:
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




# ✅ 2. 특정 검출 영상(detected_id)의 상세 정보 조회
@router.get("/detected-videos/{detected_id}", response_model=dict)
def get_detected_video(detected_id: int, db: Session = Depends(get_db)):
    detected_video = db.query(Detected).filter(Detected.detected_id == detected_id).first()


    if not detected_video:
        raise HTTPException(status_code=404, detail="해당 detected_id가 존재하지 않습니다.")

    return {
        "detected_id": detected_video.detected_id,
        "user_id": detected_video.user_id,
        "car_num": detected_video.car_num,
        "video_path": detected_video.d_video_path,
        "location": detected_video.place,
        "violation": detected_video.violation,
        "time": detected_video.time
    }


# ✅ 3. 특정 검출 영상(detected_id) 스트리밍 API
@router.get("/video-stream/{detected_id}")
def stream_video(detected_id: int, db: Session = Depends(get_db)):
    detected_video = db.query(Detected).filter(Detected.detected_id == detected_id).first()

    if not detected_video:
        raise HTTPException(status_code=404, detail="해당 detected_id가 존재하지 않습니다.")

    video_path = detected_video.d_video_path

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="비디오 파일을 찾을 수 없습니다.")

    def iterfile():
        with open(video_path, mode="rb") as file:
            yield from file

    return StreamingResponse(iterfile(), media_type="video/mp4")
