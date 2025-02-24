from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database

router = APIRouter()

# 위반 사항 검출 api
@router.post("/detect-violation")
def detect_violation(detected: schemas.DetectedCreate, db: Session = Depends(database.SessionLocal)):
    new_detected = crud.create_detected_entry(db, detected.video_id, detected.car_num, detected.d_video_path)
    return {"message": "위반 사항이 저장되었습니다.", "detected_id": new_detected.detected_id}

# 검출된 영상 정보 조회 API
@router.get("/detected/{detected_id}")
def get_detected_video(detected_id: int, db: Session = Depends(database.SessionLocal)):
    detected = crud.get_detected_by_id(db, detected_id)
    if not detected:
        raise HTTPException(status_code=404, detail="검출된 위반 사항을 찾을 수 없습니다.")
    return detected

