"""
Udemy 페이지 탐색 및 강의 선택 모듈 (통합 관리자)
"""

from .course_finder import CourseFinder
from .curriculum_analyzer import CurriculumAnalyzer
from .transcript_scraper import TranscriptScraper
from core.models import Course
from typing import Optional


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