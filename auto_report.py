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
from models import User, Detected, Report
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from database import SessionLocal, engine
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoAlertPresentException

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 안전신문고 계정 가져오기
def get_safety_credentials(user_id: str, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.site_id and user.site_pw:
        return user.site_id, user.site_pw
    return None, None

# 사용자의 최근 신고할 위반 사항 가져오기
def get_user_violation(user_id: str, db: Session):
    violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
    if violation_record:
        return violation_record.violation
    return None

##################################################################
'''
신고 자동 실행 API
'''
@router.post("/report/apply")
def report_violation(
    detected_id : int,
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

    detected_record = db.query(Detected).filter(
        Detected.detected_id == detected_id,
        Detected.user_id == user_id
    ).first()

    if not detected_record:
        raise HTTPException(status_code = 403, detail = "해당 신고 데이터에 접근할 권한이 없습니다.")


    site_id, site_pw = get_safety_credentials(user_id, db)
    if not site_id or not site_pw:
        raise HTTPException(status_code=400, detail="안전신문고 로그인 정보가 없습니다.")

    violation = detected_record.violation
    place_address = detected_record.place
    car_num = detected_record.car_num

    if not violation: raise HTTPException(status_code = 400, detail = "신고할 위반 사항이 없브니다.")


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
        url = "https://www.safetyreport.go.kr/#safereport/safereport3"
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "ReportTypeSelect"))
        )
        print("신고 페이지 로드 완료")

    except Exception as e:
        print(f"신고 페이지 로드 중 오류 발생: {e}")
        driver.quit()
        raise HTTPException(status_code=500, detail="신고 페이지 로드 실패")

    ##################################################################
    '''
    1. 신고 유형 선택 
    '''
    
    try:
        violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
        if not violation_record or not violation_record.violation:
            raise HTTPException(status_code=400, detail="신고할 위반 사항이 없습니다.")

        violation = violation_record.violation
        print(f"현재 violation 값: {violation}")

        # 드롭다운 요소 대기
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ReportTypeSelect"))
        )
        
        # Select 클래스 사용
        select = Select(dropdown)
        time.sleep(1)  # 드롭다운 옵션이 로드될 시간을 확보

        # 신고 유형 옵션 매핑
        violation_mapping = {
            "Weaving": "이륜차 위반",
            "No Helmet": "이륜차 위반",
            "Stealth": "불법등화, 반사판(지) 가림/손상",
            "Overloading": "기타 자동차 안전기준 위반",
        }
        
        selected_option = violation_mapping.get(violation, "교통위반(고속도로 포함)")
        print(f"선택할 옵션: {selected_option}")

        # 텍스트로 옵션 선택
        select.select_by_visible_text(selected_option)
        print(f"✅ 신고 유형 선택 완료: {selected_option}")

    except Exception as e:
        print(f"🚨 신고 유형 선택 중 오류 발생: {e}")
        driver.quit()
        raise HTTPException(status_code=500, detail=f"신고 유형 선택 실패: {str(e)}")

    ##################################################################
    '''
    2. 사진/동영상 파일 업로드 
    '''
    """
    try:
    # 로그인한 user_id로 최신 detected 레코드 조회
        violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
        if not violation_record or not violation_record.detected_id:
            raise HTTPException(status_code=400, detail="업로드할 동영상 파일 정보가 없습니다.")

        detected_id = violation_record.detected_id
        video_extension = os.path.splitext(violation_record.d_video_path)[1]  # 예: ".mp4"
        video_filename = f"{detected_id}{video_extension}"
        video_path = os.path.abspath(os.path.join("C:\\project\\backend\\videos", video_filename))

        # 파일 및 경로 검증
        print(f"파일 경로: {video_path}")
        if not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail=f"파일을 찾을 수 없습니다: {video_path}")

        file_size = os.path.getsize(video_path)
        if file_size > 130 * 1024 * 1024:  # 130MB 체크
            raise HTTPException(status_code=400, detail=f"파일 크기가 130MB를 초과합니다: {file_size} bytes")
        print(f"파일 크기 확인: {file_size} bytes (130MB 이하)")

        
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)  # 첫 번째 iframe 내부로 진입
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[starts-with(@id, 'file_o_')]"))
        )
        file_input.send_keys(video_path)
        driver.switch_to.default_content()
        print("파일 업로드 완료")
    except Exception as e:
        print(f"🚨 파일 업로드 실패: {e}")
        driver.quit()  # 드라이버 종료를 추가해 리소스 누수 방지
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")
    """
    ##################################################################


    ##################################################################
    '''
    3. 신고 발생 지역
    '''
    try:
        violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
        place_address = violation_record.place if violation_record else None
        if not place_address:
            raise HTTPException(status_code=400, detail="등록된 장소 정보가 없습니다.")
        driver.find_element(By.XPATH, '//*[@id="btnFindLoc"]').click()
        original_window = driver.current_window_handle
        time.sleep(1)
        all_windows = driver.window_handles
        if len(all_windows) >1:
            new_window = [w for w in all_windows if w != original_window][0]
            driver.switch_to.window(new_window)
            print("새 창으로 전환 완료")
        else:
            print("동일 창 내 팝업으로 확인됨")
        time.sleep(1)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print("발견된 iframe 개수:", len(iframes))
            for idx, iframe in enumerate(iframes):
                print(
                    f"iframe[{idx}] - id={iframe.get_attribute('id')}, "
                    f"title={iframe.get_attribute('title')}, "
                    f"src={iframe.get_attribute('src')}")
        else:
            print("iframe 없음. 모달 div 가능성 ")
        try:
            iframe_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title = '우편번호 검색 프레임']")))
            driver.switch_to.frame(iframe_element)
            print("iframe 전환 완료")
            wait = WebDriverWait(driver, 10)
            modal = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "popup_body")))
            search_input = wait.until(EC.presence_of_element_located((By.ID, "region_name")))
            search_input.send_keys(place_address)
            search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn_search")))
            search_button.click()
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li")))
            first_item = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul/li[1]/dl/dd[1]/span/button")))       
            first_item.click()
        except Exception as e:
            print("iframe 접근 혹은 내부 요소 처리 중 예외 발생:", e)
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) == 1)  # 창이 닫힐 때까지 기다림
        remaining_windows = driver.window_handles
        if original_window in remaining_windows:
            driver.switch_to.window(original_window)
            print("메인 창으로 정상 복귀")
        else:
            print("기존 창이 닫힘, 남아 있는 창으로 전환")
            driver.switch_to.window(remaining_windows[0])
    except Exception as e:
        print(f"신고 발생 지역 처리 중 오류 발생: {e}")
        driver.quit()
        raise HTTPException(status_code=500, detail=f"신고 발생 지역 처리 실패: {e}")
    ##################################################################


    ##################################################################
    '''
    4. 제목
    '''
    try:
        violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
        if not violation_record or not violation_record.violation:
            raise HTTPException(status_code=400, detail="등록된 위반 사항이 없습니다.")
        violation_translate = {
            "No Helmet": "헬멧 미착용",
            "Stealth": "스텔스",
            "Overloading": "과적차량",
            "Weaving": "급차선 변경(칼치기)"}
        report_title = violation_translate.get(violation_record.violation, violation_record.violation)
        제목 = driver.find_element(By.XPATH, '//*[@id="C_A_TITLE"]')
        제목.clear()
        제목.send_keys(report_title)
        print("제목 입력 완료")
        #driver.switch_to.default_content()
    except Exception as e:
        print(f"제목 입력 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"제목 입력 실패: {e}")
    ##################################################################
    


    ##################################################################
    '''
    5. 신고내용
    '''
    try:
        if violation_record:
            detected_date = violation_record.time.strftime("%Y.%m.%d")
            detected_time = violation_record.time.strftime("%H:%M")
            timestamp = f"{detected_date} {detected_time}"
            place = violation_record.place
            car_num = violation_record.car_num
            report_content = f"""{car_num} 차량 {violation_translate.get(violation_record.violation, violation_record.violation)} 행위 목격했습니다. 블랙박스 영상 첨부합니다.
        
                                * 차량번호 : {car_num}
                                * 발생일자 : {detected_date}
                                * 발생시각 : {detected_time}
                                * 위반장소 : {place}
                            """
            content = driver.find_element(By.XPATH, '//*[@id="C_A_CONTENTS"]')
            content.clear()
            content.send_keys(report_content)
            print("신고 내용 입력 완료")
        else:
            raise HTTPException(status_code=400, detail="신고할 데이터가 DB에 존재하지 않습니다.")
    except Exception as e:
        print(f"신고 내용 입력 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"신고 내용 입력 실패: {e}")
    ##################################################################


    ##################################################################
    '''
    6. 차량 번호
    '''
    
    try:
        if violation_record:
            car_num = violation_record.car_num
        else:
            raise HTTPException(status_code=400, detail="등록된 차량 번호가 없습니다")
        if car_num:
            car_input = driver.find_element(By.XPATH, '//*[@id="VHRNO"]')
            car_input.clear()
            car_input.send_keys(car_num)
            print("차량 번호 입력 완료")
        else:
            driver.find_element(By.XPATH, '//*[@id="chkNoVhrNo"]').click()
            print("차량 번호 없음")
    except Exception as e:
        print(f"차량 번호 입력 도중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"차량 번호 입력 실패: {e}")
    ##################################################################
    

    ##################################################################
    '''
    7. 발생일자 & 8. 발생 시각
    '''
    try:
        if violation_record and violation_record.time:
            detected_date = violation_record.time.strftime("%Y.%m.%d")
            detected_hour = violation_record.time.strftime("%H")
            detected_min = violation_record.time.strftime("%M")
        else:
            raise HTTPException(status_code=400, detail="등록된 날짜 정보가 없음")
        
        date = driver.find_element(By.XPATH, '//*[@id="DEVEL_DATE"]')
        date.clear()
        date.send_keys(detected_date)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()

        hour_select = Select(driver.find_element(By.ID, "DEVEL_TIME_HH"))
        hour_select.select_by_value(detected_hour)

        min_select = Select(driver.find_element(By.ID, "DEVEL_TIME_MM"))
        min_select.select_by_value(detected_min)
        print("발생일자 및 시각 입력 완료")

    except Exception as e:
        print(f"발생일자 및 시각 입력 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"발생일자 및 시각 입력 실패: {e}")

    ##################################################################
    '''
    10. 신고 내용 공유 여부
    '''
    try:
        신고 = False
        if 신고:
            pass
        else:
            driver.find_element(By.XPATH, '//*[@id="frmSafeReport"]/div[2]/article/div/div[3]/table/tbody/tr[11]/td/article/div/label[2]').click()
            print("신고 내용 공유 여부 선택 완료")
    except Exception as e:
        print(f"신고 내용 공유 여부 선택 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"신고 내용 공유 여부 선택 실패: {e}")
    ##################################################################


    ##################################################################
    '''
    최종 제출 버튼
    '''
    try:
    # 페이지 맨 아래로 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        # 신청 버튼 요소 찾기기
        apply_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'신청')]")))
        # 버튼 활성화 체크
        if apply_button.is_displayed() and apply_button.is_enabled():
            print("✅ 버튼이 활성화됨, 클릭 시도")
            # JavaScript 클릭 시도
            driver.execute_script("$$.fnGoNext(2);")
            print("🚀 신청 버튼 JavaScript 클릭 완료!")
        else:
            print("⚠️ 버튼이 비활성화 상태입니다.")
            raise Exception("신청 버튼이 활성화되지 않음")
    except Exception as e:
        print(f"🚨 신청 버튼 클릭 관련 오류 발생: {e}")
        return {"error": "신청 버튼 클릭 실패"}
    ##################################################################
    

    ##################################################################
    '''
    팝업창 확인 누르기 
    '''

    try:
        # 1번 팝업
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"팝업 메시지: {alert.text}")
        alert.accept()
        print("팝업 확인 버튼 클릭 완료!")
        # 2번 팝업
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"두 번째 팝업 메시지: {alert.text}")
        alert.accept()
        print("두 번째 팝업 확인 버튼 클릭 완료!!")
    except NoAlertPresentException:
        print("팝업이 감지되지 않았습니다.")
    except Exception as e:
        print(f"팝업 처리 중 오류 발생: {e}")


    try:
        url = "https://www.safetyreport.go.kr/#mypage/mysafereport/44012853"
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "ReportTypeSelect"))
        )
        print("신고 페이지 로드 완료")

        try:
            report_number_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'safetyreport.go.kr')]"))
            )
            report_number = report_number_element.text.strip()
            print(f"🚀 신고번호 확인 완료: {report_number}")
        except Exception as e:
            print(f"🚨 신고번호 추출 중 오류 발생: {e}")
            report_number = None  # 에러 발생 시 None 처리


        if report_number:
            try:
                db = SessionLocal()
                violation_record = db.query(Detected).filter(Detected.user_id == user_id).order_by(Detected.detected_id.desc()).first()
                if violation_record:
                    violation_record.report_id = report_number  # 신고번호 업데이트
                    db.commit()
                    print(f"✅ DB 업데이트 완료! detected_id={violation_record.detected_id}, report_id={report_number}")
                else:
                    print("🚨 DB에서 해당 user_id의 신고 내역을 찾을 수 없음")
            except Exception as e:
                print(f"🚨 DB 업데이트 중 오류 발생: {e}")
                db.rollback()
            finally:
                db.close()
        else:
            print("🚨 신고번호가 없어서 DB 업데이트를 수행하지 않음")
    except Exception:
        print("무언가 단단히 잘못되었다.")
    input("디버깅용")
    ##################################################################




