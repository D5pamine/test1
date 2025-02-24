import time, os, requests, pytz
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from models import User, Detected
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from database import SessionLocal, engine
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 안전신문고 계정 가져오기
def get_safety_credentials(user_id: int, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.site_id and user.site_pw:
        return user.site_id, user.site_pw
    return None, None


# 사용자의 최근 신고할 위반 사항 가져오기
def get_user_violation(user_id: int, db: Session):
    violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
    if violation_record:
        return violation_record.violation
    return None


# FastAPI 엔드포인트 추가 : 신고 자동 실행
@router.post("/report")
def report_violation(
    token: str = Depends(oauth2_scheme),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
    ):
    if not authorization:
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다.")

    headers = {"Authorization": authorization}
    response = requests.get("http://localhost:8000/auth/token", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="로그인 정보가 유효하지 않음")

    user_data = response.json()
    user_id = user_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="유저 ID 확인 불가")

    site_id, site_pw = get_safety_credentials(user_id, db)
    if not site_id or not site_pw:
        raise HTTPException(status_code=400, detail="안전신문고 로그인 정보가 없습니다.")

    violation = get_user_violation(user_id, db)
    if not violation:
        raise HTTPException(status_code=400, detail="신고할 위반 사항이 없습니다.")

    violation_mapping = {
        "Weaving": 2,
        "No Helmet": 2,
        "Stealth": 5,
        "Overloading": 7,
    }

    selected_index = violation_mapping.get(violation, 1)

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
        exit()

    '''
    신고 사이트로 이동
    '''
    try:
        url = "https://www.safetyreport.go.kr/#safereport/safereport3"
        driver.get(url)
        time.sleep(2)
        print("신고 페이지 로드 완료")

        iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
    except Exception as e:
        print(f"신고 페이지 로드 중 오류 발생")


    '''
    1. 신고 유형 선택 
    '''
    try:
        select_element = driver.find_element(By.ID, "ReportTypeSelect")
        select = Select(select_element)
        select.select_by_index(selected_index)
        print(f"신고 유형 선택 완료: {selected_index}번째 옵션")
    except Exception as e:
        print(f"신고 유형 선택 중 오류 발생: {e}")


##################################################################
    '''
    2. 사진/동영상 파일 업로드 
    '''
    try:
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[starts-with(@id, 'file_o_')]"))
        )
        file_path = os.path.abspath("C:/project/test_video.mp4")
        file_input.send_keys(file_path)
        print(f" 파일 업로드 완료: {file_path}")
        driver.switch_to.default_content()
    
    except Exception as e:
        print(f" 파일 업로드 실패: {e}")
##################################################################


###################################################################
    '''
    이건 무슨 코드인지 모르겠음
    '''
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        print("발견된 iframe 개수:", len(iframes))
        for idx, iframe in enumerate(iframes):
            print(
                f"iframe[{idx}] - id = {iframe.get_attribute('id')}, "
                f"title = {iframe.get_attribute('title')}, "
                f"src = {iframe.get_attribute('src')}"
            )
    else:
        print("iframe이 없습니다. 모달 idv만 사용되었을 가능성 있음")
####################################################################
    
    
####################################################################
    '''
    3. 신고 발생 지역
    '''
    try:
        violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
        if violation_record:
            place_address = violation_record.place
        else:
            raise HTTPException(status_code=400, detail = "등록된 장소 정보가 없습니다,")
        iframe_element = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "iframe[title = '우편번호 검색 프레임']")
            )
        )
        driver.switch_to.frame(iframe_element)
        print("iframe 전환 완료")
        wait = WebDriverWait(driver, 10)
        modal = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "popup_body"))
        )
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "region_name"))
        )
        # detected 테이블에서 가져온 주소 입력
        search_input.send_keys(place_address)
        search_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn_search"))
        )
        search_button.click()
        wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li"))
        )
        first_item = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul/li[1]/dl/dd[1]/span/button"))
        )
        first_item.click()
        print(f"주소 입력 완료")
    except Exception as e:
        print("iframe 접근 혹은 내부 요소 처리 중 예외 발생: ", e)
####################################################################


####################################################################
    '''
    4. 제목
    '''
    try:
        violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
        if violation_record and violation_record.violation:
            violation_type = violation_record.violation
        else:
            raise HTTPException(status_code = 400, detail = "등록된 위반 사항이 없습니다.")

        violation_translate = {
            "No Helmet": "헬멧 미착용",
            "Stealth" : "스텔스",
            "Overloading": "과적차량",
            "Weaving": "급차선 변경(칼치기)"
        }

        violation_translate = violation_translate.get(violation_type, violation_type)
        report_title = f"{violation_translate}"
        
        제목 = driver.find_element(By.XPATH, '//*[@id="C_A_TITLE]')
        제목.send_keys(report_title)
        print("제목 입력 완료 ")
    except Exception as e:
        print("제목 입력 중 오류 발생")
####################################################################


####################################################################
    '''
    5. 신고내용
    '''
    try:
        if violation_record:
            detected_date = violation_record.time.strftime("%Y.%m.%d")
            detected_time = violation_record.time.strftime("%H:%M")
            timestamp = f"{detected_date} {detected_time}"
            place = violation_record.place
        
        report_content = f"{timestamp}에 {place}에서 차량번호 {car_num}인 차량이 {violation_translate}을(를) 위반하는 모습을 목격했습니다. 첨부된 영상확인 바랍니다."
        content = driver.find_element(By.XPATH, '//*[@id="C_A_CONTENTS"]')
        content.send_keys(report_content)
        print("신고 내용 입력 완료")
    
    except Exception:
        print("신고 내용 입력 중 오류 발생")
####################################################################


####################################################################
    '''
    6. 차량 번호
    '''
    try:
        if violation_record:
            place_address = violation_record.place
            car_num = violation_record.car_num
        else:
            raise HTTPException(status_code = 400, detail = "등록된 차량 번호가 없습니다")

        if car_num:
            car_input = driver.find_element(By.XPATH, '//*[@id="VHRNO"]')
            car_input.clear()
            car_input.send_keys(car_num)
            print("차량 번호 입력 완료")
        else:
            driver.find_element(By.XPATH, '//*[@id="chkNoVhrNo"]').click()
            print("차량 번호 없음")

    except Exception:
        print("차량 번호 입력 도중 오류")
####################################################################


####################################################################
    '''
    7. 발생일자 & 8. 발생 시각
    '''
    try:
        if violation_record and violation_record.time:
            detected_hour = violation_record.time.strftime("%H")
            detected_min = violation_record.time.strftime("%M")
        else:
            raise HTTPException(status_code = 400, detail = "등록된 날짜 정보가 없음")
        
        date = driver.find_element(By.XPATH, '//*[@id="DEVEL_DATE"]')
        date.clear()
        date.send_keys(detected_date)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()

        hour_select = Select(driver.find_element(By.ID, "DEVEL_TIME_HH"))
        hour_select.select_by_value(detected_hour)

        min_select = Select(driver.find_element(By.ID, "DEVEL_TIME_MM"))
        min_select.select_by_value(detected_min)

    except Exception:
        print("오류 발생")
####################################################################


####################################################################
    '''
    10. 신고 내용 공유 여부
    '''
    try:
        신고 = False
        if 신고:
            pass
        else:
            driver.find_element(By.XPATH,'//*[@id="frmSafeReport"]/div[2]/article/div/div[3]/table/tbody/tr[11]/td/article/div/label[2]').click()
    except Exception:
        print("오류 발생")

    return {"message": "신고가 정상적으로 접수되었습니다."}



