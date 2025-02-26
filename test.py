from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time, os, requests
import chromedriver_autoinstaller
import mysql.connector
from database import SessionLocal
from models import User, Detected, Test
from fastapi.security import OAuth2PasswordBearer
from login_auth_api import verify_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")



# Chrome WebDriver 실행
chromedriver_autoinstaller.install()
chrome_options = Options()
chrome_options.add_argument("--load-extension=C:/project/auto_report/fuck")
chrome_options.add_argument("--disable-dev-shm-usage")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_safety_info(user_id: str, db:Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.site_id and user.site_pw:
        return user.site_id, user.site_pw
    return None, None

# 신고 접수 내역을 조회하고 DB에 저장하는 함수
@router.get("/report/results")
def get_safety_report_results(
    token: str = Depends(oauth2_scheme),
    authorization: str = Header(None),
    db:Session = Depends(get_db)
):

    
    driver = None
    user = verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail = "유효하지 않은 사용자입니다.")

    headers = {"Authorization": authorization}
    response = requests.get("http://localhost:8000/auth/token", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="로그인 정보가 유효하지 않음")

    user_data = response.json()
    user_id = user_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="유저 ID 확인 불가")

    site_id, site_pw = get_safety_info(user_id, db)
    if not site_id or not site_pw:
        raise HTTPException(status_code=400, detail="안전신문고 로그인 정보가 없습니다.")

    # Chrome WebDriver 실행
    chromedriver_autoinstaller.install()
    chrome_options = Options()
    chrome_options.add_argument("--load-extension=C:/project/auto_report/fuck")
    chrome_options.add_argument("--disable-dev-shm-usage")

    print("Chrome WebDriver 실행 중...")
    service = Service()
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome WebDriver 실행 완료!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chrome WebDriver 실행 실패: {e}")

    # 로그인
    try:
        url = "https://www.safetyreport.go.kr/#main/login/login"
        print(f"{url} 로 이동 중...")
        driver.get(url)
        time.sleep(2)
        print("로그인 페이지 로드 완료!")

        driver.find_element(By.XPATH, '//*[@id="username"]').send_keys(site_id)
        driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(site_pw)
        driver.find_element(By.XPATH, '//*[@id="contents"]/div/ul/li[1]/article/div[1]/p[3]/button').click()
        time.sleep(2)

    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
        driver.quit()
        raise HTTPException(status_code=500, detail=f"로그인 실패: {e}")

    # 신고 사이트로 이동
    try:
        url = "https://www.safetyreport.go.kr/#/mypage/mysafereport"
        driver.get(url)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        current_url = driver.current_url
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)

        report_table_xpath = '//td[@class="bbs_subject"]/a'
        try:
            report_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, report_table_xpath))
            )
        except Exception as e:
            print("신고 제목 요소를 찾을 수 없음")

        report_elements.click()
        WebDriverWait(driver, 10).until(EC.url_changes(current_url))
        new_url = driver.current_url

        print("신고번호 가져오는 중")

        report_id_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//td[contains(text(), "SPP-")]'))
        )
        report_id = report_id_element.text.strip()
        print("신고번호 가져오기 성공")


        detected_entry = db.query(Test).filter(
            Test.user_id==user_id, Test.report_id == None
            ).order_by(Test.id.desc()).first()

        if detected_entry:
            detected_entry.report_id = report_id
            db.commit()
            print("Detected 테이블에 신고번호 저장 완료")
        else:
            print("저장할 Detected 데이터가 없음")

    except Exception:
        db.rollback()
        raise HTTPException(status_code = 500, detail = "신고 처리 중 오류 발생 ")
    
    


    
    input("디버깅용")
      



        ###메모장 내역 복붙
    #except Exception:
    #    print("오류")
    #    input("디버깅용")