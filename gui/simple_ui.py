#!/usr/bin/env python3
"""
가장 단순한 GUI - segfault 없이 작동하는 버전
"""

import sys
import threading
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLineEdit, QTextEdit, QLabel, QProgressBar
)
from PySide6.QtCore import Signal, QObject

from app import UdemyScraperApp


class SimpleSignals(QObject):
    """시그널 클래스"""
    log_signal = Signal(str)
    progress_signal = Signal(int, int)
    status_signal = Signal(str)


class SimpleUdemyGUI(QMainWindow):
    """매우 단순한 GUI"""

    def __init__(self):
        super().__init__()
        self.signals = SimpleSignals()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("Udemy Scraper")
        self.setFixedSize(600, 500)

        # 메인 위젯
        main = QWidget()
        self.setCentralWidget(main)

        # 레이아웃
        layout = QVBoxLayout(main)
        layout.setSpacing(10)

        # 제목
        title = QLabel("Udemy Script Scraper")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # 버튼들
        btn_layout = QHBoxLayout()

        self.debug_btn = QPushButton("디버그 브라우저")
        self.debug_btn.clicked.connect(self.launch_debug)

        self.connect_btn = QPushButton("브라우저 연결")
        self.connect_btn.clicked.connect(self.connect_browser)

        self.reset_btn = QPushButton("초기화")
        self.reset_btn.clicked.connect(self.reset_all)

        btn_layout.addWidget(self.debug_btn)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        # 강의명 입력
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("강의명:"))
        self.course_input = QLineEdit()
        input_layout.addWidget(self.course_input)
        layout.addLayout(input_layout)

        # 진행률
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # 상태
        self.status = QLabel("준비")
        layout.addWidget(self.status)

        # 로그
        self.log = QTextEdit()
        self.log.setMaximumHeight(200)
        layout.addWidget(self.log)

    def connect_signals(self):
        """시그널 연결"""
        self.signals.log_signal.connect(self.add_log)
        self.signals.progress_signal.connect(self.update_progress)
        self.signals.status_signal.connect(self.update_status)

    def launch_debug(self):
        """디버그 브라우저 실행"""
        self.debug_btn.setEnabled(False)
        self.status.setText("디버그 브라우저 실행 중...")

        def run():
            try:
                from browser.auth import UdemyAuth
                auth = UdemyAuth(headless=False, log_callback=self.emit_log)
                success = auth.launch_debug_browser()

                if success:
                    self.emit_status("디버그 브라우저 실행됨")
                    self.emit_log("✅ 디버그 브라우저 실행 완료")
                else:
                    self.emit_status("디버그 브라우저 실행 실패")

            except Exception as e:
                self.emit_log(f"❌ 오류: {e}")
            finally:
                self.debug_btn.setEnabled(True)

        threading.Thread(target=run, daemon=True).start()

    def connect_browser(self):
        """브라우저 연결하고 바로 스크래핑 시작"""
        course_name = self.course_input.text().strip()
        if not course_name:
            self.emit_log("❌ 강의명을 먼저 입력하세요")
            return

        self.connect_btn.setEnabled(False)
        self.status.setText("브라우저 연결 및 스크래핑 진행 중...")

        def run():
            try:
                from browser.auth import UdemyAuth
                from browser.course_finder import CourseFinder

                auth = UdemyAuth(headless=False, log_callback=self.emit_log)
                success = auth.connect_to_existing_browser()

                if success:
                    # 이미 디버그 브라우저에서 Udemy 열려있으니 바로 진행
                    finder = CourseFinder(auth.driver, auth.wait, self.emit_log)
                    my_learning = finder.go_to_my_learning()

                    if my_learning:
                        self.emit_status("스크래핑 진행 중...")
                        self.emit_log("🔍 강의 검색 및 스크래핑 시작...")

                        # 바로 강의 검색하고 스크래핑 진행
                        success = finder.find_and_scrape_course(course_name,
                                                               self.emit_progress,
                                                               self.emit_status)

                        if success:
                            self.emit_status("스크래핑 완료!")
                            self.emit_log("🎉 스크래핑이 완료되었습니다!")
                        else:
                            self.emit_status("스크래핑 실패")
                            self.emit_log("❌ 스크래핑에 실패했습니다")
                    else:
                        self.emit_status("로그인 후 다시 연결하세요")
                        self.emit_log("⚠️ 로그인이 필요합니다")
                else:
                    self.emit_status("브라우저 연결 실패")

            except Exception as e:
                self.emit_log(f"❌ 오류: {e}")
            finally:
                self.connect_btn.setEnabled(True)

        threading.Thread(target=run, daemon=True).start()


    def reset_all(self):
        """초기화"""
        self.course_input.clear()
        self.progress.setValue(0)
        self.status.setText("준비")
        self.log.clear()
        self.emit_log("🔄 초기화 완료")

    def emit_log(self, message):
        """로그 발신"""
        timestamp = time.strftime("%H:%M:%S")
        self.signals.log_signal.emit(f"[{timestamp}] {message}")

    def emit_progress(self, current, total):
        """진행률 발신"""
        if total > 0:
            percent = int((current / total) * 100)
            self.signals.progress_signal.emit(current, total)

    def emit_status(self, status):
        """상태 발신"""
        self.signals.status_signal.emit(status)

    def add_log(self, message):
        """로그 추가"""
        self.log.append(message)

    def update_progress(self, current, total):
        """진행률 업데이트"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress.setValue(percent)

    def update_status(self, status):
        """상태 업데이트"""
        self.status.setText(status)


def run_simple_gui():
    """간단한 GUI 실행"""
    app = QApplication([])
    window = SimpleUdemyGUI()
    window.show()
    return app.exec()


if __name__ == "__main__":
    run_simple_gui()