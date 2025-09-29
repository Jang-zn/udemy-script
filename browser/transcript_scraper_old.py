"""
Udemy 강의 자막/스크립트 추출 모듈
"""

import time
import os
from typing import Optional, List
from selenium.webdriver.common.by import By
from config import Config
from core.models import Course, Section, Lecture
from utils.file_utils import ensure_directory, sanitize_filename
from .base import BrowserBase


class TranscriptScraper(BrowserBase):
    def __init__(self, driver, wait, log_callback=None):
        super().__init__(driver, wait, log_callback)
        self.current_course = None

    def start_complete_scraping_workflow(self, course: Course) -> bool:
        """전체 스크래핑 워크플로우 시작"""
        try:
            self.current_course = course  # 강의 정보 저장
            self.log_callback("🚀 전체 스크래핑 워크플로우 시작...")
            self.log_callback(f"📚 대상 강의: {course.title}")
            self.log_callback(f"📊 총 {len(course.sections)}개 섹션, {course.total_lectures}개 강의")

            success_count = 0
            total_sections = len(course.sections)

            for section_idx, section in enumerate(course.sections):
                self.log_callback(f"\n📁 섹션 {section_idx + 1}/{total_sections}: {section.title}")

                if self._process_section(section, section_idx):
                    success_count += 1
                    self.log_callback(f"✅ 섹션 {section_idx + 1} 완료")
                else:
                    self.log_callback(f"⚠️ 섹션 {section_idx + 1} 처리 실패 - 다음 섹션으로 진행")
                    # 실패해도 다음 섹션으로 진행

                # 섹션 간 대기
                time.sleep(2)

            self.log_callback(f"\n🏁 스크래핑 완료: {success_count}/{total_sections}개 섹션 성공")
            return success_count > 0

        except Exception as e:
            self.log_callback(f"❌ 스크래핑 워크플로우 실패: {str(e)}")
            return False

    def _ensure_normal_body_state(self) -> bool:
        """강의 페이지가 normal body 상태(트랜스크립트 패널 닫힌 상태)인지 확인하고 조정"""
        try:
            self.log_callback("     🔍 트랜스크립트 패널 상태 확인 중...")

            # 1. 트랜스크립트 버튼 찾기
            transcript_button = self._find_transcript_button()
            if not transcript_button:
                self.log_callback("     ⚠️ 트랜스크립트 버튼을 찾을 수 없음 - 정상 상태로 가정")
                return True

            # 2. 현재 패널 상태 확인 (aria-expanded="true"면 열린 상태)
            is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
            self.log_callback(f"     📊 트랜스크립트 패널 상태: {'열림' if is_expanded else '닫힘'}")

            # 3. 패널이 열려있다면 닫기
            if is_expanded:
                self.log_callback("     🔄 트랜스크립트 패널을 닫는 중...")
                try:
                    # 마우스를 비디오 영역으로 이동해서 컨트롤바 표시
                    video_area = self._find_video_area()
                    if video_area:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(video_area).perform()
                        time.sleep(1)

                    # 트랜스크립트 버튼 클릭하여 패널 닫기
                    transcript_button.click()
                    time.sleep(2)  # 패널 닫히는 시간 대기

                    self.log_callback("     ✅ 트랜스크립트 패널 닫기 완료")
                    return True  # 상태가 변경됨
                except Exception as e:
                    self.log_callback(f"     ❌ 패널 닫기 실패: {str(e)}")
                    try:
                        # JavaScript로 클릭 시도
                        self.driver.execute_script("arguments[0].click();", transcript_button)
                        time.sleep(2)
                        self.log_callback("     ✅ JavaScript로 패널 닫기 완료")
                        return True  # 상태가 변경됨
                    except Exception as e2:
                        self.log_callback(f"     ❌ JavaScript 클릭도 실패: {str(e2)}")
                        return False
            else:
                self.log_callback("     ✅ 이미 normal body 상태입니다.")
                return False  # 상태 변경 없음

            return True

        except Exception as e:
            self.log_callback(f"     ❌ normal body 상태 확인 중 오류: {str(e)}")
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

                # XPath로도 시도
                try:
                    elements = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'ranscript') or contains(@aria-label, '자막') or contains(@aria-label, '대본')]")
                    for element in elements:
                        if element.is_displayed():
                            # 버튼을 찾았지만 호버 상태 유지
                            actions.move_to_element(element).perform()
                            return element
                except:
                    pass

                time.sleep(1)  # 다음 시도 전 대기

            return None

        except Exception:
            return None

    def _find_video_area(self):
        """비디오 영역 찾기 (scraper.py와 동일한 로직)"""
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

    def _reanalyze_curriculum(self, course: Course) -> bool:
        """상태 변경 후 커리큘럼 재분석"""
        try:
            # CurriculumAnalyzer를 사용해서 다시 분석
            from .curriculum_analyzer import CurriculumAnalyzer

            analyzer = CurriculumAnalyzer(self.driver, self.wait, self.log_callback)
            success = analyzer.analyze_curriculum(course)

            if success:
                self.log_callback(f"     ✅ 재분석 완료: {len(course.sections)}개 섹션, {course.total_lectures}개 강의")

                # 섹션 제목들을 로그로 출력 (처음 5개만)
                for i, section in enumerate(course.sections[:5]):
                    self.log_callback(f"       섹션 {i+1}: '{section.title}' ({len(section.lectures)}개 강의)")

                if len(course.sections) > 5:
                    self.log_callback(f"       ... 총 {len(course.sections)}개 섹션")

                return True
            else:
                return False

        except Exception as e:
            self.log_callback(f"     ❌ 커리큘럼 재분석 중 오류: {str(e)}")
            return False

    def _process_section(self, section: Section, section_idx: int) -> bool:
        """개별 섹션 처리"""
        try:
            self.log_callback(f"🔧 섹션 {section_idx + 1} 처리 중: {section.title}")

            # 1. 섹션 아코디언 열기
            if not self._open_section_accordion(section_idx):
                self.log_callback(f"❌ 섹션 {section_idx + 1} 아코디언 열기 실패")
                return False

            # 2. 섹션 내 비디오들 처리
            return self._process_section_videos(section, section_idx)

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 처리 실패: {str(e)}")
            return False

    def _open_section_accordion(self, section_idx: int) -> bool:
        """섹션 아코디언 열기"""
        try:
            self.log_callback(f"📂 섹션 {section_idx + 1} 아코디언 열기...")

            # 섹션 패널 찾기 (실제 HTML 구조 기반)
            section_selectors = [
                f"div[data-purpose='section-panel-{section_idx}']",
                f"div[data-purpose='section-panel-{section_idx + 1}']",  # 1부터 시작하는 경우
                f"div[data-purpose^='section-panel-']:nth-child({section_idx + 1})",
                f".curriculum-section:nth-child({section_idx + 1})"
            ]

            section_element = None
            for selector in section_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        section_element = element
                        self.log_callback(f"✅ 섹션 패널 발견: {selector}")
                        break
                except:
                    continue

            if not section_element:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 패널을 찾을 수 없음")
                return False

            # 아코디언 헤더(토글 버튼) 찾기
            header_selectors = [
                "button[data-purpose='section-header-button']",
                ".section-header button",
                ".curriculum-section-header",
                "button",
                ".section-title"
            ]

            accordion_button = None
            for selector in header_selectors:
                try:
                    button = section_element.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed():
                        accordion_button = button
                        break
                except:
                    continue

            if not accordion_button:
                self.log_callback(f"⚠️ 섹션 {section_idx + 1} 토글 버튼을 찾을 수 없음")
                return True  # 이미 열려있을 수도 있음

            # 아코디언이 닫혀있는지 확인
            is_collapsed = False
            try:
                # aria-expanded 속성 확인
                expanded = accordion_button.get_attribute('aria-expanded')
                if expanded and expanded.lower() == 'false':
                    is_collapsed = True

                # 또는 클래스명으로 확인
                class_name = accordion_button.get_attribute('class') or ""
                if 'collapsed' in class_name.lower():
                    is_collapsed = True

            except:
                # 기본적으로 닫혀있다고 가정
                is_collapsed = True

            if is_collapsed:
                self.log_callback(f"🔓 섹션 {section_idx + 1} 아코디언 열기 중...")
                accordion_button.click()

                # 콘텐츠가 로드될 때까지 대기
                from selenium.webdriver.support import expected_conditions as EC
                try:
                    # 섹션 내 ul 요소가 나타날 때까지 대기 (최대 10초)
                    self.wait.until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR,
                            f"div[data-purpose='section-panel-{section_idx}'] ul, "
                            f"div[data-purpose='section-panel-{section_idx}'] .ud-accordion-panel-content ul"
                        ))
                    )
                    self.log_callback(f"✅ 섹션 {section_idx + 1} 아코디언 열림 및 콘텐츠 로드 완료")
                except:
                    # 타임아웃시 짧은 대기 후 진행
                    time.sleep(1)
                    self.log_callback(f"⚠️ 섹션 {section_idx + 1} 콘텐츠 로드 대기 타임아웃, 진행 시도")
            else:
                self.log_callback(f"✅ 섹션 {section_idx + 1} 이미 열려있음")

            return True

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 아코디언 열기 실패: {str(e)}")
            return False

    def _process_section_videos(self, section: Section, section_idx: int) -> bool:
        """섹션 내 비디오들 처리"""
        try:
            self.log_callback(f"🎥 섹션 {section_idx + 1} 비디오 처리 시작...")

            # 섹션의 콘텐츠 영역 찾기
            content_area = self._find_section_content_area_by_index(section_idx)
            if not content_area:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 콘텐츠 영역을 찾을 수 없음")
                return False

            # 모든 강의 요소 찾기 (비디오, 문서 구분 없이)
            lecture_elements = content_area.find_elements(By.CSS_SELECTOR, "li")

            if not lecture_elements:
                self.log_callback(f"⚠️ 섹션 {section_idx + 1}에서 강의 요소를 찾을 수 없음")
                return True  # 빈 섹션일 수 있음

            self.log_callback(f"🔍 섹션 {section_idx + 1}에서 {len(lecture_elements)}개 강의 발견")

            success_count = 0
            skip_count = 0

            for lecture_idx, lecture_element in enumerate(lecture_elements):
                result = self._process_single_lecture(lecture_element, lecture_idx, section_idx)

                if result == "success":
                    success_count += 1
                elif result == "skip":
                    skip_count += 1
                    self.log_callback(f"    ⏭️ 강의 {lecture_idx + 1} 건너뜀 (문서 또는 자막 없음)")
                else:  # "error"
                    self.log_callback(f"❌ 섹션 {section_idx + 1} 강의 {lecture_idx + 1} 처리 중 오류 - 다음 강의로 진행")
                    # 오류가 나도 다음 강의로 진행

                # 강의 간 대기
                import time
                time.sleep(0.5)

            self.log_callback(f"📊 섹션 {section_idx + 1} 결과: {success_count}개 자막 추출, {skip_count}개 건너뜀, 총 {len(lecture_elements)}개 강의")
            return True  # 항상 성공으로 처리하여 다음 섹션으로 진행

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 비디오 처리 실패: {str(e)}")
            return False

    def _find_section_content_area_by_index(self, section_idx: int):
        """섹션 인덱스로 콘텐츠 영역 찾기"""
        try:
            section_selectors = [
                f"div[data-purpose='section-panel-{section_idx}']",
                f"div[data-purpose='section-panel-{section_idx + 1}']",
                f".curriculum-section:nth-child({section_idx + 1})"
            ]

            for selector in section_selectors:
                try:
                    section_element = self.driver.find_element(By.CSS_SELECTOR, selector)

                    # 섹션 내 콘텐츠 영역 찾기 (Udemy의 실제 구조 기반)
                    content_selectors = [
                        ".accordion-panel-module--content--0dD7R ul",  # 실제 패널 콘텐츠 클래스
                        ".ud-accordion-panel-content ul",
                        ".accordion-panel-module--content-wrapper--TkHqe ul",
                        ".section-content ul",
                        ".curriculum-section-content ul",
                        "ul"
                    ]

                    for content_selector in content_selectors:
                        try:
                            content = section_element.find_element(By.CSS_SELECTOR, content_selector)
                            return content
                        except:
                            continue

                    return section_element

                except:
                    continue

            return None

        except:
            return None

    def _process_single_lecture(self, lecture_element, lecture_idx: int, section_idx: int) -> str:
        """개별 강의 처리 (비디오/문서 구분 없이)
        Returns: "success", "skip", or "error"
        """
        try:
            # 강의 제목 추출
            lecture_title = self._extract_video_title(lecture_element)
            self.log_callback(f"  📚 강의 {lecture_idx + 1}: {lecture_title}")

            # 강의 클릭
            if not self._click_video(lecture_element):
                self.log_callback(f"    ⚠️ 강의 클릭 실패 - 건너뜀")
                return "skip"

            # 페이지 로딩 대기
            if not self._wait_for_video_page():
                self.log_callback(f"    ⚠️ 강의 페이지 로딩 실패 - 건너뜀")
                return "skip"

            # 자막 패널 열기 시도
            if not self._open_transcript_panel():
                self.log_callback(f"    ℹ️ 자막 패널 없음 - 문서 또는 자막 없는 강의")
                # 섹션 목록으로 돌아가기
                self._return_to_section_list()
                return "skip"

            # 자막 내용 추출
            transcript_content = self._extract_transcript_content()
            if not transcript_content:
                self.log_callback(f"    ℹ️ 자막 내용 없음")
                # 자막 패널 닫기
                self._close_transcript_panel()
                return "skip"

            # 자막 파일 저장
            self._save_transcript(transcript_content, lecture_title, section_idx, lecture_idx)

            # 자막 패널 닫기 (자동으로 섹션 목록으로 돌아감)
            self._close_transcript_panel()

            self.log_callback(f"    ✅ 강의 {lecture_idx + 1} 자막 추출 완료")
            return "success"

        except Exception as e:
            self.log_callback(f"    ⚠️ 강의 {lecture_idx + 1} 처리 중 오류: {str(e)}")
            # 오류 발생시 섹션 목록으로 돌아가기 시도
            try:
                self._return_to_section_list()
            except:
                pass
            return "error"

    def _extract_video_title(self, video_element) -> str:
        """비디오 제목 추출"""
        try:
            # 실제 Udemy 구조에 맞는 선택자
            title_selectors = [
                "span[data-purpose='item-title']",  # 메인 제목 선택자
                ".curriculum-item-link--curriculum-item-title-content--S-urg span",  # 대체 선택자
                ".truncate-with-tooltip--ellipsis--YJw4N span",  # 툴팁 내 제목
                ".curriculum-item-title",
                ".lecture-name"
            ]

            for selector in title_selectors:
                try:
                    title_element = video_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title and not title.startswith("비디오_"):
                        # 번호 제거 (예: "1. 제목" -> "제목")
                        if ". " in title:
                            title = title.split(". ", 1)[1]
                        return title
                except:
                    continue

            # 전체 텍스트에서 추출 시도
            try:
                full_text = video_element.text.strip()
                if full_text:
                    lines = full_text.split('\n')
                    for line in lines:
                        if line and not line.startswith("재생") and not line.startswith("시작") and "분" not in line:
                            # 번호 제거
                            if ". " in line:
                                line = line.split(". ", 1)[1]
                            return line
            except:
                pass

            return f"비디오_{int(time.time())}"

        except:
            return f"비디오_{int(time.time())}"

    def _click_video(self, video_element) -> bool:
        """비디오 클릭"""
        try:
            # 현재 재생 중인지 확인 (aria-current="true")
            is_current = video_element.get_attribute("aria-current") == "true"
            if is_current:
                # 이미 재생 중이므로 클릭할 필요 없음
                return True

            # 더 포괄적인 클릭 가능한 요소 찾기
            clickable_selectors = [
                # 기본 링크와 버튼
                "a", "button",
                # 아이템 링크
                ".item-link", ".curriculum-item-link",
                # 커리큘럼 아이템
                "div[data-purpose^='curriculum-item']", "[data-purpose^='curriculum-item']",
                # 컨테이너들
                ".curriculum-item-link--item-container--HFnn0",
                ".curriculum-item--curriculum-item--1rHQL",
                # 제목 요소들
                "span[data-purpose='item-title']", "[data-purpose='item-title']",
                ".curriculum-item-link--curriculum-item-title--VBsdR",
                # 버튼들
                ".ud-btn", "button[aria-label*='재생']", "button[aria-label*='시작']",
                "button[aria-label*='Play']", "button[aria-label*='Start']"
            ]

            for selector in clickable_selectors:
                try:
                    elements = video_element.find_elements(By.CSS_SELECTOR, selector)
                    for clickable in elements:
                        if clickable.is_displayed() and clickable.is_enabled():
                            try:
                                # 스크롤하여 요소 보이기
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable)
                                import time
                                time.sleep(0.3)

                                # ActionChains로 클릭 시도
                                from selenium.webdriver.common.action_chains import ActionChains
                                actions = ActionChains(self.driver)
                                actions.move_to_element(clickable).click().perform()
                                time.sleep(0.3)
                                return True
                            except:
                                # 일반 클릭 시도
                                try:
                                    clickable.click()
                                    time.sleep(0.3)
                                    return True
                                except:
                                    # JavaScript 클릭 시도
                                    try:
                                        self.driver.execute_script("arguments[0].click();", clickable)
                                        time.sleep(0.3)
                                        return True
                                    except:
                                        continue
                except:
                    continue

            # 요소 자체에 직접 클릭 시도
            try:
                # 스크롤하여 요소 보이기
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video_element)
                import time
                time.sleep(0.3)

                # ActionChains로 클릭
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(video_element).click().perform()
                time.sleep(0.3)
                return True
            except:
                try:
                    # 일반 클릭
                    video_element.click()
                    time.sleep(0.3)
                    return True
                except:
                    try:
                        # JavaScript 클릭
                        self.driver.execute_script("arguments[0].click();", video_element)
                        time.sleep(0.3)
                        return True
                    except:
                        return False

        except Exception as e:
            return False

    def _wait_for_video_page(self) -> bool:
        """비디오 페이지 로딩 대기"""
        try:
            from selenium.webdriver.support import expected_conditions as EC
            import time

            # URL이 lecture을 포함할 때까지 대기 (최대 5초)
            for i in range(5):
                if 'lecture' in self.driver.current_url:
                    break
                time.sleep(1)
            else:
                return False

            # 페이지 로딩 대기
            time.sleep(2)

            # 비디오 플레이어가 로드될 때까지 추가 대기
            try:
                self.wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "video, .video-player, [data-purpose='video-player'], .lecture-view"
                    ))
                )
            except:
                # 문서 강의일 수도 있으므로 실패해도 계속
                pass

            # 추가 안정화 대기
            time.sleep(1)
            return True

        except:
            return False

    def _open_transcript_panel(self) -> bool:
        """자막 패널 열기 (강화된 로직)"""
        try:
            self.log_callback("    🔍 트랜스크립트 버튼 찾는 중...")

            # 1. 트랜스크립트 버튼 찾기
            transcript_button = self._find_transcript_button()
            if not transcript_button:
                self.log_callback("    ❌ 트랜스크립트 버튼을 찾을 수 없습니다.")
                return False

            # 2. 현재 패널 상태 확인
            is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
            self.log_callback(f"    📊 트랜스크립트 패널 상태: {'열림' if is_expanded else '닫힘'}")

            if is_expanded:
                self.log_callback("    ✅ 트랜스크립트 패널이 이미 열려있습니다.")
                return True

            # 3. 비디오 영역으로 마우스 이동 (컨트롤바 표시를 위해)
            video_area = self._find_video_area()
            if video_area:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(video_area).perform()
                # 마우스 호버 후 컨트롤바가 나타날 때까지 잠시 대기
                import time
                time.sleep(0.5)

            # 4. 트랜스크립트 버튼 클릭
            self.log_callback("    🖱️ 트랜스크립트 버튼 클릭 중...")
            try:
                transcript_button.click()
            except Exception as e:
                self.log_callback(f"    ⚠️ 일반 클릭 실패: {str(e)}, JavaScript 클릭 시도...")
                self.driver.execute_script("arguments[0].click();", transcript_button)

            # 5. 패널 열릴 때까지 대기
            from selenium.webdriver.support import expected_conditions as EC
            try:
                # aria-expanded가 true가 될 때까지 대기
                self.wait.until(
                    lambda driver: transcript_button.get_attribute('aria-expanded') == 'true'
                )
                # 패널 콘텐츠가 로드될 때까지 추가 대기
                self.wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "[data-purpose='transcript-panel'], .transcript--transcript-panel--JLceZ"
                    ))
                )
            except:
                import time
                time.sleep(1)  # 폴백

            # 6. 패널이 열렸는지 확인
            is_expanded_after = transcript_button.get_attribute('aria-expanded') == 'true'
            if is_expanded_after:
                self.log_callback("    ✅ 트랜스크립트 패널 열기 완료")
                return True
            else:
                self.log_callback("    ❌ 트랜스크립트 패널 열기 실패 - 상태 변화 없음")
                return False

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 패널 열기 중 오류: {str(e)}")
            return False

    def _extract_transcript_content(self) -> Optional[str]:
        """자막 내용 추출 (강화된 로직)"""
        try:
            self.log_callback("    📖 트랜스크립트 내용 추출 중...")
            time.sleep(2)

            # 1. 트랜스크립트 패널 찾기 (실제 HTML 구조 기반)
            transcript_panel = self._find_transcript_panel_for_extraction()
            if not transcript_panel:
                self.log_callback("    ❌ 트랜스크립트 패널을 찾을 수 없습니다.")
                return None

            self.log_callback(f"    ✅ 트랜스크립트 패널 발견: {transcript_panel.tag_name}")

            # 2. cue 요소들 찾기 (실제 구조: data-purpose="transcript-cue")
            cue_elements = transcript_panel.find_elements(By.CSS_SELECTOR, "[data-purpose='transcript-cue']")
            self.log_callback(f"    📊 트랜스크립트 cue 요소 {len(cue_elements)}개 발견")

            if not cue_elements:
                self.log_callback("    ❌ 트랜스크립트 cue 요소가 없습니다.")
                self._debug_transcript_panel_contents(transcript_panel)
                return None

            # 3. 각 cue에서 텍스트 추출
            transcript_lines = []
            for i, cue_element in enumerate(cue_elements):
                try:
                    # data-purpose="cue-text" span에서 텍스트 추출
                    text_element = cue_element.find_element(By.CSS_SELECTOR, "[data-purpose='cue-text']")
                    text = text_element.text.strip()

                    if text:
                        transcript_lines.append(text)
                        if i < 3:  # 처음 3개만 로그
                            self.log_callback(f"      {i+1}. '{text[:30]}...'")

                except Exception as e:
                    if i < 3:
                        self.log_callback(f"      ❌ {i+1}번째 cue 추출 실패: {str(e)}")
                    continue

            if transcript_lines:
                total_text = "\n".join(transcript_lines)
                self.log_callback(f"    ✅ 트랜스크립트 추출 완료: {len(transcript_lines)}개 항목, 총 {len(total_text)}자")
                return total_text
            else:
                self.log_callback("    ❌ 추출된 텍스트가 없습니다.")
                return None

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 추출 중 오류: {str(e)}")
            return None

    def _find_transcript_panel_for_extraction(self):
        """트랜스크립트 패널 찾기 (추출용)"""
        try:
            # 실제 HTML 구조 기반 선택자
            panel_selectors = [
                "[data-purpose='transcript-panel']",
                ".transcript--transcript-panel--JLceZ",
                ".transcript--transcript-panel--JLceZ[data-purpose='transcript-panel']"
            ]

            for selector in panel_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        return element
                except:
                    continue

            return None

        except Exception:
            return None

    def _debug_transcript_panel_contents(self, panel_element):
        """디버깅: 트랜스크립트 패널 내용 분석"""
        try:
            self.log_callback("    🔍 디버깅: 트랜스크립트 패널 내용 분석...")

            # 패널의 모든 자식 요소들
            all_children = panel_element.find_elements(By.XPATH, ".//*")
            self.log_callback(f"    📊 패널 내 전체 요소 개수: {len(all_children)}")

            # data-purpose 속성을 가진 요소들
            data_purpose_elements = panel_element.find_elements(By.CSS_SELECTOR, "[data-purpose]")
            self.log_callback(f"    📊 data-purpose 속성 요소 개수: {len(data_purpose_elements)}")

            if data_purpose_elements:
                self.log_callback("    📋 data-purpose 속성들 (최대 10개):")
                for i, elem in enumerate(data_purpose_elements[:10]):
                    try:
                        purpose = elem.get_attribute('data-purpose')
                        tag = elem.tag_name
                        text = elem.text[:30] + "..." if len(elem.text) > 30 else elem.text
                        self.log_callback(f"       {i+1}. <{tag} data-purpose='{purpose}'> '{text}'")
                    except:
                        continue

        except Exception as e:
            self.log_callback(f"    ❌ 패널 내용 디버깅 중 오류: {str(e)}")

    def _save_transcript(self, content: str, video_title: str, section_idx: int, video_idx: int):
        """자막 파일 저장"""
        try:
            # 강의명 폴더 생성
            output_dir = Config.get_output_directory()
            course_name = self.current_course.title if self.current_course else "Unknown_Course"
            safe_course_name = sanitize_filename(course_name)
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
                f.write(f"Video: {video_title}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)

            self.log_callback(f"    💾 저장완료: {filename}")

        except Exception as e:
            self.log_callback(f"    ❌ 파일 저장 실패: {str(e)}")

    def _return_to_section_list(self):
        """섹션 목록으로 돌아가기 (트랜스크립트 패널 닫기)"""
        try:
            # 트랜스크립트 패널을 닫으면 자동으로 섹션 목록으로 돌아감
            self._close_transcript_panel()
        except Exception as e:
            self.log_callback(f"    ⚠️ 섹션 목록으로 돌아가기 실패: {str(e)}")

    def _close_transcript_panel(self):
        """트랜스크립트 패널 닫기 (사이드바가 자동으로 섹션 목록으로 복귀)"""
        try:
            self.log_callback("    🔄 트랜스크립트 패널 닫는 중 (섹션 목록 복귀)...")

            # 1. 비디오 영역으로 마우스 이동 먼저 (컨트롤바 표시를 위해)
            video_area = self._find_video_area()
            if video_area:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(video_area).perform()
                # 마우스 호버 후 컨트롤바가 나타날 때까지 잠시 대기
                import time
                time.sleep(0.5)
            else:
                self.log_callback("    ⚠️ 비디오 영역을 찾을 수 없음")

            # 2. 트랜스크립트 버튼 찾기
            transcript_button = self._find_transcript_button()
            if not transcript_button:
                self.log_callback("    ⚠️ 트랜스크립트 버튼을 찾을 수 없음")
                return

            # 3. 현재 패널 상태 확인
            is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'

            if not is_expanded:
                self.log_callback("    ℹ️ 트랜스크립트 패널이 이미 닫혀있습니다.")
                return

            # 4. 패널 닫기 (사이드바가 자동으로 섹션 목록으로 변경됨)
            try:
                transcript_button.click()
                time.sleep(2)
                self.log_callback("    ✅ 트랜스크립트 패널 닫기 완료 → 섹션 목록 복귀")
            except Exception as e:
                self.log_callback(f"    ⚠️ 일반 클릭 실패: {str(e)}, JavaScript 클릭 시도...")
                try:
                    self.driver.execute_script("arguments[0].click();", transcript_button)
                    time.sleep(2)
                    self.log_callback("    ✅ JavaScript로 트랜스크립트 패널 닫기 완료 → 섹션 목록 복귀")
                except Exception as e2:
                    self.log_callback(f"    ❌ 패널 닫기 실패: {str(e2)}")

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 패널 닫기 중 오류: {str(e)}")

