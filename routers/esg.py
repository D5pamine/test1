from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database

router = APIRouter()


# ESG 점수 계산 및 저장 API
@router.post("/calculate-esg")
def calculate_esg(esg: schemas.ESGCreate, db: Session = Depends(database.SessionLocal)):
    new_esg = crud.create_esg_entry(db, esg)
    return {"message": "ESG 점수가 저장되었습니다.", "esg_id": new_esg.esg_id}


# ESG 점수 조회 API
@router.get("/esg/{esg_id}")
def get_esg(esg_id: int, db: Session = Depends(database.SessionLocal)):
    esg = crud.get_esg_by_id(db, esg_id)
    if not esg:
        raise HTTPException(status_code=404, detail="ESG 점수를 찾을 수 없습니다.")
    return esg
