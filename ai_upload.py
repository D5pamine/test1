from fastapi import FastAPI, File, UploadFile, APIRouter
import shutil
import os

router = APIRouter()

# 저장할 폴더 설정
JSON_DIR = r"C:\project\backend\json"
VIDEO_DIR = r"C:\project\backend\videos"

os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

@router.post("/files/files/upload")
async def upload_files(
    json_file: UploadFile = File(...), 
    video_file: UploadFile = File(...)
):
    # JSON 파일 저장
    json_save_path = os.path.join(JSON_DIR, json_file.filename)
    with open(json_save_path, "wb") as buffer:
        shutil.copyfileobj(json_file.file, buffer)

    # MP4 영상 파일 저장
    video_save_path = os.path.join(VIDEO_DIR, video_file.filename)
    with open(video_save_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    return {
        "message": "파일 저장 완료",
        "json_path": json_save_path,
        "video_path": video_save_path
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(router, host="0.0.0.0", port=8000)
