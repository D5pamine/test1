from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database

router = APIRouter()

# 신고 제출 API
@router.post("/submit-report")
def submit_report(report: schemas.ReportCreate, db: Session = Depends(database.SessionLocal)):
    new_report = crud.create_report(db, report)
    return {"message": "신고가 정상적으로 접수되었습니다.", "report_id": new_report.report_id}

# 특정 신고 조회 API
@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(database.SessionLocal)):
    report = crud.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="신고 내역을 찾을 수 없습니다.")
    return report
