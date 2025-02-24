import requests
import json

# 서버 URL
server_url = "http://172.20.10.3:8000/files/files/upload"

# 업로드할 영상 파일 경로
video_filename = "칼치기 판단 1.mp4"

# 전송할 JSON 데이터 (파일 전송에 포함되지 않고 추가 필드로 보낼 경우)
data = json.dumps({
    "detected_id" : 1,
    "violation": "No Helmet",
    "car_num": "92다 3341",
     "gps": {
        "latitude": 37.5665,
        "longitude": 126.9780,
        "timestamp": "2025-02-19T15:30:45.123456"
    },
    "video_path": f"{server_url}/{video_filename}"
          
})


# JSON 파일 저장
json_filename = "hs.json"
with open(json_filename, "w", encoding="utf-8") as f:
    f.write(data)

# 파일 전송 (JSON + MP4)
files = {
    "json_file": open(json_filename, "rb"),  # JSON 파일
    "video_file": open(video_filename, "rb")  # MP4 영상 파일
}

# 서버에 파일 업로드 요청
response = requests.post(server_url, files=files)

# 응답 확인
if response.status_code == 200:
    print("파일 전송 성공:", response.json())
else:
    print("파일 전송 실패:", response.status_code, response.text)

