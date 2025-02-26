# 받은 JSON 파일에서 GPS 정보를 도로명으로 바꾸고 필요한 정보를 추출해서 DB에 저장
'''
JSON에서 데이터 추출해서 DB에 저장
'''

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
        print(f"파일 없음: {json_filename}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as file:
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

    if None in [detected_id, violation, car_num, d_video_path, latitude, longitude, time]:
        print(f"🚨 필수 데이터 누락됨: {json_filename}")
        return

    try:
        timestamp = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        print(f"🚨 잘못된 시간 형식: {json_filename}")
        return

    address = get_address_from_gps(latitude, longitude)

    db = SessionLocal()
    try:
        if db.query(Detected).filter(Detected.detected_id == detected_id).first():
            print(f"✅ 이미 저장된 데이터: {json_filename}")
            return

        detected_video = Detected(
            detected_id=detected_id,
            violation=violation,
            car_num=car_num,
            d_video_path=d_video_path,
            place=address,
            time=timestamp
        )

        db.add(detected_video)
        db.commit()
        print(f"✅ DB 저장 완료: {json_filename}")

    except Exception as e:
        print(f"🚨 DB 오류: {str(e)}")
        db.rollback()
    finally:
        db.close()

    os.makedirs(JSON_FOLDER_PATH, exist_ok=True)
    os.rename(json_path, os.path.join(JSON_FOLDER_PATH, json_filename))

class JSONFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            time.sleep(1)  # 파일 저장 완료 대기
            filename = os.path.basename(event.src_path)
            print(f"📂 새 JSON 파일 감지: {filename}")
            store_json_to_db(filename)


def process_all_json_files():
    json_files = [f for f in os.listdir(JSON_FOLDER_PATH) if f.endswith(".json")]

    if not json_files:
        print("📂 처리할 JSON 파일이 없습니다.")
        return

    print(f"📂 총 {len(json_files)}개의 JSON 파일을 확인합니다.")
    
    for json_filename in json_files:
        store_json_to_db(json_filename)
    
    print("✅ 모든 JSON 파일 처리가 완료되었습니다.")


@router.on_event("startup")
def startup_event():
    print("🚀 서버 시작 -> JSON 데이터 처리 시작")
    process_all_json_files()
    
    observer = Observer()
    observer.schedule(JSONFileHandler(), JSON_FOLDER_PATH, recursive=False)
    observer.start()
    print("👀 JSON 폴더 감시 시작")





