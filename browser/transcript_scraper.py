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

    def start_complete_scraping_workflow(self, course: Course) -> bool:
        """전체 스크래핑 워크플로우 시작"""
        try:
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
                    self.log_callback(f"❌ 섹션 {section_idx + 1} 실패")

                # 섹션 간 대기
                time.sleep(2)

            self.log_callback(f"\n🏁 스크래핑 완료: {success_count}/{total_sections}개 섹션 성공")
            return success_count > 0

        except Exception as e:
            self.log_callback(f"❌ 스크래핑 워크플로우 실패: {str(e)}")
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
                time.sleep(2)  # 아코디언 열리는 시간 대기
                self.log_callback(f"✅ 섹션 {section_idx + 1} 아코디언 열림")
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

            # 비디오 요소들 찾기
            video_elements = content_area.find_elements(By.CSS_SELECTOR,
                "li[data-purpose='curriculum-item-video'], .curriculum-item-video, li")

            if not video_elements:
                self.log_callback(f"⚠️ 섹션 {section_idx + 1}에서 비디오 요소를 찾을 수 없음")
                return True  # 비디오가 없는 섹션일 수 있음

            self.log_callback(f"🔍 섹션 {section_idx + 1}에서 {len(video_elements)}개 요소 발견")

            success_count = 0
            for video_idx, video_element in enumerate(video_elements):
                if self._process_single_video(video_element, video_idx, section_idx):
                    success_count += 1

                # 비디오 간 대기
                time.sleep(1)

            self.log_callback(f"📊 섹션 {section_idx + 1} 결과: {success_count}/{len(video_elements)}개 비디오 성공")
            return success_count > 0

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

                    # 섹션 내 콘텐츠 영역 찾기
                    content_selectors = [
                        ".section-content ul",
                        ".curriculum-section-content ul",
                        "ul",
                        ".section-list"
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

    def _process_single_video(self, video_element, video_idx: int, section_idx: int) -> bool:
        """개별 비디오 처리"""
        try:
            # 비디오 제목 추출
            video_title = self._extract_video_title(video_element)
            self.log_callback(f"  🎬 비디오 {video_idx + 1}: {video_title}")

            # 비디오 클릭
            if not self._click_video(video_element):
                self.log_callback(f"    ❌ 비디오 클릭 실패")
                return False

            # 비디오 페이지 로딩 대기
            if not self._wait_for_video_page():
                self.log_callback(f"    ❌ 비디오 페이지 로딩 실패")
                return False

            # 자막 패널 열기
            if not self._open_transcript_panel():
                self.log_callback(f"    ❌ 자막 패널 열기 실패")
                return False

            # 자막 내용 추출
            transcript_content = self._extract_transcript_content()
            if not transcript_content:
                self.log_callback(f"    ⚠️ 자막 내용 없음")
                return False

            # 자막 파일 저장
            self._save_transcript(transcript_content, video_title, section_idx, video_idx)

            # 자막 패널 닫기
            self._close_transcript_panel()

            self.log_callback(f"    ✅ 비디오 {video_idx + 1} 완료")
            return True

        except Exception as e:
            self.log_callback(f"    ❌ 비디오 {video_idx + 1} 처리 실패: {str(e)}")
            return False

    def _extract_video_title(self, video_element) -> str:
        """비디오 제목 추출"""
        try:
            title_selectors = [
                "span[data-purpose='item-title']",
                ".curriculum-item-title",
                ".lecture-name",
                "span"
            ]

            for selector in title_selectors:
                try:
                    title_element = video_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        return title
                except:
                    continue

            return f"비디오_{int(time.time())}"

        except:
            return f"비디오_{int(time.time())}"

    def _click_video(self, video_element) -> bool:
        """비디오 클릭"""
        try:
            # 클릭 가능한 요소 찾기
            clickable_selectors = [
                "a",
                "button",
                "span[data-purpose='item-title']"
            ]

            for selector in clickable_selectors:
                try:
                    clickable = video_element.find_element(By.CSS_SELECTOR, selector)
                    if clickable.is_displayed():
                        clickable.click()
                        return True
                except:
                    continue

            # 직접 클릭
            video_element.click()
            return True

        except Exception as e:
            return False

    def _wait_for_video_page(self) -> bool:
        """비디오 페이지 로딩 대기"""
        try:
            # URL이 lecture을 포함하는지 확인
            for i in range(10):
                if 'lecture' in self.driver.current_url:
                    time.sleep(2)  # 추가 로딩 대기
                    return True
                time.sleep(1)

            return False

        except:
            return False

    def _open_transcript_panel(self) -> bool:
        """자막 패널 열기"""
        try:
            # 자막 버튼 찾기
            transcript_selectors = [
                "button[data-purpose='transcript-toggle']",
                ".transcript-button",
                "button:contains('Transcript')",
                "button:contains('자막')"
            ]

            for selector in transcript_selectors:
                try:
                    if selector.startswith("button:contains"):
                        # contains 사용 시 XPath로 변환
                        text = selector.split("'")[1]
                        xpath_selector = f"//button[contains(text(), '{text}')]"
                        transcript_button = self.driver.find_element(By.XPATH, xpath_selector)
                    else:
                        transcript_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if transcript_button.is_displayed():
                        transcript_button.click()
                        time.sleep(2)
                        return True
                except:
                    continue

            return False

        except:
            return False

    def _extract_transcript_content(self) -> Optional[str]:
        """자막 내용 추출"""
        try:
            # 자막 패널이 열릴 때까지 대기
            time.sleep(2)

            # 자막 컨테이너 찾기
            transcript_selectors = [
                ".transcript-container",
                "[data-purpose='transcript']",
                ".transcript-content",
                ".captions-display"
            ]

            transcript_container = None
            for selector in transcript_selectors:
                try:
                    container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if container.is_displayed():
                        transcript_container = container
                        break
                except:
                    continue

            if not transcript_container:
                return None

            # 자막 텍스트 추출
            transcript_elements = transcript_container.find_elements(By.CSS_SELECTOR,
                ".transcript-cue, .caption-line, p, div")

            if transcript_elements:
                transcript_lines = []
                for element in transcript_elements:
                    text = element.text.strip()
                    if text:
                        transcript_lines.append(text)

                return "\n".join(transcript_lines)

            # 전체 텍스트 추출
            return transcript_container.text.strip()

        except Exception as e:
            return None

    def _save_transcript(self, content: str, video_title: str, section_idx: int, video_idx: int):
        """자막 파일 저장"""
        try:
            # 출력 디렉토리 생성
            output_dir = Config.get_output_directory()
            section_dir = output_dir / f"Section_{section_idx + 1:02d}"
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

    def _close_transcript_panel(self):
        """자막 패널 닫기"""
        try:
            # 같은 버튼을 다시 클릭하거나 닫기 버튼 클릭
            close_selectors = [
                "button[data-purpose='transcript-toggle']",
                ".transcript-close",
                ".close-button"
            ]

            for selector in close_selectors:
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if close_button.is_displayed():
                        close_button.click()
                        break
                except:
                    continue

        except:
            pass