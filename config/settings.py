"""
Udemy 스크래퍼 설정 관리 모듈
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class Config:
    """설정 관리 클래스"""

    # 기본 디렉토리 설정
    BASE_DIR = Path(__file__).parent.parent
    OUTPUT_DIR = BASE_DIR / (os.getenv('OUTPUT_DIR', 'output_udemy_scripts'))
    SESSION_DIR = BASE_DIR / 'sessions'

    # Udemy 관련 설정
    UDEMY_BASE_URL = "https://www.udemy.com"
    UDEMY_LOGIN_URL = "https://www.udemy.com/join/login-popup/"
    UDEMY_MY_LEARNING_URL = "https://www.udemy.com/home/my-courses/learning/"

    # 브라우저 설정
    HEADLESS_MODE = False  # 항상 False로 고정 (2FA 수동 입력 필요)
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'true').lower() == 'true'

    # 타이밍 설정
    WAIT_TIMEOUT = 10  # 요소 대기 시간 (초)
    BETWEEN_LECTURES_DELAY = (1, 3)  # 강의 간 대기시간 (초) - 랜덤
    PAGE_LOAD_DELAY = 2  # 페이지 로드 대기시간 (초)

    # 재시도 설정
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 재시도 간격 (초)

    # 로그 설정
    LOG_LEVEL = "INFO" if not DEBUG_MODE else "DEBUG"

    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.SESSION_DIR.mkdir(exist_ok=True)

    @classmethod
    def get_output_directory(cls) -> Path:
        """출력 디렉토리 반환"""
        cls.ensure_directories()
        return cls.OUTPUT_DIR

    @classmethod
    def get_course_output_dir(cls, course_name: str) -> Path:
        """강의별 출력 디렉토리 경로 반환"""
        # 파일명에 사용할 수 없는 문자 제거
        safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).strip()
        return cls.OUTPUT_DIR / safe_name

    @classmethod
    def get_session_file_path(cls) -> Path:
        """세션 쿠키 파일 경로 반환"""
        return cls.SESSION_DIR / 'udemy_session.json'