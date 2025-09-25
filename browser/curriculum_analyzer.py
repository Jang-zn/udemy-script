"""
Udemy 강의 커리큘럼 분석 모듈
"""

import time
from typing import Optional, List
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from config import Config
from core.models import Course, Section, Lecture
from .base import BrowserBase


class CurriculumAnalyzer(BrowserBase):
    def __init__(self, driver, wait, log_callback=None):
        super().__init__(driver, wait, log_callback)

    def analyze_curriculum(self, course: Course) -> bool:
        """강의 커리큘럼 분석"""
        try:
            self.log_callback("📋 강의 커리큘럼 분석 시작...")

            # 1. 커리큘럼 영역으로 스크롤
            self._scroll_curriculum_to_top()

            # 2. 섹션 요소들 찾기
            section_elements = self._find_curriculum_sections()
            if not section_elements:
                self.log_callback("❌ 커리큘럼 섹션을 찾을 수 없습니다.")
                return False

            self.log_callback(f"✅ {len(section_elements)}개 섹션 발견")

            # 3. 각 섹션 분석
            for idx, section_element in enumerate(section_elements):
                section = self._analyze_section(section_element, idx)
                if section:
                    course.sections.append(section)
                    self.log_callback(f"   섹션 {idx + 1}: '{section.title}' ({section.lecture_count}개 강의)")

            self.log_callback(f"📊 커리큘럼 분석 완료: {len(course.sections)}개 섹션, {course.total_lectures}개 강의")
            return True

        except Exception as e:
            self.log_callback(f"❌ 커리큘럼 분석 실패: {str(e)}")
            return False

    def _find_curriculum_sections(self) -> List:
        """커리큘럼 섹션 요소들 찾기"""
        try:
            self.log_callback("🔍 커리큘럼 섹션 검색 중...")

            # 실제 HTML 구조에 기반한 선택자들
            section_selectors = [
                "div[data-purpose^='section-panel-']",  # 실제 Udemy 구조
                ".curriculum-section",
                ".section-container",
                ".curriculum-item[data-purpose*='section']",
                "div[class*='section'][class*='panel']"
            ]

            for selector in section_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.log_callback(f"✅ {selector}로 {len(elements)}개 섹션 발견")
                        return elements
                except Exception as e:
                    self.log_callback(f"   선택자 {selector} 실패: {str(e)}")
                    continue

            # 모든 선택자 실패 시 페이지 소스 분석
            self.log_callback("⚠️ 섹션 선택자 모두 실패, 페이지 구조 분석...")
            try:
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # data-purpose 속성에서 section 관련 요소 찾기
                section_elements = soup.find_all('div', {'data-purpose': lambda x: x and 'section' in x})
                if section_elements:
                    self.log_callback(f"✅ BeautifulSoup으로 {len(section_elements)}개 섹션 발견")
                    # Selenium 요소로 다시 찾기
                    selenium_elements = []
                    for elem in section_elements:
                        data_purpose = elem.get('data-purpose')
                        try:
                            sel_elem = self.driver.find_element(By.CSS_SELECTOR, f"div[data-purpose='{data_purpose}']")
                            selenium_elements.append(sel_elem)
                        except:
                            continue
                    return selenium_elements

            except Exception as e:
                self.log_callback(f"   BeautifulSoup 분석 실패: {str(e)}")

            return []

        except Exception as e:
            self.log_callback(f"❌ 섹션 찾기 실패: {str(e)}")
            return []

    def _scroll_curriculum_to_top(self):
        """커리큘럼 영역을 페이지 상단으로 스크롤"""
        try:
            self.log_callback("📜 커리큘럼 영역으로 스크롤...")

            # 커리큘럼 관련 요소 찾기
            curriculum_selectors = [
                "[data-purpose='curriculum']",
                ".curriculum",
                ".course-curriculum",
                "#curriculum",
                ".curriculum-container"
            ]

            curriculum_element = None
            for selector in curriculum_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        curriculum_element = element
                        self.log_callback(f"✅ 커리큘럼 영역 발견: {selector}")
                        break
                except:
                    continue

            if curriculum_element:
                # 커리큘럼 영역으로 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", curriculum_element)
                time.sleep(1)
                self.log_callback("✅ 커리큘럼 영역으로 스크롤 완료")
            else:
                self.log_callback("⚠️ 커리큘럼 영역을 찾을 수 없어 페이지 상단으로 스크롤")
                self.driver.execute_script("window.scrollTo(0, 0);")

            time.sleep(2)  # 스크롤 후 안정화 대기

        except Exception as e:
            self.log_callback(f"⚠️ 스크롤 중 오류: {str(e)}")
            # 기본 스크롤
            try:
                self.driver.execute_script("window.scrollTo(0, 0);")
            except:
                pass

    def _analyze_section(self, section_element, section_idx: int) -> Optional[Section]:
        """개별 섹션 분석"""
        try:
            # 섹션 제목 추출
            section_title = self._extract_section_title(section_element)
            if not section_title:
                self.log_callback(f"   섹션 {section_idx + 1}: 제목 추출 실패")
                return None

            # Section 객체 생성
            section = Section(title=section_title, section_index=section_idx)

            # 섹션 내 강의 분석
            content_area = self._find_section_content_area(section_element)
            if content_area:
                video_lectures = self._find_video_lectures(content_area)
                for lecture_idx, lecture_element in enumerate(video_lectures):
                    lecture = self._analyze_lecture(lecture_element, lecture_idx)
                    if lecture:
                        section.lectures.append(lecture)

            return section

        except Exception as e:
            self.log_callback(f"   섹션 {section_idx + 1} 분석 실패: {str(e)}")
            return None

    def _find_section_content_area(self, section_element):
        """섹션의 콘텐츠 영역 찾기"""
        try:
            # 섹션 내용이 들어있는 영역 찾기
            content_selectors = [
                ".section-content",
                ".curriculum-section-content",
                ".section-list",
                "ul",
                ".lecture-list"
            ]

            for selector in content_selectors:
                try:
                    content = section_element.find_element(By.CSS_SELECTOR, selector)
                    return content
                except:
                    continue

            # 직접 자식 요소들 반환
            return section_element

        except:
            return section_element

    def _find_video_lectures(self, content_area):
        """비디오 강의 요소들 찾기"""
        try:
            # 비디오 강의를 나타내는 선택자들
            video_selectors = [
                "li[data-purpose='curriculum-item-video']",
                ".curriculum-item-video",
                "li.curriculum-item",
                "[data-purpose*='video']",
                "li"  # 마지막 후보
            ]

            for selector in video_selectors:
                try:
                    videos = content_area.find_elements(By.CSS_SELECTOR, selector)
                    if videos:
                        # 실제 비디오 강의인지 필터링
                        filtered_videos = []
                        for video in videos:
                            try:
                                # 비디오 아이콘이나 재생 시간이 있는지 확인
                                if (video.find_elements(By.CSS_SELECTOR, "svg, .play-icon, .duration") or
                                    'video' in video.get_attribute('class').lower() or
                                    'video' in video.get_attribute('data-purpose').lower()):
                                    filtered_videos.append(video)
                            except:
                                # 텍스트가 있으면 일단 포함
                                if video.text.strip():
                                    filtered_videos.append(video)

                        if filtered_videos:
                            return filtered_videos
                except:
                    continue

            return []

        except:
            return []

    def _extract_section_title(self, section_element):
        """섹션 제목 추출"""
        try:
            title_selectors = [
                "h3", "h2", "h4",
                ".section-title",
                ".curriculum-section-title",
                "[data-purpose='section-title']",
                "button span",
                "span"
            ]

            for selector in title_selectors:
                try:
                    title_element = section_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title and len(title) > 2:
                        return title
                except:
                    continue

            return "제목 없음"

        except:
            return "제목 없음"

    def _analyze_lecture(self, lecture_element, lecture_idx: int):
        """개별 강의 분석"""
        try:
            # 강의 제목 추출
            title_selectors = [
                ".lecture-name",
                ".curriculum-item-title",
                "span[data-purpose='item-title']",
                ".item-title",
                "span"
            ]

            lecture_title = "강의 제목 없음"
            for selector in title_selectors:
                try:
                    title_element = lecture_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title and len(title) > 2:
                        lecture_title = title
                        break
                except:
                    continue

            # 강의 시간 추출
            duration_selectors = [
                ".curriculum-item-duration",
                ".duration",
                ".lecture-duration",
                "span[class*='duration']"
            ]

            duration = "시간 정보 없음"
            for selector in duration_selectors:
                try:
                    duration_element = lecture_element.find_element(By.CSS_SELECTOR, selector)
                    duration_text = duration_element.text.strip()
                    if duration_text:
                        duration = duration_text
                        break
                except:
                    continue

            # Lecture 객체 생성
            lecture = Lecture(
                title=lecture_title,
                duration=duration,
                lecture_index=lecture_idx
            )

            return lecture

        except Exception as e:
            return None