"""
Udemy 스크래퍼 GUI 인터페이스 (CustomTkinter 버전)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
from pathlib import Path
from config import Config
from app import UdemyScraperApp

class UdemyScraperGUI:
    def __init__(self):
        # CustomTkinter 설정
        ctk.set_appearance_mode("system")  # 시스템 테마 따라감 (dark/light)
        ctk.set_default_color_theme("blue")  # 테마: blue, dark-blue, green

        self.root = ctk.CTk()  # CTk 사용
        self.root.title("🎓 Udemy 강의 대본 스크래퍼")
        self.root.geometry("600x500")  # 조금 더 크게
        self.root.resizable(True, True)
        self.root.minsize(580, 450)

        # 창 중앙 배치
        self.root.center_window_on_screen = True

        # 앱 인스턴스
        self.app = None
        self.auth = None
        self.scraping_thread = None
        self.browser_thread = None

        # 버튼 상태 관리 (중복 클릭 방지)
        self.button_states = {
            'debug_chrome': True,
            'connect': False,
            'start_scraping': False,
            'reset': True
        }

        # 환경변수에서 기본값 로드
        self.default_email = os.getenv('UDEMY_EMAIL', '')
        self.default_password = os.getenv('UDEMY_PASSWORD', '')

        self.setup_ui()

        # 창 활성화 (CustomTkinter 방식)
        self.root.lift()
        self.root.focus()

    def setup_ui(self):
        """UI 구성 요소 설정 (CustomTkinter 버전)"""

        # 메인 프레임 (패딩 추가)
        main_frame = ctk.CTkFrame(self.root, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목
        title_label = ctk.CTkLabel(main_frame, text="🎓 Udemy 강의 대본 스크래퍼",
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))

        # 심플한 안내
        instruction_text = "1) Chrome 디버그모드 시작 → 2) Udemy 로그인 → 3) 브라우저 연결 → 4) 스크래핑 시작"
        instruction_label = ctk.CTkLabel(main_frame, text=instruction_text,
                                        font=ctk.CTkFont(size=12),
                                        text_color="gray60")
        instruction_label.pack(pady=(0, 20))

        # 강의명 입력 프레임
        input_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        input_frame.pack(fill="x", padx=20, pady=10)

        # 강의명 레이블
        course_label = ctk.CTkLabel(input_frame, text="🎬 강의명:",
                                   font=ctk.CTkFont(size=14, weight="bold"))
        course_label.pack(pady=(15, 5))

        # 강의명 입력 필드 (CustomTkinter Entry - 올바른 방법)
        self.course_entry = ctk.CTkEntry(input_frame,
                                        placeholder_text="강의명을 입력하세요",
                                        font=ctk.CTkFont(size=14),
                                        height=40,
                                        corner_radius=8,
                                        border_width=2)
        self.course_entry.pack(fill="x", padx=15, pady=(0, 15))

        # macOS 클립보드 이슈 해결: tkinter의 기본 이벤트 강제 활성화
        self.course_entry.bind("<Command-v>", self._force_paste)
        self.course_entry.bind("<Command-c>", self._force_copy)
        self.course_entry.bind("<Command-x>", self._force_cut)
        self.course_entry.bind("<Command-a>", self._force_select_all)

        # Windows/Linux 호환성
        self.course_entry.bind("<Control-v>", self._force_paste)
        self.course_entry.bind("<Control-c>", self._force_copy)
        self.course_entry.bind("<Control-x>", self._force_cut)
        self.course_entry.bind("<Control-a>", self._force_select_all)

        # 우클릭 메뉴 추가
        self._setup_context_menu(self.course_entry)

        # 헤드리스 모드 항상 False로 설정 (더 이상 사용안함)
        self.headless_var = False

        # 버튼 프레임
        button_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        button_frame.pack(fill="x", padx=20, pady=10)

        # Chrome 디버그 모드 시작 버튼 (큰 버튼)
        self.debug_chrome_button = ctk.CTkButton(button_frame,
                                               text="🌐 Chrome 디버그모드 시작 (Udemy 이동)",
                                               command=self._safe_start_debug_chrome,
                                               font=ctk.CTkFont(size=14, weight="bold"),
                                               height=40,
                                               corner_radius=10,
                                               hover_color="#1565c0")
        self.debug_chrome_button.pack(fill="x", padx=15, pady=(15, 10))

        # 하단 버튼들 (작은 버튼들)
        bottom_buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        bottom_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))

        # 브라우저 연결 버튼
        self.connect_button = ctk.CTkButton(bottom_buttons_frame,
                                          text="1️⃣ 브라우저 연결",
                                          command=self._safe_connect_existing_browser,
                                          font=ctk.CTkFont(size=13),
                                          height=35,
                                          corner_radius=8,
                                          state="disabled")
        self.connect_button.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # 스크래핑 시작 버튼
        self.start_button = ctk.CTkButton(bottom_buttons_frame,
                                        text="2️⃣ 스크래핑 시작",
                                        command=self._safe_start_scraping,
                                        font=ctk.CTkFont(size=13),
                                        height=35,
                                        corner_radius=8,
                                        state="disabled")
        self.start_button.pack(side="left", fill="x", expand=True, padx=5)

        # 초기화 버튼
        self.reset_button = ctk.CTkButton(bottom_buttons_frame,
                                        text="🔄 초기화",
                                        command=self._safe_reset_application,
                                        font=ctk.CTkFont(size=13),
                                        height=35,
                                        width=80,
                                        corner_radius=8,
                                        fg_color="gray40",
                                        hover_color="gray50")
        self.reset_button.pack(side="right", padx=(5, 0))

        # 진행 상황 프레임
        progress_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        progress_frame.pack(fill="x", padx=20, pady=10)

        # 진행 상황 레이블
        progress_label = ctk.CTkLabel(progress_frame, text="📊 진행 상황",
                                     font=ctk.CTkFont(size=14, weight="bold"))
        progress_label.pack(pady=(15, 5))

        # 진행률 바
        self.progress = ctk.CTkProgressBar(progress_frame,
                                          height=20,
                                          corner_radius=10)
        self.progress.pack(fill="x", padx=15, pady=(0, 10))
        self.progress.set(0)

        # 상태 메시지
        self.status_label = ctk.CTkLabel(progress_frame,
                                        text="✅ 준비 완료",
                                        font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 15))

        # 로그 프레임
        log_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 로그 레이블
        log_label = ctk.CTkLabel(log_frame, text="📝 로그",
                                font=ctk.CTkFont(size=14, weight="bold"))
        log_label.pack(pady=(15, 5))

        # 로그 텍스트 (CustomTkinter의 CTkTextbox 사용)
        self.log_text = ctk.CTkTextbox(log_frame,
                                      font=ctk.CTkFont(family="Consolas", size=11),
                                      corner_radius=8,
                                      height=200)
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Enter 키 바인딩
        self.root.bind('<Return>', lambda e: self.start_scraping())

        # 버튼 호버 효과는 activebackground로 처리됨 (제거)

        # 닫기 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_tooltip(self, widget, text):
        """위젯에 툴팁 추가"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#FFFFE0",
                           relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _on_entry_click(self, event):
        """Entry 클릭 이벤트 처리"""
        self.course_entry.focus_force()
        return "break"

    def _on_entry_focus(self, event):
        """Entry 포커스 이벤트 처리"""
        # 전체 텍스트 선택 (선택사항)
        self.course_entry.selection_range(0, tk.END)

    def _on_paste(self, event):
        """붙여넣기 이벤트 처리"""
        try:
            widget = event.widget
            clipboard = widget.clipboard_get()
            # 현재 선택된 텍스트 삭제
            if widget.selection_present():
                widget.delete("sel.first", "sel.last")
            widget.insert(tk.INSERT, clipboard)
        except Exception as e:
            self.log_message(f'⚠️ 붙여넣기 실패: {e}')
        return 'break'

    def log_message(self, message: str):
        """로그 메시지 추가 - UI + 콘솔 동시 출력"""
        import time

        # 콘솔에도 출력 (즉시 확인 가능)
        print(f"[UDEMY] {message}")

        # UI 로그 텍스트에도 추가
        try:
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            # update_idletasks 대신 더 가벼운 update 사용
            if not hasattr(self, '_last_update_time'):
                self._last_update_time = 0
            if time.time() - self._last_update_time > 0.1:  # 100ms 간격으로 제한
                self._last_update_time = time.time()
                self.root.update()
        except Exception as e:
            # UI 업데이트 실패해도 콘솔엔 출력됨
            print(f"[UDEMY] ⚠️ UI 로그 업데이트 실패: {e}")

    def update_status(self, status: str):
        """상태 메시지 업데이트 - UI + 콘솔 동시 출력"""
        # 콘솔에도 상태 출력
        print(f"[UDEMY STATUS] {status}")

        # UI 상태 라벨 업데이트
        try:
            self.status_label.configure(text=f"📍 {status}")
            # 더 가벼운 업데이트
            self.root.update()
        except Exception as e:
            print(f"[UDEMY] ⚠️ 상태 UI 업데이트 실패: {e}")

    def update_progress(self, current: int, total: int):
        """진행률 업데이트 - UI + 콘솔 동시 출력"""
        if total > 0:
            percentage = current / total  # CustomTkinter는 0-1 범위
            percentage_display = percentage * 100

            # 콘솔에 진행률 출력
            print(f"[UDEMY PROGRESS] {current}/{total} ({percentage_display:.1f}%)")

            try:
                self.progress.set(percentage)
                # 더 가벼운 업데이트
                self.root.update()
            except Exception as e:
                print(f"[UDEMY] ⚠️ 진행률 UI 업데이트 실패: {e}")

    def start_debug_chrome(self):
        """디버그 모드로 Chrome 시작하고 Udemy로 이동"""
        try:
            self.log_message("🌐 Chrome 디버그 모드 시작...")
            self.update_status("Chrome 디버그 모드 시작 중...")

            # 기존 Chrome 프로세스들 종료 확인
            from browser.manager import ExistingBrowserManager

            self.browser_manager = ExistingBrowserManager(log_callback=self.log_message)

            # Chrome 디버그 모드로 시작
            if self.browser_manager.start_chrome_with_debug_port():
                self.log_message("✅ Chrome이 디버그 모드로 시작되었습니다!")
                self.log_message("📌 다음 단계를 따라하세요:")
                self.log_message("   1. Chrome에서 Udemy 로그인")
                self.log_message("   2. '1️⃣ 브라우저 연결' 버튼 클릭")
                self.log_message("   3. 자동으로 내 학습 페이지로 이동됩니다")
                self.update_status("Chrome 디버그 모드 시작 완료")

                # 연결 버튼 활성화
                self.button_states['connect'] = True
                self.button_states['debug_chrome'] = True  # 다시 활성화
                self._update_button_states()
            else:
                self.log_message("❌ Chrome 디버그 모드 시작 실패")
                self.update_status("Chrome 시작 실패")
                # 실패 시 버튼 다시 활성화
                self.button_states['debug_chrome'] = True
                self._update_button_states()

        except Exception as e:
            self.log_message(f"❌ Chrome 시작 중 오류: {str(e)}")
            self.update_status("오류 발생")
            # 오류 시 버튼 다시 활성화
            self.button_states['debug_chrome'] = True
            self._update_button_states()

    def connect_existing_browser(self):
        """기존 Chrome 브라우저에 연결"""
        try:
            self.log_message("🔗 기존 Chrome 브라우저 연결 시도...")
            self.update_status("기존 브라우저 연결 중...")

            # 기존 브라우저 연결 스레드 시작
            self.connect_thread = threading.Thread(
                target=self._connect_existing_workflow,
                daemon=True
            )
            self.connect_thread.start()

        except Exception as e:
            self.log_message(f"❌ 브라우저 연결 실패: {str(e)}")
            messagebox.showerror("오류", f"브라우저 연결 실패:\n{str(e)}")

    def _connect_existing_workflow(self):
        """기존 브라우저 연결 및 자동 내 학습 이동 워크플로우"""
        try:
            from browser.manager import ExistingBrowserManager
            from browser.course_finder import CourseFinder

            # 기존 브라우저 매니저 생성
            browser_manager = ExistingBrowserManager(log_callback=self.log_message)

            # 기존 브라우저에 연결 시도
            if not browser_manager.connect_to_existing_browser():
                # 연결 실패 - Chrome 디버그 모드 안내
                self.log_message("❌ 기존 브라우저 연결 실패")
                self.log_message("")
                self.log_message("📋 Chrome을 디버그 모드로 시작하는 방법:")
                self.log_message("1. '🌐 Chrome 디버그모드 시작' 버튼 클릭")
                self.log_message("2. 또는 터미널에서 다음 명령어 실행:")
                self.log_message('/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug')
                self.log_message("3. Chrome이 열리면 Udemy 로그인")
                self.log_message("4. '브라우저 연결' 버튼 다시 클릭")
                self.log_message("")
                self.update_status("Chrome 디버그 모드로 시작 필요")
                # 실패 시 버튼 다시 활성화
                self.button_states['connect'] = True
                self._update_button_states()
                return

            # 연결 성공
            self.auth = browser_manager
            self.log_message("✅ 기존 브라우저 연결 성공!")

            # CourseFinder로 로그인 상태 확인 및 내 학습 이동
            course_finder = CourseFinder(browser_manager.driver, browser_manager.wait, self.log_message)

            # 로그인 상태 확인하고 내 학습으로 이동
            if course_finder.go_to_my_learning():
                self.log_message("✅ 내 학습 페이지 준비 완료!")

                # 강의명이 입력되어 있으면 자동으로 스크래핑 시작
                course_name = self.course_entry.get().strip()
                if course_name:
                    self.log_message(f"🚀 강의명 입력됨: '{course_name}' - 자동 스크래핑 시작!")
                    self.connect_button.configure(text="✅ 연결됨")
                    self.button_states['connect'] = True
                    # 스크래핑 버튼 비활성화 (자동 진행)
                    self.button_states['start_scraping'] = False
                    self._update_button_states()
                    self.update_status("자동 스크래핑 진행 중...")

                    # 스크래핑 자동 시작 (별도 스레드)
                    self._start_auto_scraping(course_name)
                else:
                    self.log_message("📌 강의명을 입력하고 스크래핑을 시작하세요")
                    # 스크래핑 버튼 활성화
                    self.button_states['start_scraping'] = True
                    self.button_states['connect'] = True
                    self.connect_button.configure(text="✅ 연결됨")
                    self._update_button_states()
                    self.update_status("내 학습 페이지 준비 완료")

                    # 강의명 입력 필드에 포커스
                    self.course_entry.focus()

            else:
                self.log_message("❌ 로그인 상태가 아니거나 내 학습 이동 실패")
                self.log_message("💡 브라우저에서 수동으로 Udemy 로그인 후:")
                self.log_message("   1. 내 학습 페이지로 이동")
                self.log_message("   2. '초기화' 후 다시 '브라우저 연결' 시도")
                self.update_status("로그인 필요")
                # 실패 시 버튼 다시 활성화
                self.button_states['connect'] = True
                self._update_button_states()

        except Exception as e:
            self.log_message(f"❌ 연결 워크플로우 오류: {str(e)}")
            self.update_status("오류 발생")
            # 오류 시 버튼 다시 활성화
            self.button_states['connect'] = True
            self._update_button_states()

    def _start_auto_scraping(self, course_name: str):
        """자동 스크래핑 시작 (별도 스레드)"""
        try:
            self.log_message("🤖 자동 스크래핑 모드 시작...")

            # 스크래핑 스레드 시작
            self.scraping_thread = threading.Thread(
                target=self._auto_scraping_workflow,
                args=(course_name,),
                daemon=True
            )
            self.scraping_thread.start()

        except Exception as e:
            self.log_message(f"❌ 자동 스크래핑 시작 실패: {str(e)}")
            # 실패 시 버튼 다시 활성화
            self.button_states['start_scraping'] = True
            self._update_button_states()

    def _auto_scraping_workflow(self, course_name: str):
        """자동 스크래핑 워크플로우 (스레드 내에서 실행)"""
        try:
            self.log_message("🚀 새로운 통합 스크래핑 워크플로우 시작!")
            self.update_status("스크래핑 준비 중...")

            from browser.navigation import UdemyNavigator
            from core.models import Course

            # 네비게이터 생성 (기존 브라우저 사용)
            navigator = UdemyNavigator(
                driver=self.auth.driver,
                wait=self.auth.wait,
                log_callback=self.log_message
            )

            # 1. 강의 검색 및 선택
            self.log_message(f"🔍 강의 검색: '{course_name}'")
            course = navigator.search_and_select_course(course_name)
            if not course:
                self.log_message("❌ 강의를 찾을 수 없습니다.")
                self.update_status("강의 검색 실패")
                return

            self.log_message(f"✅ 강의 선택: {course.title}")

            # 2. 커리큘럼 분석
            self.log_message("📋 커리큘럼 분석 중...")
            self.update_status("커리큘럼 분석 중...")
            if not navigator.analyze_curriculum(course):
                self.log_message("❌ 커리큘럼 분석 실패")
                self.update_status("커리큘럼 분석 실패")
                return

            # 3. 스크래핑 진행
            self.log_message("📝 스크립트 추출 시작...")
            self.update_status("스크립트 추출 중...")
            success = navigator.start_complete_scraping_workflow(course)

            if success:
                self.log_message("🎉 자동 스크래핑 완료!")
                self.update_status("스크래핑 완료")
            else:
                self.log_message("❌ 스크래핑 중 오류 발생")
                self.update_status("스크래핑 실패")

        except Exception as e:
            self.log_message(f"❌ 자동 스크래핑 실패: {str(e)}")
            self.update_status("자동 스크래핑 실패")
        finally:
            # 완료 시 버튼 다시 활성화
            self.button_states['start_scraping'] = True
            self._update_button_states()

    def start_scraping(self):
        """스크래핑 시작"""
        if self.scraping_thread and self.scraping_thread.is_alive():
            messagebox.showwarning("경고", "이미 스크래핑이 진행 중입니다.")
            return

        # 입력값 검증 (강의명만)
        course_name = self.course_entry.get().strip()

        if not course_name:
            messagebox.showerror("오류", "강의명을 입력해주세요.")
            return

        # 브라우저가 열려있는지 확인
        if not hasattr(self, 'auth') or not self.auth or not self.auth.driver:
            messagebox.showerror("오류", "먼저 브라우저를 열고 로그인해주세요.")
            return

        # UI 상태 변경
        self.start_button.configure(state="disabled", text="⏳ 진행 중...")
        self.log_text.delete("1.0", "end")
        self.progress.set(0)

        # Config 업데이트 (헤드리스 모드는 항상 False)
        Config.HEADLESS_MODE = False

        # 스크래핑 스레드 시작 (기존 브라우저 사용)
        self.scraping_thread = threading.Thread(
            target=self.run_scraping_workflow_with_browser,
            args=(course_name,),
            daemon=True
        )
        self.scraping_thread.start()

    def run_scraping_workflow_with_browser(self, course_name: str):
        """기존 브라우저를 사용하여 스크래핑 워크플로우 실행 (새로운 통합 워크플로우)"""
        try:
            self.log_message("🚀 새로운 통합 스크래핑 워크플로우 시작!")
            self.update_status("스크래핑 준비 중...")

            from browser.navigation import UdemyNavigator
            from core.models import Course

            # 네비게이터 생성 (기존 브라우저 사용)
            navigator = UdemyNavigator(
                driver=self.auth.driver,
                wait=self.auth.wait,
                log_callback=self.log_message
            )

            # 현재 페이지 확인
            current_url = self.auth.driver.current_url
            self.log_message(f"🔍 현재 페이지: {current_url}")

            # '내 학습' 페이지로 이동
            if 'my-courses' not in current_url and 'home/my-courses' not in current_url:
                self.log_message("📚 '내 학습' 페이지로 이동 중...")
                if not navigator.go_to_my_learning():
                    self.log_message("⚠️ '내 학습' 페이지로 이동할 수 없습니다. 수동으로 이동해주세요.")
                    self.update_status("내 학습 페이지로 이동 필요")

            # 강의 검색 및 선택
            self.log_message(f"🔍 강의 검색 중: {course_name}")
            self.update_status("강의 검색 중...")

            course = navigator.search_and_select_course(course_name)
            if not course:
                self.log_message(f"❌ 강의를 찾을 수 없습니다: {course_name}")
                self.update_status("강의 찾기 실패")
                return

            self.log_message(f"✅ 강의 발견: {course.title}")
            self.update_status("강의 분석 및 스크래핑 시작...")

            # 🚀 새로운 통합 워크플로우 실행!
            # 이 메서드가 모든 것을 처리합니다:
            # - 커리큘럼 분석
            # - 섹션별 아코디언 열기
            # - 비디오 강의 클릭
            # - 자막 패널 열기/닫기
            # - 자막 내용 추출 및 저장
            if navigator.start_complete_scraping_workflow(course):
                self.log_message("🎉 모든 스크래핑 작업이 완료되었습니다!")
                self.update_status("완료")

                from config import Config
                output_dir = Config.get_output_directory()
                messagebox.showinfo("완료", f"강의 대본이 성공적으로 추출되었습니다!\n저장 위치: {output_dir}")
            else:
                self.log_message("❌ 스크래핑 워크플로우 실패")
                self.update_status("스크래핑 실패")
                messagebox.showerror("오류", "스크래핑 과정에서 문제가 발생했습니다. 로그를 확인해주세요.")

        except Exception as e:
            self.log_message(f"❌ 오류 발생: {str(e)}")
            self.update_status("오류 발생")
            import traceback
            self.log_message(f"🔍 상세 오류: {traceback.format_exc()}")
            messagebox.showerror("오류", f"예상치 못한 오류가 발생했습니다:\n{str(e)}")
        finally:
            # UI 상태 복원
            self.start_button.configure(state="normal", text="2️⃣ 스크래핑 시작")

    def reset_application(self):
        """애플리케이션 상태 초기화"""
        try:
            self.log_message("🔄 초기화 중...")

            # 진행 중인 스레드 중단
            if hasattr(self, 'scraping_thread') and self.scraping_thread and self.scraping_thread.is_alive():
                self.log_message("⚠️ 진행 중인 작업 중단...")
                # 스레드는 직접 중단할 수 없으므로 플래그 설정 (필요시)

            # 브라우저 연결 해제
            if hasattr(self, 'auth') and self.auth:
                try:
                    self.auth.cleanup()
                    self.log_message("🔗 브라우저 연결 해제")
                except:
                    pass
                self.auth = None

            # UI 상태 초기화
            self.course_entry.delete(0, "end")  # 입력 필드 초기화
            self.course_entry.focus()  # 포커스 설정

            # 버튼 상태 초기화
            self.connect_button.configure(
                state="normal",
                text="1️⃣ 브라우저 연결"
            )
            self.start_button.configure(
                state="disabled",
                text="2️⃣ 스크래핑 시작"
            )

            # 진행률 초기화
            self.progress.set(0)
            self.update_status("초기화 완료")

            # 로그 초기화
            self.log_text.delete("1.0", "end")
            self.log_message("✅ 초기화 완료 - 다시 시작할 수 있습니다")

        except Exception as e:
            self.log_message(f"❌ 초기화 중 오류: {str(e)}")
            messagebox.showerror("오류", f"초기화 실패:\n{str(e)}")

    def on_closing(self):
        """창 닫기 이벤트 처리"""
        if self.scraping_thread and self.scraping_thread.is_alive():
            if messagebox.askokcancel("종료", "스크래핑이 진행 중입니다. 정말 종료하시겠습니까?"):
                if self.auth:
                    self.auth.cleanup()
                self.root.destroy()
        else:
            if self.auth:
                self.auth.cleanup()
            self.root.destroy()

    # ==================== 안전한 버튼 래퍼 함수들 (중복 클릭 방지) ====================

    def _safe_button_wrapper(self, button_key, original_func, *args, **kwargs):
        """버튼 클릭 안전 래퍼 - 중복 클릭 방지"""
        try:
            # 버튼이 이미 비활성 상태면 무시
            if not self.button_states.get(button_key, False):
                self.log_message(f"⚠️ {button_key} 버튼이 비활성화 상태입니다")
                return

            # 버튼 즉시 비활성화
            self.button_states[button_key] = False
            self._update_button_states()

            # 원본 함수 실행
            original_func(*args, **kwargs)

        except Exception as e:
            self.log_message(f"❌ {button_key} 실행 중 오류: {str(e)}")
            # 오류 시 버튼 다시 활성화
            self.button_states[button_key] = True
            self._update_button_states()

    def _update_button_states(self):
        """버튼 상태 UI 업데이트 (CustomTkinter용)"""
        try:
            # macOS CustomTkinter 버그 우회: configure 대신 직접 상태 관리
            if self.button_states['debug_chrome']:
                self.debug_chrome_button.configure(state="normal")
            else:
                self.debug_chrome_button.configure(state="disabled")

            if self.button_states['connect']:
                self.connect_button.configure(state="normal")
            else:
                self.connect_button.configure(state="disabled")

            if self.button_states['start_scraping']:
                self.start_button.configure(state="normal")
            else:
                self.start_button.configure(state="disabled")

            if self.button_states['reset']:
                self.reset_button.configure(state="normal")
            else:
                self.reset_button.configure(state="disabled")

            # UI 강제 업데이트 (macOS 버그 우회)
            self.root.update_idletasks()

        except Exception as e:
            self.log_message(f"⚠️ 버튼 상태 업데이트 실패: {str(e)}")

    def _safe_start_debug_chrome(self):
        """Chrome 디버그 시작 안전 래퍼"""
        self._safe_button_wrapper('debug_chrome', self.start_debug_chrome)

    def _safe_connect_existing_browser(self):
        """브라우저 연결 안전 래퍼"""
        self._safe_button_wrapper('connect', self.connect_existing_browser)

    def _safe_start_scraping(self):
        """스크래핑 시작 안전 래퍼"""
        self._safe_button_wrapper('start_scraping', self.start_scraping)

    def _safe_reset_application(self):
        """초기화 안전 래퍼"""
        self._safe_button_wrapper('reset', self.reset_application)

    def _force_paste(self, event):
        """강제 붙여넣기 (macOS 클립보드 버그 해결)"""
        try:
            # 시스템 클립보드에서 직접 가져오기
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                # 현재 선택영역 삭제
                try:
                    start = self.course_entry.index("sel.first")
                    end = self.course_entry.index("sel.last")
                    self.course_entry.delete(start, end)
                except:
                    pass
                # 현재 커서 위치에 삽입
                cursor_pos = self.course_entry.index("insert")
                self.course_entry.insert(cursor_pos, clipboard_text)
                self.log_message(f"✅ 텍스트 붙여넣기: {clipboard_text[:50]}...")
        except Exception as e:
            self.log_message(f"⚠️ 붙여넣기 실패: {str(e)}")
        return "break"

    def _force_copy(self, event):
        """강제 복사"""
        try:
            selected_text = self.course_entry.selection_get()
            if selected_text:
                # 클립보드 초기화 후 새 텍스트 추가
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                # 클립보드 업데이트 강제 적용 (macOS 버그)
                self.root.update()
                self.log_message(f"✅ 텍스트 복사: {selected_text[:50]}...")
        except Exception as e:
            self.log_message(f"⚠️ 복사 실패: {str(e)}")
        return "break"

    def _force_cut(self, event):
        """강제 잘라내기"""
        try:
            selected_text = self.course_entry.selection_get()
            if selected_text:
                # 클립보드에 복사
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.root.update()
                # 선택영역 삭제
                start = self.course_entry.index("sel.first")
                end = self.course_entry.index("sel.last")
                self.course_entry.delete(start, end)
                self.log_message(f"✅ 텍스트 잘라내기: {selected_text[:50]}...")
        except Exception as e:
            self.log_message(f"⚠️ 잘라내기 실패: {str(e)}")
        return "break"

    def _force_select_all(self, event):
        """전체 선택"""
        try:
            self.course_entry.select_range(0, "end")
            self.course_entry.icursor("end")
        except Exception as e:
            self.log_message(f"⚠️ 전체 선택 실패: {str(e)}")
        return "break"

    def _setup_context_menu(self, entry_widget):
        """우클릭 컨텍스트 메뉴 설정"""
        def show_context_menu(event):
            try:
                context_menu = tk.Menu(self.root, tearoff=0)
                context_menu.add_command(label="잘라내기 ⌘X", command=lambda: self._force_cut(None))
                context_menu.add_command(label="복사 ⌘C", command=lambda: self._force_copy(None))
                context_menu.add_command(label="붙여넣기 ⌘V", command=lambda: self._force_paste(None))
                context_menu.add_separator()
                context_menu.add_command(label="전체 선택 ⌘A", command=lambda: self._force_select_all(None))

                context_menu.post(event.x_root, event.y_root)
            except Exception as e:
                print(f"⚠️ 컨텍스트 메뉴 오류: {str(e)}")

        entry_widget.bind("<Button-2>", show_context_menu)  # 우클릭 (macOS)
        entry_widget.bind("<Control-Button-1>", show_context_menu)  # Ctrl+클릭 (macOS)

    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 함수"""
    # 필요한 디렉토리 생성
    Config.ensure_directories()

    # GUI 실행
    gui = UdemyScraperGUI()
    gui.run()

if __name__ == "__main__":
    main()