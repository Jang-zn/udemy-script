#!/usr/bin/env python3
"""
Udemy 스크래퍼 메인 진입점
"""

import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """메인 함수"""
    try:
        from gui.pyside_ui import run_pyside_gui
        print("🚀 Udemy Scraper GUI 시작...")
        run_pyside_gui()

    except ImportError as e:
        print(f"❌ 모듈 import 실패: {str(e)}")
        print("📦 PySide6를 설치하세요: pip3 install pyside6")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 애플리케이션 시작 실패: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()