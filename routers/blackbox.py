from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import crud
import schemas
import database
import shutil
import os
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploads"

# 블랙박스 영상 업로드 API
@router.post("/upload-video")
def upload_video(user_id: str, file: UploadFile = File(...), db: Session = Depends(database.SessionLocal)):
  
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    file_path = os.path.join(UPLOAD_DIR, f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_video = crud.create_blackbox_video(db, user_id, file_path, datetime.utcnow(), "알 수 없는 장소")
    return {"message": "영상 업로드 완료", "video_id": new_video.video_id}
