from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    user_id: str
    user_pw: str
    username: str
    email: EmailStr
    phone: int
    site_id: str
    site_pw: str


class SafetyAccountUpdate(BaseModel):
    user_id: str  # 사용자 ID
    safety_id: str  # 안전신문고 아이디
    safety_pw: str  # 안전신문고 비밀번호


class Token(BaseModel):
    user_id: str
    user_pw: str
    access_token: str
    refresh_token: str
    token_type: str

class LoginRequest(BaseModel):
    user_id: str
    user_pw: str


# 사용자 정보 불러오기에서 사용
class UserResponse(BaseModel):
    user_id: str
    username: str
    email: Optional[EmailStr]
    phone: str
    site_id: Optional[str]
    #esg_score: Optional[float]
    #report_count: Optional[int]
    #blackbox_videos: Optional[list[str]]=None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
  
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
  


class DetectedCreate(BaseModel):
    car_num: str
    d_video_path: str
    place: str
    violation: str
    time: datetime
    user_id: str

class DetectedResponse(BaseModel):
    detected_id: int
    car_num: str
    d_video_path: str
    place: str
    violation: str
    time: datetime
    user_id: str
    report_id: Optional[int] = None

    class Config:
        from_attributes = True

class ESGCreate(BaseModel):
    user_id: str
    report_id: int
    esg_score: Optional[float] = None
    rate: Optional[float] = None


class ESGResponse(BaseModel):
    esg_id: int
    user_id: str
    report_id: int
    esg_score: Optional[float] = None
    rate: Optional[float] = None

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    detected_id: int
    user_id: str
    title: str
    detail: str
    report_violation: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: int
    detected_id: int
    user_id: str
    title: str
    detail: str
    report_result: Optional[str] = None
    report_violation: Optional[str] = None

    class Config:
        from_attributes = True