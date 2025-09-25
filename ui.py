"""
Udemy 스크래퍼 GUI 인터페이스
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
from pathlib import Path
from config import Config
from app import UdemyScraperApp

class UdemyScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Udemy 강의 대본 스크래퍼")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        self.root.minsize(480, 350)

        # macOS에서 포커스 문제 해결
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

        # 앱 인스턴스
        self.app = None
        self.auth = None
        self.scraping_thread = None
        self.browser_thread = None

        # 환경변수에서 기본값 로드
        self.default_email = os.getenv('UDEMY_EMAIL', '')
        self.default_password = os.getenv('UDEMY_PASSWORD', '')

        self.setup_ui()

        # 창 활성화
        self.root.focus_force()

    def setup_ui(self):
        """UI 구성 요소 설정"""

        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 제목
        title_label = ttk.Label(main_frame, text="Udemy 강의 대본 스크래퍼",
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # 심플한 안내
        instruction_text = "1) Chrome 디버그모드 시작 → 2) Udemy 로그인 → 3) 브라우저 연결 → 4) 스크래핑 시작"
        instruction_label = ttk.Label(main_frame, text=instruction_text,
                                     foreground="gray", font=("Arial", 9))
        instruction_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # 구분선 제거 - 심플하게

        # 강의명 입력 - ttk.Entry로 다시 변경하고 이벤트 처리 개선
        course_frame = ttk.Frame(main_frame)
        course_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        course_frame.columnconfigure(1, weight=1)

        ttk.Label(course_frame, text="강의명:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        # 심플한 스타일
        style = ttk.Style()
        style.theme_use('clam')  # 깔끔한 테마

        # 기본 폰트 설정
        style.configure('TButton', font=('Arial', 10))
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TEntry', font=('Arial', 10), padding=5)

        self.course_var = tk.StringVar()
        self.course_entry = ttk.Entry(course_frame,
                                     textvariable=self.course_var,
                                     font=("Arial", 10),
                                     width=40)
        self.course_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        self.course_entry.focus_set()

        # 다양한 클릭 이벤트 바인딩
        self.course_entry.bind("<Button-1>", self._on_entry_click)
        self.course_entry.bind("<FocusIn>", self._on_entry_focus)
        self.course_entry.bind('<Command-v>', self._on_paste)  # Mac
        self.course_entry.bind('<Control-v>', self._on_paste)  # Windows/Linux

        # 헤드리스 모드 항상 False로 설정
        self.headless_var = tk.BooleanVar(value=False)

        # 버튼들
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=0)  # 초기화 버튼용

        # 첫 번째 행: Chrome 디버그 모드 시작 버튼
        self.debug_chrome_button = ttk.Button(button_frame,
                                             text="🌐 Chrome 디버그모드 시작 (Udemy 이동)",
                                             command=self.start_debug_chrome)
        self.debug_chrome_button.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 5), pady=(0, 5))

        # 두 번째 행: 기존 버튼들
        self.connect_button = ttk.Button(button_frame,
                                        text="1. 브라우저 연결",
                                        command=self.connect_existing_browser)
        self.connect_button.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)

        self.start_button = ttk.Button(button_frame,
                                      text="2. 스크래핑 시작",
                                      command=self.start_scraping,
                                      state='disabled')
        self.start_button.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)

        self.reset_button = ttk.Button(button_frame,
                                      text="초기화",
                                      command=self.reset_application,
                                      width=8)
        self.reset_button.grid(row=1, column=2, padx=(5, 0), pady=5)

        # 툴팁 제거 - 심플하게

        # 진행 상황 표시
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="5")
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        # 진행률 바
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)

        # 상태 메시지
        self.status_var = tk.StringVar(value="준비 완료")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, font=("Arial", 9))
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=2)

        # 로그 창 - 높이 증가
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=60, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 그리드 가중치 설정
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)  # 로그 프레임이 확장되도록
        progress_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

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
        """로그 메시지 추가 - 성능 개선"""
        import time
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        # update_idletasks 대신 더 가벼운 update 사용
        if not hasattr(self, '_last_update_time'):
            self._last_update_time = 0
        if time.time() - self._last_update_time > 0.1:  # 100ms 간격으로 제한
            self._last_update_time = time.time()
            self.root.update()

    def update_status(self, status: str):
        """상태 메시지 업데이트 - 성능 개선"""
        self.status_var.set(status)
        # 더 가벼운 업데이트
        self.root.update()

    def update_progress(self, current: int, total: int):
        """진행률 업데이트 - 성능 개선"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress['value'] = percentage
            # 더 가벼운 업데이트
            self.root.update()

    def start_debug_chrome(self):
        """디버그 모드로 Chrome 시작하고 Udemy로 이동"""
        try:
            self.log_message("🌐 Chrome 디버그 모드 시작...")
            self.update_status("Chrome 디버그 모드 시작 중...")

            # 기존 Chrome 프로세스들 종료 확인
            from existing_browser import ExistingBrowserManager

            self.browser_manager = ExistingBrowserManager(log_callback=self.log_message)

            # Chrome 디버그 모드로 시작
            if self.browser_manager.start_chrome_with_debug_port():
                self.log_message("✅ Chrome이 디버그 모드로 시작되었습니다!")
                self.log_message("📌 Chrome에서 Udemy 로그인 후 '1. 브라우저 연결' 버튼을 눌러주세요")
                self.update_status("Chrome 디버그 모드 시작 완료")

                # 연결 버튼 활성화
                self.connect_button.config(state='normal')
            else:
                self.log_message("❌ Chrome 디버그 모드 시작 실패")
                self.update_status("Chrome 시작 실패")

        except Exception as e:
            self.log_message(f"❌ Chrome 시작 중 오류: {str(e)}")
            self.update_status("오류 발생")

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
        """기존 브라우저 연결 워크플로우"""
        try:
            from existing_browser import ExistingBrowserManager

            # 기존 브라우저 매니저 생성
            browser_manager = ExistingBrowserManager(log_callback=self.log_message)

            # 기존 브라우저에 연결 시도
            if browser_manager.connect_to_existing_browser():
                # 연결 성공
                self.auth = browser_manager  # auth 객체로 설정
                self.log_message("✅ 기존 브라우저 연결 성공!")
                self.log_message("📌 Udemy '내 학습' 페이지에서 스크래핑을 시작하세요")

                # 스크래핑 버튼 활성화
                self.start_button.config(state='normal')
                self.connect_button.config(state='disabled', text="✅ 연결됨")
                self.update_status("기존 브라우저 연결 완료")

            else:
                # 연결 실패 - 사용자에게 Chrome 디버그 모드 안내
                self.log_message("❌ 기존 브라우저 연결 실패")
                self.log_message("")
                self.log_message("📋 Chrome을 디버그 모드로 시작하는 방법:")
                self.log_message("1. 터미널을 열어주세요")
                self.log_message("2. 다음 명령어를 입력하세요:")
                self.log_message('/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug')
                self.log_message("3. Chrome이 열리면 Udemy 로그인 후 '내 학습'으로 이동")
                self.log_message("4. '초기화' 버튼을 누르고 다시 연결 시도")
                self.log_message("")
                self.update_status("Chrome 디버그 모드로 시작 필요")

        except Exception as e:
            self.log_message(f"❌ 연결 워크플로우 오류: {str(e)}")
            self.update_status("오류 발생")



    def start_scraping(self):
        """스크래핑 시작"""
        if self.scraping_thread and self.scraping_thread.is_alive():
            messagebox.showwarning("경고", "이미 스크래핑이 진행 중입니다.")
            return

        # 입력값 검증 (강의명만)
        course_name = self.course_var.get().strip()

        if not course_name:
            messagebox.showerror("오류", "강의명을 입력해주세요.")
            return

        # 브라우저가 열려있는지 확인
        if not hasattr(self, 'auth') or not self.auth or not self.auth.driver:
            messagebox.showerror("오류", "먼저 브라우저를 열고 로그인해주세요.")
            return

        # UI 상태 변경
        self.start_button.config(state='disabled', text="진행 중...")
        self.log_text.delete(1.0, tk.END)
        self.progress['value'] = 0

        # Config 업데이트
        Config.HEADLESS_MODE = self.headless_var.get()

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

            from navigation import UdemyNavigator
            from models import Course

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
            self.start_button.config(state='normal', text="2. 스크래핑 시작")

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
            self.course_var.set("")  # 입력 필드 초기화
            self.course_entry.focus_set()  # 포커스 설정

            # 버튼 상태 초기화
            self.connect_button.config(
                state='normal',
                text="1. 기존 브라우저 연결"
            )
            self.start_button.config(
                state='disabled',
                text="2. 스크래핑 시작"
            )

            # 진행률 초기화
            self.progress['value'] = 0
            self.update_status("초기화 완료")

            # 로그 초기화
            self.log_text.delete(1.0, tk.END)
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