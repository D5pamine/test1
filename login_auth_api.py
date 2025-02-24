
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from database import SessionLocal, engine, Base
from models import User
from schemas import UserResponse, Token, LoginRequest
from crud import get_user_by_user_id
from jose.exceptions import JWTError

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: #에러가 발생해도, 발생하지 않아도 무조건 거치는 구문 / 파일닫기
        db.close()


# 환경변수 로드
# load_dotenv()
SECRET_KEY = "0c1f65cf7317cf95dc42c7b748f17d66dc6ae034d1cf6f50e09a39602f944b66"
ALGORITHM = "HS256"

# 토큰 만료시간 설정
ACCESS_TOKEN_EXPIRE_MINUTES = 60    # 액세스 토큰 만료 (기본 60분)
REFRESH_TOKEN_EXPIRE_MINUTES = 1440  # 리프레시 토큰 만료 (24시간)

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#app = FastAPI()
router = APIRouter(tags = ["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login/user",
    scheme_name = "Bearer"
    )

current_user_tokens = {}


# JWT 토큰 생성 함수
def create_access_token(data:dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)


# 로그인 API (토큰 발급): user_id 기준으로 인증
@router.post("/login/user", response_model=Token, tags=["Authentication"])
def login(request_data: LoginRequest, db: Session = Depends(get_db)):
    user_id = request_data.user_id
    user_pw = request_data.user_pw
    user = get_user_by_user_id(db, request_data.user_id)

    if not user or not user.user_pw:
        raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    
    access_token = create_access_token(
        data={"sub": user.user_id}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_access_token(
        data={"sub": user.user_id}, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    current_user_tokens[user.user_id] = access_token

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    )



# JWT 검증: 유효한 사용자 가져오기
@router.get("/token")
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # 토큰 디코딩해서 사용자 정보(payload) 가져오기
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail = "사용자 정보가 존재하지 않습니다.")
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")




    
# 리프레시 토큰을 사용해 새로운 액세스 토큰 발급
@router.post("/refresh", response_model=Token)
def refresh_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user = get_user_by_user_id(db, user_id)

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        new_access_token = create_access_token(
            data={"sub": user.user_id}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {"access_token": new_access_token}

   

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")



def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # DB에서 사용자 조회
        user = get_user_by_user_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user  # ✅ 인증된 사용자 반환

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

