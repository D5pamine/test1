# 받은 JSON 파일에서 GPS 정보를 도로명으로 바꾸고 필요한 정보를 추출해서 DB에 저장


from fastapi import Depends, HTTPException, APIRouter, File, UploadFile
from datetime import datetime
from pydantic import BaseModel
from database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
from models import Detected
import json, requests, os, time
from login_auth_api import get_current_user
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


'''
받은 JSON 파일에서 GPS 정보를 도로명으로 바꾸고 필요한 정보를 추출해서 DB에 저장
'''

router = APIRouter()

naver_clientid = "cuz1ad1kxw"
naver_clientsecret = "B5XICp3ypKpC9Za38N9If0ayCGfY9YtdhRF0gQH9"

SERVER_JSON_DIR = "C:/project/backend/json"
SERVER_VIDEO_DIR = "C:/project/backend/videos"

# DB 연결 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GPS 좌표를 도로명 주소로 변환
def get_address_from_gps(latitude: float, longitude: float) -> str:
    url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
    querystring = {
        "coords" : f"{longitude}, {latitude}",
        "orders" : "roadaddr",
        "output" : "json"
    }

    headers = {
        "X-NCP-APIGW-API-KEY-ID" : naver_clientid,
        "X-NCP-APIGW-API-KEY" : naver_clientsecret,
        "cache-control" : "no-cache"
    }

    response = requests.get(url, headers = headers, params = querystring)
    if response.status_code == 200:
        data = response.json()
        if data["status"]["code"] == 0 and data["results"]:
            road_address = data["results"][0]["region"]
            return f"{road_address['area1']['name']} {road_address['area2']['name']} {road_address['area3']['name']}"

    return "주소 정보 없음"


'''
JSON & VIDEO 파일 읽어와서 DB에 내용 저장 
'''
JSON_FOLDER_PATH = "C:/project/backend/json"
VIDEO_FOLDER_PATH = "C:/project/backend/video"

def store_json_to_db(json_filename):
    json_path = os.path.join(JSON_FOLDER_PATH, json_filename)

    if not os.path.exists(json_path):
        print("파일이 존재하지 않음")
        return
    user_id = os.path.splitext(json_filename)[0]

    try:
        with open(json_path, "r", encoding = "utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        print(f"JSON 파싱 오류: {json_filename}")
        return

        
    detected_id = data.get("detected_id")
    violation = data.get("violation")
    car_num = data.get("car_num")
    d_video_path = data.get("video_path")
    latitude = data.get("gps", {}).get("latitude")
    longitude = data.get("gps", {}).get("longitude")
    time = data.get("gps", {}).get("timestamp")

    if not (detected_id and violation and car_num and d_video_path and latitude and longitude and time):
        raise HTTPException(status_code=400, detail = "필수 데이터가 누락되었습니다.")

        '''
        video_path = None
        for video_file in os.listdir(VIDEO_FOLDER_PATH):
            if str(detected_id) in video_file:  # detected_id가 파일명에 포함된 경우
                video_path = os.path.join(VIDEO_FOLDER_PATH, video_file)
                break  # 첫 번째로 찾은 파일 사용

        if not video_path:
            print(f"⚠ 매칭되는 영상 파일 없음: detected_id={detected_id}")
            continue
        '''
    try:
        timestamp = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        raise HTTPException(status_code = 400, detail = "잘못된 시간 형식입니다.")
    
    # GPS 변환
    address = get_address_from_gps(latitude, longitude)

    db = next(get_db())
    # DB 중복 체크
    existing_video = db.query(Detected).filter(Detected.detected_id == detected_id).first()
    if existing_video:
        return {"message": f"이미 저장된 비디오입니다."}
    
    # DB 저장
    detected_video = Detected(
        user_id = user_id,
        detected_id = detected_id,
        violation = violation,
        car_num = car_num,
        d_video_path = d_video_path,
        place = address,
        time = timestamp
    )

    db.add(detected_video)
    db.commit()
    db.refresh(detected_video)

    print(f"새 파일 감지 -> DB 저장 완료")

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            json_filename = os.path.basename(event.src_path)
            print("새로운 json 파일 감지")
            store_json_to_db(json_filename)

def watch_folder():
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path = JSON_FOLDER_PATH, revursive = False)
    observer.start()

    print("JSON 폴더 감시 시작: {JSON_FOLDER_PATH}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    watch_folder()








'''
    return {
        "message": "파일 업로드 및 DB 저장 성공",
        "user_id": detected_video.user_id,
        "detected_id" : detected_video.detected_id,
        "d_video_path" : detected_video.d_video_path,
        "location" : detected_video.place
    }
# except json.JSONDecodeError:
    # raise HTTPException(status_code=400, detail = "잘못된 json 형식입니다.")
'''

