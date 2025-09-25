"""
기존 Chrome 브라우저 세션 재사용 모듈
"""

import time
import socket
import subprocess
import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class ExistingBrowserManager:
    def __init__(self, log_callback=None):
        self.driver = None
        self.wait = None
        self.log_callback = log_callback or print

    def check_debug_port(self, port=9222):
        """디버그 포트가 열려있는지 확인"""
        try:
            # 소켓으로 포트 확인
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()

            if result == 0:
                self.log_callback(f"✅ 포트 {port} 열려있음")
                # HTTP 요청으로 Chrome DevTools API 확인
                try:
                    response = requests.get(f"http://127.0.0.1:{port}/json", timeout=3)
                    if response.status_code == 200:
                        tabs = response.json()
                        self.log_callback(f"🔍 Chrome 탭 {len(tabs)}개 발견")
                        return True
                except:
                    pass
            else:
                self.log_callback(f"❌ 포트 {port} 닫혀있음")
            return False
        except Exception as e:
            self.log_callback(f"⚠️ 포트 확인 실패: {str(e)}")
            return False

    def connect_to_existing_browser(self, debug_port=9222):
        """기존 Chrome 브라우저에 연결"""
        try:
            self.log_callback("🔗 기존 Chrome 브라우저에 연결 시도...")

            # 먼저 디버그 포트 확인
            if not self.check_debug_port(debug_port):
                self.log_callback(f"⚠️ Chrome 디버그 포트 {debug_port}가 열려있지 않습니다")
                self.log_callback("💡 Chrome을 --remote-debugging-port=9222로 시작해야 합니다")
                return False

            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

            # 로그 레벨 설정
            chrome_options.add_argument("--log-level=3")  # 에러만 출력

            # 서비스 설정 (로그 비활성화)
            from selenium.webdriver.chrome.service import Service
            service = Service()
            service.log_path = os.devnull if hasattr(os, 'devnull') else '/dev/null'

            # 드라이버 생성 (기존 브라우저에 연결)
            self.log_callback("🔌 WebDriver 연결 시도...")
            self.log_callback(f"   연결 주소: 127.0.0.1:{debug_port}")

            try:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, 10)

                # 연결 확인
                current_url = self.driver.current_url
                self.log_callback("✅ 기존 브라우저에 연결 성공!")
                self.log_callback(f"🔍 현재 페이지: {current_url}")

                # Udemy 관련 페이지 확인
                if 'udemy.com' in current_url:
                    self.log_callback("🎯 Udemy 사이트 감지됨")
                else:
                    self.log_callback("⚠️ Udemy 사이트가 아닙니다. Udemy로 이동하세요")

                return True

            except Exception as driver_error:
                self.log_callback(f"❌ WebDriver 연결 실패: {str(driver_error)}")
                self.log_callback("🔍 Chrome이 디버그 모드로 실행되었는지 확인하세요")
                return False

        except Exception as e:
            self.log_callback(f"❌ 연결 과정 중 오류: {str(e)}")
            import traceback
            self.log_callback(f"🔍 상세 오류: {traceback.format_exc()}")
            return False

    def find_chrome_executable(self):
        """Chrome 실행 파일 경로 찾기"""
        possible_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser'
        ]

        for path in possible_paths:
            import os
            if os.path.exists(path):
                self.log_callback(f"🔍 Chrome 발견: {path}")
                return path

        self.log_callback("❌ Chrome 실행 파일을 찾을 수 없습니다")
        return None

    def kill_existing_chrome_debug_processes(self):
        """기존 Chrome 디버그 프로세스 종료"""
        try:
            self.log_callback("🔄 기존 Chrome 디버그 프로세스 확인...")
            # 포트를 사용하는 프로세스 확인
            result = subprocess.run(['lsof', '-ti:9222'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    self.log_callback(f"🛑 기존 프로세스 {pid} 종료")
                    subprocess.run(['kill', '-9', pid], capture_output=True)
                time.sleep(1)
        except Exception as e:
            self.log_callback(f"⚠️ 프로세스 정리 중 오류: {str(e)}")

    def start_chrome_with_debug_port(self, debug_port=9222):
        """디버그 포트를 활성화한 Chrome 시작"""
        try:
            self.log_callback("🌐 디버그 모드로 Chrome 시작 중...")

            # Chrome 실행 파일 찾기
            chrome_path = self.find_chrome_executable()
            if not chrome_path:
                return False

            # 기존 디버그 프로세스 정리
            self.kill_existing_chrome_debug_processes()

            # Chrome을 디버그 포트와 함께 시작
            chrome_cmd = [
                chrome_path,
                f'--remote-debugging-port={debug_port}',
                '--user-data-dir=/tmp/chrome_debug_profile_udemy',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                'https://www.udemy.com'
            ]

            self.log_callback(f"🚀 Chrome 시작 명령: {' '.join(chrome_cmd[:3])}...")
            subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Chrome이 시작될 때까지 대기
            self.log_callback("⏳ Chrome 시작 대기 중...")
            for i in range(10):  # 10초 대기
                time.sleep(1)
                if self.check_debug_port(debug_port):
                    break
                self.log_callback(f"   대기 중... {i+1}/10초")
            else:
                self.log_callback("❌ Chrome이 정상적으로 시작되지 않았습니다")
                return False

            self.log_callback("✅ Chrome이 디버그 모드로 시작되었습니다!")
            self.log_callback("📌 수동으로 로그인하고 '내 학습' 페이지로 이동하세요")
            return True

        except Exception as e:
            self.log_callback(f"❌ Chrome 시작 실패: {str(e)}")
            return False

    def cleanup(self):
        """연결 해제 (브라우저는 닫지 않음)"""
        try:
            if self.driver:
                self.driver.quit()
                self.log_callback("🔗 브라우저 연결 해제 (브라우저는 열린 상태 유지)")
        except Exception as e:
            self.log_callback(f"⚠️ 연결 해제 중 오류: {str(e)}")

    def get_browser_status(self):
        """브라우저 상태 확인"""
        if not self.driver:
            return "연결되지 않음"
        try:
            title = self.driver.title
            url = self.driver.current_url
            return f"연결됨 - {title[:30]}... ({url[:50]}...)"
        except:
            return "연결 끊어짐"