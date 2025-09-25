#!/usr/bin/env python3
"""
Udemy Scraper GUI - PySide6 기반
"""

import sys
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLineEdit, QTextEdit, QLabel, QProgressBar,
    QFrame, QMessageBox
)
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QFont

from app import UdemyScraperApp


class WorkerThread(QThread):
    """백그라운드에서 스크래핑 작업을 수행하는 워커 쓰레드"""

    # 시그널 정의
    progress_updated = Signal(int, int)  # current, total
    status_updated = Signal(str)  # status message
    log_message = Signal(str)  # log message
    work_finished = Signal(bool)  # success

    def __init__(self, course_name):
        super().__init__()
        self.course_name = course_name
        self.scraper_app = None

    def run(self):
        """스크래핑 작업 실행"""
        try:
            self.scraper_app = UdemyScraperApp(
                progress_callback=self.emit_progress,
                status_callback=self.emit_status,
                log_callback=self.emit_log
            )

            # 빈 이메일/패스워드로 실행 (2FA 기반)
            success = self.scraper_app.run_workflow("", "", self.course_name)
            self.work_finished.emit(success)

        except Exception as e:
            self.emit_log(f"❌ 스크래핑 실패: {str(e)}")
            self.work_finished.emit(False)

    def emit_progress(self, current, total):
        """진행률 시그널 발신"""
        self.progress_updated.emit(current, total)

    def emit_status(self, status):
        """상태 시그널 발신"""
        self.status_updated.emit(status)

    def emit_log(self, message):
        """로그 시그널 발신"""
        self.log_message.emit(message)


class UdemyScraperGUI(QMainWindow):
    """Udemy Scraper GUI"""

    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Udemy Script Scraper")
        self.setFixedSize(800, 700)

        # 메인 위젯 및 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        self.create_title_section(layout)

        # 구분선
        self.create_separator(layout)

        # 브라우저 연결 섹션
        self.create_browser_section(layout)

        # 구분선
        self.create_separator(layout)

        # 강의 정보 입력 섹션
        self.create_course_section(layout)

        # 구분선
        self.create_separator(layout)

        # 진행률 섹션
        self.create_progress_section(layout)

        # 로그 섹션
        self.create_log_section(layout)

        # 상태 표시줄
        self.create_status_section(layout)

        # 초기 상태 설정
        self.reset_ui_state()

    def create_title_section(self, layout):
        """제목 섹션 생성"""
        title_label = QLabel("🎓 Udemy Script Scraper")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)

        subtitle_label = QLabel("안정적인 클릭 & 복사/붙여넣기 지원")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(subtitle_label)

    def create_separator(self, layout):
        """구분선 생성"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator)

    def create_browser_section(self, layout):
        """브라우저 연결 섹션 생성"""
        browser_label = QLabel("🌐 브라우저 연결")
        browser_label.setFont(QFont("", 12, QFont.Bold))
        browser_label.setStyleSheet("color: #34495e; margin: 5px 0;")
        layout.addWidget(browser_label)

        browser_layout = QHBoxLayout()

        self.connect_btn = QPushButton("브라우저 연결 & Udemy 이동")
        self.connect_btn.setMinimumHeight(45)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f5f8b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.connect_btn.clicked.connect(self.connect_browser)

        browser_layout.addWidget(self.connect_btn)
        layout.addLayout(browser_layout)

    def create_course_section(self, layout):
        """강의 입력 섹션 생성"""
        course_label = QLabel("📚 강의 정보")
        course_label.setFont(QFont("", 12, QFont.Bold))
        course_label.setStyleSheet("color: #34495e; margin: 5px 0;")
        layout.addWidget(course_label)

        # 강의명 입력
        course_input_layout = QHBoxLayout()

        course_name_label = QLabel("강의명:")
        course_name_label.setMinimumWidth(60)
        course_name_label.setStyleSheet("color: #2c3e50; font-weight: bold;")

        self.course_entry = QLineEdit()
        self.course_entry.setMinimumHeight(35)
        self.course_entry.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 8px;
                font-size: 11pt;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)

        course_input_layout.addWidget(course_name_label)
        course_input_layout.addWidget(self.course_entry)
        layout.addLayout(course_input_layout)

        # 스크래핑 버튼
        self.scraping_btn = QPushButton("🎬 스크래핑 시작")
        self.scraping_btn.setMinimumHeight(45)
        self.scraping_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11pt;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.scraping_btn.clicked.connect(self.start_scraping)
        layout.addWidget(self.scraping_btn)

    def create_progress_section(self, layout):
        """진행률 섹션 생성"""
        progress_label = QLabel("📊 진행 상황")
        progress_label.setFont(QFont("", 12, QFont.Bold))
        progress_label.setStyleSheet("color: #34495e; margin: 5px 0;")
        layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("대기 중...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #7f8c8d; margin: 5px 0;")
        layout.addWidget(self.progress_label)

    def create_log_section(self, layout):
        """로그 섹션 생성"""
        log_label = QLabel("📋 작업 로그")
        log_label.setFont(QFont("", 12, QFont.Bold))
        log_label.setStyleSheet("color: #34495e; margin: 5px 0;")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(250)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
                background-color: #f8f9fa;
                color: #2c3e50;
            }
        """)
        layout.addWidget(self.log_text)

    def create_status_section(self, layout):
        """상태 섹션 생성"""
        self.status_label = QLabel("🔄 준비 완료")
        self.status_label.setStyleSheet("""
            color: #2c3e50;
            font-weight: bold;
            padding: 8px;
            background-color: #ecf0f1;
            border-radius: 6px;
            margin-top: 5px;
        """)
        layout.addWidget(self.status_label)

    def reset_ui_state(self):
        """UI 상태 초기화"""
        self.connect_btn.setEnabled(True)
        self.scraping_btn.setEnabled(False)
        self.course_entry.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("대기 중...")
        self.status_label.setText("🔄 준비 완료")
        self.log_text.clear()

    def connect_browser(self):
        """브라우저 연결"""
        self.connect_btn.setEnabled(False)
        self.status_label.setText("🌐 브라우저 연결 중...")
        self.log_message("🔧 브라우저 연결 시도 중...")

        # 브라우저 연결 로직을 별도 쓰레드에서 실행
        def browser_connect():
            try:
                from browser.auth import UdemyAuth

                auth = UdemyAuth(headless=False, log_callback=self.log_message)
                success = auth.connect_to_existing_browser()

                if success:
                    # Udemy로 이동
                    auth.driver.get("https://www.udemy.com")

                    QTimer.singleShot(0, lambda: self.on_browser_connected(True))
                else:
                    QTimer.singleShot(0, lambda: self.on_browser_connected(False))

            except Exception as e:
                self.log_message(f"❌ 브라우저 연결 실패: {str(e)}")
                QTimer.singleShot(0, lambda: self.on_browser_connected(False))

        threading.Thread(target=browser_connect, daemon=True).start()

    def on_browser_connected(self, success):
        """브라우저 연결 결과 처리"""
        if success:
            self.status_label.setText("✅ 브라우저 연결됨 - 로그인 후 강의명 입력하세요")
            self.scraping_btn.setEnabled(True)
            self.log_message("✅ 브라우저 연결 성공!")
            self.log_message("💡 Udemy에서 수동으로 로그인한 후 강의명을 입력하고 스크래핑을 시작하세요.")
        else:
            self.status_label.setText("❌ 브라우저 연결 실패")
            self.connect_btn.setEnabled(True)
            self.log_message("❌ 브라우저 연결 실패. Chrome을 디버그 모드로 실행하세요.")

    def start_scraping(self):
        """스크래핑 시작"""
        course_name = self.course_entry.text().strip()
        if not course_name:
            QMessageBox.warning(self, "경고", "강의명을 입력해주세요!")
            return

        # UI 상태 변경
        self.scraping_btn.setEnabled(False)
        self.course_entry.setEnabled(False)
        self.connect_btn.setEnabled(False)
        self.status_label.setText("🎬 스크래핑 진행 중...")

        # 워커 쓰레드 시작
        self.worker_thread = WorkerThread(course_name)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.status_updated.connect(self.update_status)
        self.worker_thread.log_message.connect(self.log_message)
        self.worker_thread.work_finished.connect(self.on_scraping_finished)
        self.worker_thread.start()

    def update_progress(self, current, total):
        """진행률 업데이트"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_label.setText(f"진행률: {current}/{total} ({percentage}%)")

    def update_status(self, status):
        """상태 업데이트"""
        self.status_label.setText(f"🎬 {status}")

    def log_message(self, message):
        """로그 메시지 추가"""
        self.log_text.append(f"[{self.get_timestamp()}] {message}")
        # 자동 스크롤을 맨 아래로
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def get_timestamp(self):
        """현재 시간 문자열 반환"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def on_scraping_finished(self, success):
        """스크래핑 완료 처리"""
        if success:
            self.status_label.setText("🎉 스크래핑 완료!")
            self.log_message("🎉 모든 작업이 성공적으로 완료되었습니다!")
            QMessageBox.information(self, "완료", "스크래핑이 성공적으로 완료되었습니다!")
        else:
            self.status_label.setText("❌ 스크래핑 실패")
            self.log_message("❌ 스크래핑이 실패했습니다.")
            QMessageBox.critical(self, "오류", "스크래핑이 실패했습니다. 로그를 확인해주세요.")

        # UI 상태 초기화
        self.scraping_btn.setEnabled(True)
        self.course_entry.setEnabled(True)
        self.connect_btn.setEnabled(True)

        # 워커 쓰레드 정리
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None

    def closeEvent(self, event):
        """윈도우 종료 시 정리"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()


def run_pyside_gui():
    """GUI 실행"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 현대적인 스타일

    window = UdemyScraperGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_pyside_gui()