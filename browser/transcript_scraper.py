"""
Udemy 강의 자막/스크립트 추출 모듈 (리팩토링된 버전)
"""

import time
import os
from typing import Optional, List
from selenium.webdriver.common.by import By
from config import Config
from core.models import Course, Section, Lecture
from utils.file_utils import ensure_directory, sanitize_filename
from .base import BrowserBase
from .element_finder import ElementFinder, ClickHandler, SectionNavigator
from .transcript_extractor import TranscriptExtractor, VideoNavigator
from .selectors import UdemySelectors


class TranscriptScraper(BrowserBase):
    """강의 자막 추출 메인 클래스 (리팩토링된 버전)"""

    def __init__(self, driver, wait, log_callback=None):
        super().__init__(driver, wait, log_callback)
        self.current_course = None

        # 헬퍼 클래스들 초기화
        self.element_finder = ElementFinder(driver, wait, log_callback)
        self.click_handler = ClickHandler(driver, log_callback)
        self.section_navigator = SectionNavigator(driver, wait, log_callback)
        self.transcript_extractor = TranscriptExtractor(driver, wait, log_callback)
        self.video_navigator = VideoNavigator(driver, wait, log_callback)

    def start_complete_scraping_workflow(self, course: Course) -> bool:
        """전체 스크래핑 워크플로우 시작"""
        try:
            self.current_course = course
            self.log_callback("🚀 전체 스크래핑 워크플로우 시작...")
            self.log_callback(f"📚 대상 강의: {course.title}")
            self.log_callback(f"📊 총 {len(course.sections)}개 섹션, {course.total_lectures}개 강의")

            # 처음 상태 확인 및 정리
            if self._ensure_normal_body_state():
                self.log_callback("✅ 초기 상태 확인 완료")

            # 커리큘럼 재분석 (필요시)
            if not course.sections or course.total_lectures == 0:
                self.log_callback("🔄 커리큘럼 재분석 필요...")
                if not self._reanalyze_curriculum(course):
                    self.log_callback("❌ 커리큘럼 재분석 실패")
                    return False

            # 모든 섹션 처리
            success_count = 0
            total_sections = len(course.sections)

            for section_idx, section in enumerate(course.sections):
                self.log_callback(f"\\n📁 섹션 {section_idx + 1}/{total_sections}: {section.title}")

                if self._process_section(section, section_idx):
                    success_count += 1
                    self.log_callback(f"✅ 섹션 {section_idx + 1} 완료")
                else:
                    self.log_callback(f"⚠️ 섹션 {section_idx + 1} 처리 실패 - 다음 섹션으로 진행")

                # 섹션 간 대기
                time.sleep(2)

            self.log_callback(f"\\n🏁 스크래핑 완료: {success_count}/{total_sections}개 섹션 성공")
            return success_count > 0

        except Exception as e:
            self.log_callback(f"❌ 스크래핑 워크플로우 실패: {str(e)}")
            return False

    def _ensure_normal_body_state(self) -> bool:
        """normal body 상태 확인 및 설정"""
        try:
            self.log_callback("🔍 페이지 상태 확인 중...")

            # 트랜스크립트 버튼 찾기
            transcript_button = self.element_finder.find_transcript_button()
            if not transcript_button:
                self.log_callback("⚠️ 트랜스크립트 버튼을 찾을 수 없음 - 정상 상태로 가정")
                return True

            # 현재 패널 상태 확인
            is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
            self.log_callback(f"📊 트랜스크립트 패널 상태: {'열림(script body)' if is_expanded else '닫힘(normal body)'}")

            # 패널이 열려있다면 닫기
            if is_expanded:
                self.log_callback("🔄 섹션 영역 표시를 위해 트랜스크립트 패널을 닫는 중...")
                if self.transcript_extractor.close_transcript_panel():
                    self.log_callback("✅ 트랜스크립트 패널 닫기 완료 → 섹션 영역 표시")
                    return True
                else:
                    self.log_callback("❌ 트랜스크립트 패널 닫기 실패")
                    return False
            else:
                self.log_callback("✅ 이미 normal body 상태 - 섹션 영역이 표시되어 있음")
                return True

        except Exception as e:
            self.log_callback(f"❌ 상태 확인 중 오류: {str(e)}")
            return False

    def _reanalyze_curriculum(self, course: Course) -> bool:
        """커리큘럼 재분석"""
        try:
            from .curriculum_analyzer import CurriculumAnalyzer
            analyzer = CurriculumAnalyzer(self.driver, self.wait, self.log_callback)
            success = analyzer.analyze_curriculum(course)

            if success:
                self.log_callback(f"✅ 재분석 완료: {len(course.sections)}개 섹션, {course.total_lectures}개 강의")
                return True
            else:
                return False

        except Exception as e:
            self.log_callback(f"❌ 커리큘럼 재분석 중 오류: {str(e)}")
            return False

    def _process_section(self, section: Section, section_idx: int) -> bool:
        """개별 섹션 처리"""
        try:
            self.log_callback(f"🔧 섹션 {section_idx + 1} 처리 중: {section.title}")

            # 1. 섹션 아코디언 열기
            if not self.section_navigator.open_section_accordion(section_idx):
                self.log_callback(f"❌ 섹션 {section_idx + 1} 아코디언 열기 실패")
                return False

            # 2. 섹션 내 비디오들 처리
            return self._process_section_videos(section, section_idx)

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 처리 실패: {str(e)}")
            return False

    def _process_section_videos(self, section: Section, section_idx: int) -> bool:
        """섹션 내 비디오들 처리"""
        try:
            self.log_callback(f"🎥 섹션 {section_idx + 1} 비디오 처리 시작...")

            # 섹션 콘텐츠 영역 찾기
            section_content = self._find_section_content_area(section_idx)
            if not section_content:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 콘텐츠 영역을 찾을 수 없음")
                return False

            # 강의 요소들 찾기
            lecture_elements = self._find_lecture_elements(section_content)
            if not lecture_elements:
                self.log_callback(f"❌ 섹션 {section_idx + 1}에서 강의를 찾을 수 없음")
                return False

            self.log_callback(f"🔍 섹션 {section_idx + 1}에서 {len(lecture_elements)}개 강의 발견")

            # 각 강의 처리
            success_count = 0
            skip_count = 0

            for lecture_idx, lecture_element in enumerate(lecture_elements):
                result = self._process_single_lecture(lecture_element, lecture_idx, section_idx)

                if result == "success":
                    success_count += 1
                elif result == "skip":
                    skip_count += 1

            # 결과 로그
            total_lectures = len(lecture_elements)
            self.log_callback(f"📊 섹션 {section_idx + 1} 결과: {success_count}개 자막 추출, {skip_count}개 건너뜀, 총 {total_lectures}개 강의")

            return success_count > 0

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 비디오 처리 실패: {str(e)}")
            return False

    def _process_single_lecture(self, lecture_element, lecture_idx: int, section_idx: int) -> str:
        """개별 강의 처리"""
        try:
            # 강의 제목 추출
            lecture_title = self._extract_lecture_title(lecture_element)
            self.log_callback(f"  📚 강의 {lecture_idx + 1}: {lecture_title}")

            # 강의 클릭
            if not self.click_handler.click_lecture_item(lecture_element):
                self.log_callback(f"    ⚠️ 강의 클릭 실패 - 건너뜀")
                return "skip"

            # 페이지 로딩 대기
            if not self.video_navigator.wait_for_video_page_load():
                self.log_callback(f"    ⚠️ 강의 페이지 로딩 실패 - 건너뜀")
                return "skip"

            # 트랜스크립트 추출
            transcript_content = self.transcript_extractor.extract_transcript_from_video()
            if not transcript_content:
                self.log_callback(f"    ⚠️ 트랜스크립트 추출 실패 - 건너뜀")
                return "skip"

            # 파일 저장
            self._save_transcript(transcript_content, lecture_title, section_idx, lecture_idx)

            # 섹션 목록으로 돌아가기
            self._return_to_section_list()

            self.log_callback(f"    ✅ 강의 {lecture_idx + 1} 자막 추출 완료")
            return "success"

        except Exception as e:
            self.log_callback(f"    ❌ 강의 {lecture_idx + 1} 처리 중 오류: {str(e)}")
            return "error"

    def _find_section_content_area(self, section_idx: int):
        """섹션 콘텐츠 영역 찾기"""
        selectors = [
            f"div[data-purpose='section-panel-{section_idx}']",
            f"div[data-purpose='section-panel-{section_idx + 1}']",
            f".curriculum-section:nth-child({section_idx + 1})"
        ]

        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except:
                continue

        return None

    def _find_lecture_elements(self, section_content):
        """강의 요소들 찾기"""
        for selector in UdemySelectors.LECTURE_ITEMS:
            try:
                elements = section_content.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except:
                continue
        return []

    def _extract_lecture_title(self, lecture_element) -> str:
        """강의 제목 추출"""
        try:
            for selector in UdemySelectors.LECTURE_TITLES:
                try:
                    title_element = lecture_element.find_element(By.CSS_SELECTOR, selector)
                    if title_element and title_element.text:
                        title = title_element.text.strip()
                        if title and not title.startswith("재생") and not title.startswith("시작"):
                            # 번호 제거
                            if ". " in title:
                                title = title.split(". ", 1)[1]
                            return title
                except:
                    continue

            # 전체 텍스트에서 추출 시도
            full_text = lecture_element.text
            if full_text:
                lines = full_text.split('\\n')
                for line in lines:
                    if line and not line.startswith("재생") and not line.startswith("시작") and "분" not in line:
                        if ". " in line:
                            line = line.split(". ", 1)[1]
                        return line

            return f"비디오_{int(time.time())}"

        except:
            return f"비디오_{int(time.time())}"

    def _save_transcript(self, content: str, video_title: str, section_idx: int, video_idx: int):
        """트랜스크립트 파일 저장"""
        try:
            if not self.current_course:
                self.log_callback("    ⚠️ 강의 정보가 없어 파일 저장 실패")
                return

            from pathlib import Path

            # 출력 디렉토리 생성
            output_dir = Path("output")
            ensure_directory(output_dir)

            # 강의명 폴더 생성
            safe_course_name = sanitize_filename(self.current_course.title)
            course_dir = output_dir / safe_course_name
            ensure_directory(course_dir)

            # 섹션 디렉토리 생성
            section_dir = course_dir / f"Section_{section_idx + 1:02d}"
            ensure_directory(section_dir)

            # 파일명 생성
            safe_title = sanitize_filename(video_title)
            filename = f"{video_idx + 1:02d}_{safe_title}.txt"
            file_path = section_dir / filename

            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Video: {video_title}\\n")
                f.write("=" * 50 + "\\n\\n")
                f.write(content)

            self.log_callback(f"    💾 저장완료: {filename}")

        except Exception as e:
            self.log_callback(f"    ❌ 파일 저장 실패: {str(e)}")

    def _return_to_section_list(self):
        """섹션 목록으로 돌아가기"""
        try:
            # 트랜스크립트 패널을 닫으면 자동으로 섹션 목록으로 돌아감
            self.transcript_extractor.close_transcript_panel()
        except Exception as e:
            self.log_callback(f"    ⚠️ 섹션 목록으로 돌아가기 실패: {str(e)}")

    # 기존 메서드들과의 호환성을 위한 메서드들
    def _find_transcript_button(self):
        """호환성을 위한 메서드"""
        return self.element_finder.find_transcript_button()

    def _find_video_area(self):
        """호환성을 위한 메서드"""
        return self.element_finder.find_video_area()