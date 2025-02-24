from fastapi import FastAPI
from user_management import router as user_router
from login_auth_api import router as login_router
from signup_api import router as signup_router
from detected_videos import router as detected_videos_router
from routers import detected
from video_routers import router as video_routers
import uvicorn
from fastapi.middleware.cors import CORSMiddleware 
from ai_upload import router as upload_router
from auto_report import router as auto_report


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서 요청 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# user_management의 router를 FastAPI 앱에 등록
app.include_router(user_router, prefix = "/user")
app.include_router(login_router, prefix = "/auth")
app.include_router(signup_router, prefix = "/auth")
app.include_router(detected_videos_router)
app.include_router(video_routers)
app.include_router(upload_router, prefix="/files", tags=["File Upload"])
app.include_router(auto_report, tags = ["Report"])

@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

if __name__ == "__main__": 
    uvicorn.run(app, host="0.0.0.0", port=3000)