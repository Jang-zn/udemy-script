"""
Udemy 페이지 탐색 및 강의 선택 모듈 (통합 관리자)
"""

from .course_finder import CourseFinder
from .curriculum_analyzer import CurriculumAnalyzer
from .transcript_scraper import TranscriptScraper
from core.models import Course
from typing import Optional
from selenium.webdriver.common.by import By
import time


class UdemyNavigator:
    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print

        # 하위 모듈들 초기화
        self.course_finder = CourseFinder(driver, wait, log_callback)
        self.curriculum_analyzer = CurriculumAnalyzer(driver, wait, log_callback)
        self.transcript_scraper = TranscriptScraper(driver, wait, log_callback)

    def go_to_my_learning(self) -> bool:
        """'내 학습' 버튼 클릭해서 My Learning 페이지로 이동"""
        return self.course_finder.go_to_my_learning()

    def search_and_select_course(self, course_name: str) -> Optional[Course]:
        """강의 검색 및 선택"""
        return self.course_finder.search_and_select_course(course_name)

    def analyze_curriculum(self, course: Course) -> bool:
        """강의 커리큘럼 분석"""
        return self.curriculum_analyzer.analyze_curriculum(course)

    def start_complete_scraping_workflow(self, course: Course) -> bool:
        """전체 스크래핑 워크플로우 시작"""
        return self.transcript_scraper.start_complete_scraping_workflow(course)

    def _ensure_normal_body_state_and_check_sections(self) -> bool:
        """상태 체크하고 섹션 영역이 제대로 보이는지 확인"""
        try:
            self.log_callback("     🔍 트랜스크립트 패널 상태 확인 중...")

            # 1. 트랜스크립트 버튼 찾기
            transcript_button = self._find_transcript_button()
            if not transcript_button:
                self.log_callback("     ⚠️ 트랜스크립트 버튼을 찾을 수 없음 - 정상 상태로 가정")
                return False

            # 2. 현재 패널 상태 확인 (aria-expanded="true"면 열린 상태)
            is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
            self.log_callback(f"     📊 트랜스크립트 패널 상태: {'열림(script body)' if is_expanded else '닫힘(normal body)'}")

            # 3. 패널이 열려있다면 닫기 (섹션 영역이 보이도록)
            if is_expanded:
                self.log_callback("     🔄 섹션 영역 표시를 위해 트랜스크립트 패널을 닫는 중...")

                # 동영상 영역에 마우스 hover (컨트롤바 표시를 위해)
                video_area = self._find_video_area()
                if video_area:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(video_area).perform()
                    time.sleep(1)

                try:
                    transcript_button.click()
                    time.sleep(2)  # 패널 닫히는 시간 대기
                    self.log_callback("     ✅ 트랜스크립트 패널 닫기 완료 → 섹션 영역 표시")
                    return True  # 상태 변경됨
                except Exception as e:
                    self.log_callback(f"     ❌ 패널 닫기 실패: {str(e)}")
                    try:
                        # JavaScript로 클릭 시도
                        self.driver.execute_script("arguments[0].click();", transcript_button)
                        time.sleep(2)
                        self.log_callback("     ✅ JavaScript로 패널 닫기 완료 → 섹션 영역 표시")
                        return True
                    except Exception as e2:
                        self.log_callback(f"     ❌ JavaScript 클릭도 실패: {str(e2)}")
                        return False
            else:
                self.log_callback("     ✅ 이미 normal body 상태 - 섹션 영역이 표시되어 있음")
                return False  # 상태 변경 없음

        except Exception as e:
            self.log_callback(f"     ❌ 상태 확인 중 오류: {str(e)}")
            return False

    def _find_transcript_button(self):
        """트랜스크립트 버튼 찾기 (호버 상태 유지)"""
        try:
            import time
            # 페이지 로딩 대기 (3초로 단축)
            time.sleep(1)

            # 비디오 영역 찾기
            video_area = self._find_video_area()
            if not video_area:
                return None

            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)

            # 비디오 영역에 마우스 이동하고 호버 상태 유지
            actions.move_to_element(video_area).perform()
            time.sleep(0.5)  # 컨트롤바가 나타날 때까지 대기

            # 호버 상태를 유지하면서 버튼 찾기
            transcript_selectors = [
                "button[data-purpose='transcript-toggle']",
                "button[aria-label*='트랜스크립트']",
                "button[aria-label*='Transcript']",
                "button[aria-label*='transcript']",
                "button[aria-label*='대본']",
                "button[aria-label*='자막']",
                "button[aria-label*='Subtitles']",
                ".transcript-toggle"
            ]

            # 여러 번 시도 (컨트롤바가 안정화될 때까지)
            for attempt in range(3):
                # 호버 상태 재설정
                actions.move_to_element(video_area).perform()
                time.sleep(0.3)

                for selector in transcript_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element and element.is_displayed():
                            # 버튼을 찾았지만 호버 상태 유지
                            actions.move_to_element(element).perform()
                            return element
                    except:
                        continue

            return None

        except Exception:
            return None

    def _find_video_area(self):
        """비디오 영역 찾기"""
        try:
            video_selectors = [
                "video",
                ".video-player",
                "[data-purpose='video-player']",
                ".vjs-tech",
                ".player-container"
            ]

            for selector in video_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        return element
                except:
                    continue

            return None

        except Exception:
            return None