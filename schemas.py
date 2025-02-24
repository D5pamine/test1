from pydantic import BaseModel, EmailStr
from typing import Optional

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
    esg_score: Optional[float]
    report_count: Optional[int]
    blackbox_videos: Optional[list[str]]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
  
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
  
class BlackboxCreate(BaseModel):
    video_name: str
    description: Optional[str] = None
    confidence: float


class DetectedCreate(BaseModel):
    blackbox_id: int
    car_num: str
