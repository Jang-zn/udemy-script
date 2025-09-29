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
from .smart_waiter import SmartWaiter


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
        self.smart_waiter = SmartWaiter(driver, wait, log_callback)

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

                # 섹션 간 최소 대기 (성능 최적화)
                time.sleep(0.5)

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
                # 디버깅: 섹션 내용 구조 확인
                self._debug_section_structure(section_content, section_idx)
                return False

            self.log_callback(f"🔍 섹션 {section_idx + 1}에서 {len(lecture_elements)}개 강의 발견")

            # 각 강의 처리 (스마트 대기 적용)
            success_count = 0
            skip_count = 0

            for lecture_idx in range(len(lecture_elements)):
                # 각 강의마다 DOM에서 최신 요소를 다시 찾기 (stale element 방지)
                # 섹션 콘텐츠 영역도 다시 찾기
                fresh_section_content = self._find_section_content_area(section_idx)
                if not fresh_section_content:
                    self.log_callback(f"  ⚠️ 섹션 {section_idx + 1} 콘텐츠 영역을 다시 찾을 수 없음 - 건너뜀")
                    skip_count += 1
                    continue

                fresh_lecture_elements = self._find_lecture_elements(fresh_section_content)
                if not fresh_lecture_elements or len(fresh_lecture_elements) <= lecture_idx:
                    self.log_callback(f"  ⚠️ 강의 {lecture_idx + 1} 요소를 다시 찾을 수 없음 - 건너뜀")
                    skip_count += 1
                    continue

                current_lecture_element = fresh_lecture_elements[lecture_idx]

                # 강의 처리
                result = self._process_single_lecture(current_lecture_element, lecture_idx, section_idx, fresh_section_content)

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

    def _process_single_lecture(self, lecture_element, lecture_idx: int, section_idx: int, section_content=None) -> str:
        """개별 강의 처리"""
        try:
            # 강의 제목 추출
            lecture_title = self._extract_lecture_title(lecture_element)

            # 강의 타입 감지 (커리큘럼 아이콘 기반)
            lecture_type = self._get_lecture_type_from_element(lecture_element)
            self.log_callback(f"  📚 강의 {lecture_idx + 1}: {lecture_title} (타입: {lecture_type})")

            # 문서/아티클 강의는 스킵 (트랜스크립트가 없음)
            if lecture_type == "document":
                self.log_callback(f"    ⏭️ 문서 강의는 스킵합니다 - 트랜스크립트 없음")
                return "skip"

            # 퀴즈나 리소스 강의도 스킵 (트랜스크립트가 없음)
            if lecture_type in ["quiz", "resource"]:
                self.log_callback(f"    ⏭️ {lecture_type} 강의는 스킵합니다 - 트랜스크립트 없음")
                return "skip"

            # 강의 클릭 (디버깅 추가)
            self.log_callback(f"    🖱️ 강의 {lecture_idx + 1} 클릭 시도 중...")
            if not self.click_handler.click_lecture_item(lecture_element):
                self.log_callback(f"    ❌ 강의 클릭 실패")
                # 클릭 실패 원인 디버깅
                self._debug_click_failure(lecture_element, lecture_idx)
                return "skip"
            self.log_callback(f"    ✅ 강의 {lecture_idx + 1} 클릭 성공")

            # 페이지 로딩 대기 (타입별 최적화된 대기)
            if not self.video_navigator.wait_for_video_page_load(lecture_type_hint=lecture_type):
                self.log_callback(f"    ⚠️ 강의 페이지 로딩 실패 - 건너뜀")
                return "skip"

            # 트랜스크립트 추출 (타입 힌트 전달)
            transcript_content = self.transcript_extractor.extract_transcript_from_video()
            if not transcript_content:
                self.log_callback(f"    ⚠️ 트랜스크립트 추출 실패 - 건너뜀")
                return "skip"

            # 파일 저장
            self._save_transcript(transcript_content, lecture_title, section_idx, lecture_idx)

            # 섹션 목록으로 돌아가기 (스마트 대기)
            if self._return_to_section_list_smart(section_content):
                self.log_callback(f"    ✅ 강의 {lecture_idx + 1} 자막 추출 완료")
                return "success"
            else:
                self.log_callback(f"    ⚠️ 강의 {lecture_idx + 1} 자막 추출했으나 섹션 복귀 실패")
                return "success"  # 자막은 추출했으므로 성공으로 처리

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
        """강의 요소들 찾기 (개선된 로직)"""
        for selector in UdemySelectors.LECTURE_ITEMS:
            try:
                elements = section_content.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # 강의 요소인지 필터링
                    valid_elements = []
                    for elem in elements:
                        if self._is_valid_lecture_element(elem):
                            valid_elements.append(elem)

                    if valid_elements:
                        self.log_callback(f"      '{selector}': {len(valid_elements)}개 유효한 강의 발견 (전체 {len(elements)}개 중)")
                        return valid_elements

            except Exception as e:
                self.log_callback(f"      '{selector}' 검색 오류: {str(e)}")
                continue

        return []

    def _is_valid_lecture_element(self, element) -> bool:
        """요소가 유효한 강의 요소인지 확인"""
        try:
            # 요소가 보이고 활성화되어 있는지 확인 (stale element 방지)
            try:
                if not element.is_displayed():
                    return False
            except:
                # stale element인 경우 무효한 요소로 처리
                return False

            # 텍스트나 속성에서 강의 관련 단서 찾기 (stale element 방지)
            try:
                element_text = element.text.lower() if element.text else ""
                href = element.get_attribute('href') or ""
                data_purpose = element.get_attribute('data-purpose') or ""
                aria_label = element.get_attribute('aria-label') or ""
                title = element.get_attribute('title') or ""
            except:
                # stale element인 경우 무효한 요소로 처리
                return False

            # 강의 관련 키워드 확인
            lecture_keywords = ["lecture", "강의", "재생", "play", "분", "시간", "video"]
            all_text = f"{element_text} {href} {data_purpose} {aria_label} {title}".lower()

            for keyword in lecture_keywords:
                if keyword in all_text:
                    return True

            # curriculum-item이 포함된 경우
            if "curriculum-item" in data_purpose:
                return True

            # href에 lecture가 포함된 경우
            if "lecture" in href or "/learn/" in href:
                return True

            return False

        except:
            return False

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

            # 섹션 디렉토리 생성 (섹션 제목 포함)
            if section_idx < len(self.current_course.sections):
                section_title = self.current_course.sections[section_idx].title
                safe_section_title = sanitize_filename(section_title)
                section_dir = course_dir / f"Section_{section_idx + 1:02d}_{safe_section_title}"
            else:
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
        """섹션 목록으로 돌아가기 (기존 방식)"""
        try:
            # 트랜스크립트 패널을 닫으면 자동으로 섹션 목록으로 돌아감
            self.transcript_extractor.close_transcript_panel()
        except Exception as e:
            self.log_callback(f"    ⚠️ 섹션 목록으로 돌아가기 실패: {str(e)}")

    def _return_to_section_list_smart(self, section_content=None) -> bool:
        """섹션 목록으로 돌아가기 (스마트 대기)"""
        try:
            self.log_callback("    🔄 섹션 목록으로 복귀 중...")

            # 트랜스크립트 패널 닫기 (스마트 대기 적용)
            if self.transcript_extractor.close_transcript_panel():
                self.log_callback("    ✅ 섹션 목록 복귀 완료")
                return True
            else:
                self.log_callback("    ⚠️ 섹션 목록 복귀 부분 실패")
                return False

        except Exception as e:
            self.log_callback(f"    ❌ 섹션 목록 복귀 실패: {str(e)}")
            return False

    def _get_lecture_type_from_element(self, lecture_element) -> str:
        """강의 요소에서 강의 타입 감지 (커리큘럼 아이콘 기반)"""
        try:
            # 더 안전한 방식으로 SVG use 요소들을 찾고 xlink:href 속성 확인
            all_use_elements = lecture_element.find_elements(By.CSS_SELECTOR, "svg use")

            for use_element in all_use_elements:
                try:
                    href = use_element.get_attribute("xlink:href")
                    if not href:
                        href = use_element.get_attribute("href")  # 새로운 표준

                    if href:
                        if "#icon-video" in href:
                            self.log_callback(f"      🎬 비디오 아이콘 발견: {href}")
                            return "video"
                        elif "#icon-article" in href:
                            self.log_callback(f"      📄 문서 아이콘 발견: {href}")
                            return "document"
                        elif "#icon-quiz" in href or "#icon-assignment" in href:
                            self.log_callback(f"      📝 퀴즈 아이콘 발견: {href}")
                            return "quiz"
                        elif "#icon-file" in href or "#icon-download" in href:
                            self.log_callback(f"      📁 리소스 아이콘 발견: {href}")
                            return "resource"
                except Exception:
                    continue

            # 디버깅: 발견된 아이콘들 로그
            try:
                if all_use_elements:
                    icon_hrefs = []
                    for use_elem in all_use_elements[:3]:  # 처음 3개만
                        href = use_elem.get_attribute("xlink:href") or use_elem.get_attribute("href")
                        if href:
                            icon_hrefs.append(href)
                    if icon_hrefs:
                        self.log_callback(f"      ❓ 알 수 없는 아이콘: {icon_hrefs}")
            except Exception:
                pass

            return "unknown"

        except Exception as e:
            self.log_callback(f"      ❌ 아이콘 감지 실패: {str(e)}")
            return "unknown"

    # 기존 메서드들과의 호환성을 위한 메서드들
    def _find_transcript_button(self):
        """호환성을 위한 메서드"""
        return self.element_finder.find_transcript_button()

    def _find_video_area(self):
        """호환성을 위한 메서드"""
        return self.element_finder.find_video_area()

    def _debug_section_structure(self, section_content, section_idx: int):
        """섹션 구조 디버깅"""
        try:
            self.log_callback(f"🔍 섹션 {section_idx + 1} 구조 디버깅:")
            self.log_callback(f"      섹션 태그: {section_content.tag_name}")
            self.log_callback(f"      섹션 클래스: {section_content.get_attribute('class')}")
            self.log_callback(f"      섹션 data-purpose: {section_content.get_attribute('data-purpose')}")

            # 모든 하위 요소들 확인
            all_children = section_content.find_elements(By.CSS_SELECTOR, "*")
            self.log_callback(f"      전체 하위 요소 수: {len(all_children)}")

            # 강의 관련 가능성이 있는 요소들 찾기
            potential_lecture_selectors = [
                "[data-purpose*='curriculum-item']",
                "[data-purpose*='lecture']",
                ".curriculum-item",
                ".lecture",
                "a[href*='lecture']",
                "button[aria-label*='강의']",
                "button[aria-label*='재생']",
                "*[title*='분']"  # 시간 정보가 있는 요소
            ]

            for selector in potential_lecture_selectors:
                try:
                    elements = section_content.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.log_callback(f"      '{selector}': {len(elements)}개 발견")
                        for i, elem in enumerate(elements[:3]):  # 처음 3개만
                            try:
                                text_preview = elem.text[:50] if elem.text else "텍스트 없음"
                                classes = elem.get_attribute('class') or "클래스 없음"
                                data_purpose = elem.get_attribute('data-purpose') or "data-purpose 없음"
                                self.log_callback(f"        {i+1}. [{elem.tag_name}] {text_preview} (class: {classes[:30]}, data: {data_purpose})")
                            except:
                                self.log_callback(f"        {i+1}. [정보 추출 실패]")
                    else:
                        self.log_callback(f"      '{selector}': 0개 발견")
                except Exception as e:
                    self.log_callback(f"      '{selector}': 오류 - {str(e)}")

            # 텍스트 내용에서 강의 단서 찾기
            section_text = section_content.text
            if section_text:
                if "분" in section_text or "강의" in section_text or "재생" in section_text:
                    lines = section_text.split('\n')[:10]  # 처음 10줄만
                    self.log_callback("      섹션 텍스트 미리보기:")
                    for i, line in enumerate(lines):
                        if line.strip():
                            self.log_callback(f"        {i+1}. {line.strip()[:50]}")

        except Exception as e:
            self.log_callback(f"      ❌ 구조 디버깅 실패: {str(e)}")

    def _debug_click_failure(self, lecture_element, lecture_idx: int):
        """강의 클릭 실패 원인 디버깅"""
        try:
            self.log_callback(f"    🔍 강의 {lecture_idx + 1} 클릭 실패 원인 분석:")
            self.log_callback(f"      태그: {lecture_element.tag_name}")
            self.log_callback(f"      표시됨: {lecture_element.is_displayed()}")
            self.log_callback(f"      활성화됨: {lecture_element.is_enabled()}")

            # 기본 속성
            classes = lecture_element.get_attribute('class') or 'None'
            href = lecture_element.get_attribute('href') or 'None'
            data_purpose = lecture_element.get_attribute('data-purpose') or 'None'

            self.log_callback(f"      클래스: {classes[:50]}")
            self.log_callback(f"      href: {href[:50]}")
            self.log_callback(f"      data-purpose: {data_purpose}")

            # 텍스트 확인
            text = lecture_element.text[:100] if lecture_element.text else 'None'
            self.log_callback(f"      텍스트: {text}")

            # 클릭 가능한 하위 요소들 확인
            from .selectors import UdemySelectors
            for selector in UdemySelectors.LECTURE_CLICKABLE_ELEMENTS[:5]:  # 처음 5개만
                try:
                    elements = lecture_element.find_elements(By.CSS_SELECTOR, selector)
                    visible_elements = [e for e in elements if e.is_displayed() and e.is_enabled()]
                    if visible_elements:
                        self.log_callback(f"      '{selector}': {len(visible_elements)}개 클릭 가능 요소 발견")
                        break
                except:
                    continue
            else:
                self.log_callback(f"      ❌ 클릭 가능한 하위 요소를 찾을 수 없음")

            # 현재 활성 강의 확인
            is_current = lecture_element.get_attribute("aria-current") == "true"
            self.log_callback(f"      현재 활성 강의: {is_current}")

        except Exception as e:
            self.log_callback(f"      ❌ 클릭 실패 디버깅 오류: {str(e)}")