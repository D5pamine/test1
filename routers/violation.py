from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, database

router = APIRouter()

@router.post("/violations")
def add_violation(violation: schemas.ViolationCreate, db: Session = Depends(database.SessionLocal)):
    """
    검출된 영상의 위반 사항 저장 API
    """
    new_violation = crud.create_violation(db, violation)
    return {"message": "위반 사항이 저장되었습니다.", "violation_id": new_violation.violation_id}

@router.get("/violations/{detected_id}")
def get_violation_by_detected(detected_id: int, db: Session = Depends(database.SessionLocal)):
    """
    특정 검출된 영상의 위반 사항 조회 API
    """
    violation = crud.get_violation_by_detected_id(db, detected_id)
    if not violation:
        raise HTTPException(status_code=404, detail="해당 검출된 영상의 위반 사항을 찾을 수 없습니다.")
    return violation

@router.get("/violations")
def get_all_violations(db: Session = Depends(database.SessionLocal)):
    """
    전체 위반 사항 조회 API
    """
    violations = crud.get_all_violations(db)
    return violations
