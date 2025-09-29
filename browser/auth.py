"""
Udemy 인증 처리 모듈 (반자동 로그인)
"""

import json
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

class UdemyAuth:
    def __init__(self, headless=False, log_callback=None):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.log_callback = log_callback or print
        self.is_logged_in = False

    def setup_driver(self):
        """Chrome 드라이버 설정 (최대한 봇 탐지 우회)"""
        try:
            self.log_callback("🔧 브라우저 설정 중...")

            # Chrome 옵션 설정
            chrome_options = Options()

            # 자동화 탐지 우회를 위한 핵심 옵션들
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 일반적인 Chrome 설정
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            # User-Agent 설정
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

            # 기존 Chrome 프로필 사용 (로그인 상태 유지)
            import os
            user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            if self.headless:
                chrome_options.add_argument("--headless")

            # 드라이버 생성
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # JavaScript로 자동화 속성 제거
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // Chrome 속성 추가
                    window.navigator.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };

                    // 권한 API 수정
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );

                    // 플러그인 추가
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });

                    // 언어 설정
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                '''
            })

            # WebDriverWait 설정
            self.wait = WebDriverWait(self.driver, Config.WAIT_TIMEOUT)

            self.log_callback("✅ 브라우저 설정 완료")
            self.log_callback("💡 팁: CAPTCHA가 나오면 수동으로 해결해주세요")
            return True

        except Exception as e:
            self.log_callback(f"❌ 브라우저 설정 실패: {str(e)}")
            return False

    def load_saved_session(self) -> bool:
        """저장된 세션 쿠키 로드"""
        try:
            session_file = Config.get_session_file_path()
            if not session_file.exists():
                self.log_callback("💾 저장된 세션이 없습니다.")
                return False

            self.log_callback("💾 저장된 세션 로드 시도...")

            # Udemy 메인 페이지로 이동
            self.driver.get(Config.UDEMY_BASE_URL)
            time.sleep(2)

            # 쿠키 로드
            with open(session_file, 'r') as f:
                cookies = json.load(f)

            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    # 만료된 쿠키는 무시
                    continue

            # 페이지 새로고침으로 세션 적용
            self.driver.refresh()
            time.sleep(3)

            # 로그인 상태 확인
            if self.check_login_status():
                self.log_callback("✅ 저장된 세션으로 로그인 성공!")
                self.is_logged_in = True
                return True
            else:
                self.log_callback("⚠️ 저장된 세션이 만료되었습니다.")
                return False

        except Exception as e:
            self.log_callback(f"❌ 세션 로드 실패: {str(e)}")
            return False

    def save_session_cookies(self):
        """현재 세션 쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            session_file = Config.get_session_file_path()

            with open(session_file, 'w') as f:
                json.dump(cookies, f)

            self.log_callback("💾 세션 저장 완료")

        except Exception as e:
            self.log_callback(f"❌ 세션 저장 실패: {str(e)}")

    def check_login_status(self) -> bool:
        """로그인 상태 확인"""
        try:
            # My Learning 링크나 프로필 아이콘이 있는지 확인
            profile_indicators = [
                "//a[contains(@href, '/home/my-courses')]",
                "//button[contains(@class, 'user-avatar')]",
                "//div[contains(@class, 'user-menu')]",
                "//a[contains(text(), 'My learning')]"
            ]

            for xpath in profile_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
                        return True
                except:
                    continue

            return False

        except Exception:
            return False

    def semi_automatic_login(self, email: str, password: str = "") -> bool:
        """반자동 로그인 (2FA 처리 - 비밀번호 불필요)"""
        try:
            self.log_callback("🔐 2FA 로그인 플로우 시작...")

            # 1. 저장된 세션 확인
            self.log_callback("💾 저장된 세션 확인 중...")
            if self.load_saved_session():
                return True

            # 2. 메인 페이지로 이동 후 로그인 버튼 클릭
            self.log_callback("🏠 Udemy 메인 페이지로 이동...")
            self.driver.get(Config.UDEMY_BASE_URL)
            time.sleep(3)

            # 3. 로그인 버튼 찾아서 클릭
            self.log_callback("🔍 로그인 버튼 찾는 중...")
            if not self._click_login_button():
                self.log_callback("❌ 로그인 버튼을 찾을 수 없습니다.")
                self.log_callback("🔍 현재 페이지 URL: " + self.driver.current_url)
                return False

            time.sleep(3)

            # 4. 이메일 입력
            self.log_callback("📧 이메일 입력 중...")
            try:
                email_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "id_email"))
                )
                email_field.clear()
                self._human_like_typing(email_field, email)
                self.log_callback("✅ 이메일 입력 완료")
            except Exception as e:
                self.log_callback(f"❌ 이메일 입력 실패: {str(e)}")
                self.log_callback("🔍 현재 페이지 URL: " + self.driver.current_url)
                # 페이지 소스의 일부를 확인해보기
                title = self.driver.title
                self.log_callback(f"🔍 페이지 제목: {title}")
                return False

            # 5. Continue 버튼 클릭 (비밀번호 입력 없이)
            self.log_callback("🖱️ Continue 버튼 클릭...")
            try:
                continue_button = self.driver.find_element(By.ID, "submit-id-submit")
                self._human_like_click(continue_button)
                self.log_callback("✅ Continue 버튼 클릭 완료")
            except Exception as e:
                self.log_callback(f"❌ Continue 버튼 클릭 실패: {str(e)}")
                return False

            time.sleep(5)

            # 6. 2FA 코드 입력 대기 (사용자가 수동으로 처리)
            self.log_callback("📧 2FA 인증 코드를 입력해주세요!")
            self.log_callback("⏳ 코드 입력 완료까지 최대 5분 대기 중...")

            # 7. 홈화면 이동 확인 후 "내 학습" 버튼 대기
            if self._wait_for_home_and_my_learning():
                self.log_callback("✅ 2FA 로그인 성공!")
                self.is_logged_in = True
                self.save_session_cookies()
                return True
            else:
                self.log_callback("❌ 로그인 완료를 확인할 수 없습니다.")
                return False

        except Exception as e:
            self.log_callback(f"❌ 로그인 실패: {str(e)}")
            self.log_callback(f"🔍 현재 페이지 URL: {self.driver.current_url}")
            import traceback
            self.log_callback(f"🔍 스택 트레이스: {traceback.format_exc()}")
            return False

    def _click_login_button(self) -> bool:
        """메인 페이지에서 로그인 버튼 클릭"""
        try:
            self.log_callback("🔍 다양한 로그인 버튼 선택자로 검색 중...")

            login_selectors = [
                "//a[contains(text(), 'Log in')]",
                "//button[contains(text(), 'Log in')]",
                "//a[contains(text(), '로그인')]",
                "//a[contains(@href, 'login')]",
                ".login-button",
                "[data-purpose='header-login']",
                ".header-login",
                "a[href*='login']",
                "button[type='submit'][value*='login']"
            ]

            for i, selector in enumerate(login_selectors):
                try:
                    self.log_callback(f"🔍 시도 {i+1}/{len(login_selectors)}: {selector}")

                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    self.log_callback(f"   발견된 요소 수: {len(elements)}")

                    for j, button in enumerate(elements):
                        if button and button.is_displayed():
                            self.log_callback(f"   요소 {j+1} 클릭 시도 중...")
                            self._human_like_click(button)
                            self.log_callback("✅ 로그인 버튼 클릭 완료")
                            return True
                        else:
                            self.log_callback(f"   요소 {j+1} 숨겨져 있음")

                except Exception as e:
                    self.log_callback(f"   ❌ 선택자 실패: {str(e)}")
                    continue

            # 모든 선택자 실패 시 현재 페이지 정보 출력
            self.log_callback("❌ 모든 로그인 버튼 선택자 실패")
            self.log_callback(f"🔍 현재 URL: {self.driver.current_url}")
            self.log_callback(f"🔍 페이지 제목: {self.driver.title}")

            # 페이지에 있는 모든 링크 텍스트 확인
            links = self.driver.find_elements(By.TAG_NAME, "a")
            self.log_callback(f"🔍 페이지의 모든 링크 개수: {len(links)}")
            for i, link in enumerate(links[:10]):  # 처음 10개만
                try:
                    text = link.text.strip()
                    if text:
                        self.log_callback(f"   링크 {i+1}: '{text}'")
                except:
                    continue

            return False

        except Exception as e:
            self.log_callback(f"❌ _click_login_button 예외 발생: {str(e)}")
            import traceback
            self.log_callback(f"🔍 스택 트레이스: {traceback.format_exc()}")
            return False

    def _wait_for_home_and_my_learning(self, timeout=300) -> bool:
        """홈화면 이동 후 '내 학습' 버튼 확인까지 대기"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # "내 학습" 버튼이 나타나는지 확인
                # TODO: 실제 "내 학습" 버튼 선택자로 교체 필요
                my_learning_selectors = [
                    "//a[contains(text(), 'My learning')]",
                    "//a[contains(text(), '내 학습')]",
                    "//a[contains(@href, '/home/my-courses')]",
                    "[data-purpose='my-learning-nav']"
                ]

                for selector in my_learning_selectors:
                    try:
                        if selector.startswith("//"):
                            element = self.driver.find_element(By.XPATH, selector)
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)

                        if element and element.is_displayed():
                            self.log_callback("✅ 홈화면 진입 및 '내 학습' 버튼 확인!")
                            return True
                    except:
                        continue

                # 진행 상황 표시 (30초마다)
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0 and elapsed > 0:
                    remaining = int((timeout - elapsed) / 60)
                    self.log_callback(f"⏳ 대기 중... (남은 시간: 약 {remaining}분)")

                time.sleep(2)

            except Exception as e:
                self.log_callback(f"⚠️ 홈화면 확인 중 오류: {str(e)}")
                time.sleep(5)

        self.log_callback("❌ 홈화면 진입 타임아웃 - 다시 시도해주세요.")
        return False

    def _human_like_typing(self, element, text):
        """인간처럼 타이핑 시뮬레이션"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def _human_like_click(self, element):
        """인간처럼 클릭 시뮬레이션"""
        # 약간의 대기 후 클릭
        time.sleep(random.uniform(0.5, 1.0))
        element.click()
        time.sleep(random.uniform(0.5, 1.5))

    def logout(self):
        """로그아웃"""
        try:
            if self.is_logged_in:
                self.log_callback("🚪 로그아웃 중...")
                # 세션 파일 삭제
                session_file = Config.get_session_file_path()
                if session_file.exists():
                    session_file.unlink()
                self.is_logged_in = False
                self.log_callback("✅ 로그아웃 완료")
        except Exception as e:
            self.log_callback(f"❌ 로그아웃 실패: {str(e)}")

    def cleanup(self):
        """리소스 정리"""
        try:
            if self.driver:
                self.driver.quit()
                self.log_callback("🧹 브라우저 정리 완료")
        except Exception as e:
            self.log_callback(f"⚠️ 브라우저 정리 중 오류: {str(e)}")

    def launch_debug_browser(self):
        """디버깅 브라우저 실행"""
        try:
            from browser.manager import ExistingBrowserManager

            manager = ExistingBrowserManager(log_callback=self.log_callback)
            success = manager.start_chrome_with_debug_port()

            if success:
                self.log_callback("✅ Chrome 디버깅 브라우저 실행 완료")
                return True
            else:
                self.log_callback("❌ Chrome 디버깅 브라우저 실행 실패")
                return False

        except Exception as e:
            self.log_callback(f"❌ 디버깅 브라우저 실행 중 오류: {str(e)}")
            return False

    def connect_to_existing_browser(self):
        """기존 디버깅 브라우저에 연결"""
        try:
            from browser.manager import ExistingBrowserManager

            manager = ExistingBrowserManager(log_callback=self.log_callback)
            success = manager.connect_to_existing_browser()

            if success:
                # 드라이버 객체를 가져와서 설정
                self.driver = manager.driver
                self.wait = WebDriverWait(self.driver, 10)
                self.log_callback("✅ 기존 브라우저 연결 완료")
                return True
            else:
                self.log_callback("❌ 기존 브라우저 연결 실패")
                return False

        except Exception as e:
            self.log_callback(f"❌ 브라우저 연결 중 오류: {str(e)}")
            return False

    def __del__(self):
        """소멸자"""
        self.cleanup()