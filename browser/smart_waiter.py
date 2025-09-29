"""
스마트 대기 시스템 - sleep 대신 실제 DOM 상태 변화를 감지
"""

import time
from typing import Optional, Callable, List, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .selectors import UdemySelectors


class SmartWaiter:
    """DOM 상태 변화를 감지하는 스마트 대기 시스템"""

    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print

    def wait_for_transcript_panel_close(self, transcript_button, max_wait_seconds=10) -> bool:
        """트랜스크립트 패널이 닫힐 때까지 대기"""
        try:
            self.log_callback("    ⏳ 트랜스크립트 패널 닫힘 대기 중...")

            # 1. aria-expanded가 false가 될 때까지 대기
            start_time = time.time()
            while time.time() - start_time < max_wait_seconds:
                try:
                    is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
                    if not is_expanded:
                        self.log_callback("    ✅ 트랜스크립트 패널이 닫혔습니다")
                        break
                    time.sleep(0.2)
                except:
                    time.sleep(0.2)
            else:
                self.log_callback("    ⚠️ 트랜스크립트 패널 닫힘 대기 시간 초과")
                return False

            # 2. 섹션 영역이 다시 나타날 때까지 대기
            return self.wait_for_section_area_visible()

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 패널 닫힘 대기 실패: {str(e)}")
            return False

    def wait_for_section_area_visible(self, max_wait_seconds=10) -> bool:
        """섹션 영역이 보일 때까지 대기"""
        try:
            self.log_callback("    ⏳ 섹션 영역 로딩 대기 중...")

            # 섹션 관련 요소들이 나타날 때까지 대기
            section_indicators = [
                "[data-purpose^='section-panel-']",
                ".curriculum-section",
                "[data-purpose^='curriculum-item-lecture-']",
                ".curriculum-item-link"
            ]

            start_time = time.time()
            while time.time() - start_time < max_wait_seconds:
                for selector in section_indicators:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements and any(elem.is_displayed() for elem in elements):
                            self.log_callback("    ✅ 섹션 영역이 준비되었습니다")
                            return True
                    except:
                        continue
                time.sleep(0.3)

            self.log_callback("    ⚠️ 섹션 영역 로딩 대기 시간 초과")
            return False

        except Exception as e:
            self.log_callback(f"    ❌ 섹션 영역 대기 실패: {str(e)}")
            return False

    def wait_for_next_lecture_clickable(self, current_lecture_idx: int, section_content, max_wait_seconds=15) -> bool:
        """다음 강의가 클릭 가능해질 때까지 대기 (개선된 로직)"""
        try:
            next_lecture_idx = current_lecture_idx + 1
            self.log_callback(f"    ⏳ 다음 강의({next_lecture_idx + 1}) 클릭 가능 상태 대기 중...")

            # 즉시 한 번 확인 (이미 준비되어 있을 수 있음)
            lecture_elements = self._find_fresh_lecture_elements(section_content)
            self.log_callback(f"    🔍 현재 발견된 강의 수: {len(lecture_elements) if lecture_elements else 0}")

            if lecture_elements and len(lecture_elements) > next_lecture_idx:
                next_lecture = lecture_elements[next_lecture_idx]
                if self._is_lecture_clickable(next_lecture):
                    self.log_callback(f"    ✅ 다음 강의({next_lecture_idx + 1})가 이미 클릭 가능합니다")
                    return True
                else:
                    # 클릭 불가능한 이유 디버깅
                    self._debug_lecture_clickability(next_lecture, next_lecture_idx)

            # 아직 준비되지 않았다면 대기
            start_time = time.time()
            attempt = 0
            while time.time() - start_time < max_wait_seconds:
                try:
                    attempt += 1
                    # 강의 목록 다시 찾기
                    lecture_elements = self._find_fresh_lecture_elements(section_content)

                    if not lecture_elements:
                        self.log_callback(f"    🔄 시도 {attempt}: 강의 목록을 찾을 수 없음")
                        time.sleep(1)
                        continue

                    if len(lecture_elements) <= next_lecture_idx:
                        self.log_callback(f"    🔄 시도 {attempt}: 강의 {next_lecture_idx + 1}번이 목록에 없음 ({len(lecture_elements)}개만 발견)")
                        time.sleep(1)
                        continue

                    next_lecture = lecture_elements[next_lecture_idx]

                    # 다음 강의가 클릭 가능한지 확인
                    if self._is_lecture_clickable(next_lecture):
                        self.log_callback(f"    ✅ 다음 강의({next_lecture_idx + 1})가 클릭 가능합니다 (시도 {attempt})")
                        return True

                    if attempt % 5 == 0:  # 5번마다 상태 로그
                        self.log_callback(f"    🔄 시도 {attempt}: 강의 {next_lecture_idx + 1}번 아직 클릭 불가")

                    time.sleep(1)

                except Exception as inner_e:
                    self.log_callback(f"    🔄 시도 {attempt} 강의 상태 확인 중... ({str(inner_e)[:50]})")
                    time.sleep(1)

            self.log_callback("    ⚠️ 다음 강의 클릭 가능 상태 대기 시간 초과")
            return False

        except Exception as e:
            self.log_callback(f"    ❌ 다음 강의 대기 실패: {str(e)}")
            return False

    def wait_for_transcript_panel_open(self, transcript_button, max_wait_seconds=10) -> bool:
        """트랜스크립트 패널이 열릴 때까지 대기"""
        try:
            self.log_callback("    ⏳ 트랜스크립트 패널 열림 대기 중...")

            start_time = time.time()
            while time.time() - start_time < max_wait_seconds:
                try:
                    # 1. aria-expanded 상태 확인
                    is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
                    if is_expanded:
                        # 2. 실제 패널 콘텐츠가 로드되었는지 확인
                        if self._is_transcript_content_loaded():
                            self.log_callback("    ✅ 트랜스크립트 패널이 완전히 열렸습니다")
                            return True

                    time.sleep(0.3)

                except:
                    time.sleep(0.3)

            self.log_callback("    ⚠️ 트랜스크립트 패널 열림 대기 시간 초과")
            return False

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 패널 열림 대기 실패: {str(e)}")
            return False

    def wait_for_video_page_ready(self, max_wait_seconds=15) -> bool:
        """비디오 페이지가 완전히 로드될 때까지 대기"""
        try:
            self.log_callback("    ⏳ 비디오 페이지 로딩 대기 중...")

            # 1. URL이 lecture를 포함할 때까지 대기
            start_time = time.time()
            while time.time() - start_time < 5:
                if 'lecture' in self.driver.current_url:
                    break
                time.sleep(0.5)
            else:
                self.log_callback("    ⚠️ 강의 URL로 변경되지 않음")
                return False

            # 2. 비디오 플레이어나 강의 콘텐츠가 로드될 때까지 대기
            remaining_time = max_wait_seconds - (time.time() - start_time)
            if remaining_time <= 0:
                return False

            content_loaded = False
            content_start_time = time.time()

            while time.time() - content_start_time < remaining_time:
                # 비디오 플레이어 확인
                if self._is_video_player_ready():
                    content_loaded = True
                    break

                # 문서 강의 확인
                if self._is_document_content_ready():
                    content_loaded = True
                    break

                time.sleep(0.5)

            if content_loaded:
                # 3. 추가 안정화 대기 (DOM이 완전히 안정될 때까지)
                time.sleep(1)
                self.log_callback("    ✅ 비디오 페이지가 완전히 로드되었습니다")
                return True
            else:
                self.log_callback("    ⚠️ 비디오 페이지 콘텐츠 로딩 실패")
                return False

        except Exception as e:
            self.log_callback(f"    ❌ 비디오 페이지 대기 실패: {str(e)}")
            return False

    def wait_for_element_stable(self, element, stable_duration=1.0, max_wait=10) -> bool:
        """요소가 안정적인 상태가 될 때까지 대기"""
        try:
            start_time = time.time()
            last_change_time = start_time

            previous_state = self._get_element_state(element)

            while time.time() - start_time < max_wait:
                current_state = self._get_element_state(element)

                if current_state != previous_state:
                    last_change_time = time.time()
                    previous_state = current_state

                # 안정적인 시간이 경과했으면 완료
                if time.time() - last_change_time >= stable_duration:
                    return True

                time.sleep(0.2)

            return False

        except:
            return False

    # === Private Methods ===

    def _find_fresh_lecture_elements(self, section_content):
        """섹션에서 최신 강의 요소들 찾기"""
        for selector in UdemySelectors.LECTURE_ITEMS:
            try:
                elements = section_content.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except:
                continue
        return []

    def _is_lecture_clickable(self, lecture_element) -> bool:
        """강의가 클릭 가능한 상태인지 확인"""
        try:
            # 요소가 표시되고 활성화되어 있는지 확인
            if not lecture_element.is_displayed() or not lecture_element.is_enabled():
                return False

            # 클릭 가능한 하위 요소가 있는지 확인
            clickable_selectors = ["a", "button", ".item-link", "[data-purpose^='curriculum-item']"]
            for selector in clickable_selectors:
                try:
                    clickable = lecture_element.find_element(By.CSS_SELECTOR, selector)
                    if clickable.is_displayed() and clickable.is_enabled():
                        return True
                except:
                    continue

            return True  # 하위 요소가 없어도 자체적으로 클릭 가능할 수 있음

        except:
            return False

    def _is_transcript_content_loaded(self) -> bool:
        """트랜스크립트 콘텐츠가 로드되었는지 확인"""
        try:
            for selector in UdemySelectors.TRANSCRIPT_PANELS:
                try:
                    panel = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if panel.is_displayed():
                        # cue 요소들이 있는지 확인
                        cues = panel.find_elements(By.CSS_SELECTOR, "[data-purpose='transcript-cue']")
                        return len(cues) > 0
                except:
                    continue
            return False
        except:
            return False

    def _is_video_player_ready(self) -> bool:
        """비디오 플레이어가 준비되었는지 확인"""
        try:
            for selector in UdemySelectors.VIDEO_AREAS:
                try:
                    video = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if video.is_displayed():
                        return True
                except:
                    continue
            return False
        except:
            return False

    def _is_document_content_ready(self) -> bool:
        """문서 콘텐츠가 준비되었는지 확인"""
        try:
            document_selectors = [
                ".lecture-view",
                ".lecture-content",
                "[data-purpose='lecture-content']"
            ]

            for selector in document_selectors:
                try:
                    content = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if content.is_displayed():
                        return True
                except:
                    continue
            return False
        except:
            return False

    def _get_element_state(self, element) -> dict:
        """요소의 현재 상태를 가져오기"""
        try:
            return {
                'displayed': element.is_displayed(),
                'enabled': element.is_enabled(),
                'location': element.location,
                'size': element.size,
                'text': element.text[:100]  # 텍스트 일부만
            }
        except:
            return {'error': True}


class StateMonitor:
    """페이지 상태 모니터링 클래스"""

    def __init__(self, driver, log_callback=None):
        self.driver = driver
        self.log_callback = log_callback or print

    def monitor_page_transition(self, from_state: str, to_state: str, max_wait=15) -> bool:
        """페이지 전환 모니터링"""
        try:
            self.log_callback(f"    🔄 페이지 전환 모니터링: {from_state} → {to_state}")

            start_time = time.time()
            transition_detected = False

            while time.time() - start_time < max_wait:
                current_state = self._detect_current_page_state()

                if not transition_detected and current_state != from_state:
                    transition_detected = True
                    self.log_callback(f"    🔄 전환 시작됨: {current_state}")

                if current_state == to_state:
                    self.log_callback(f"    ✅ 페이지 전환 완료: {to_state}")
                    return True

                time.sleep(0.5)

            self.log_callback(f"    ⚠️ 페이지 전환 시간 초과")
            return False

        except Exception as e:
            self.log_callback(f"    ❌ 페이지 전환 모니터링 실패: {str(e)}")
            return False

    def _detect_current_page_state(self) -> str:
        """현재 페이지 상태 감지"""
        try:
            url = self.driver.current_url

            if 'lecture' in url:
                # 트랜스크립트 패널이 열려있는지 확인
                try:
                    transcript_button = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button[data-purpose='transcript-toggle']"
                    )
                    is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
                    return 'lecture_with_transcript' if is_expanded else 'lecture_normal'
                except:
                    return 'lecture_normal'

            elif 'course' in url:
                return 'course_overview'

            else:
                return 'unknown'

        except:
            return 'unknown'

    def _debug_lecture_clickability(self, lecture_element, lecture_idx: int):
        """강의 클릭 가능성 디버깅"""
        try:
            self.log_callback(f"    🔍 강의 {lecture_idx + 1} 클릭 가능성 디버깅:")
            self.log_callback(f"      태그: {lecture_element.tag_name}")
            self.log_callback(f"      displayed: {lecture_element.is_displayed()}")
            self.log_callback(f"      enabled: {lecture_element.is_enabled()}")

            # 속성 정보
            classes = lecture_element.get_attribute('class') or 'None'
            href = lecture_element.get_attribute('href') or 'None'
            data_purpose = lecture_element.get_attribute('data-purpose') or 'None'
            aria_label = lecture_element.get_attribute('aria-label') or 'None'

            self.log_callback(f"      class: {classes[:50]}")
            self.log_callback(f"      href: {href[:50]}")
            self.log_callback(f"      data-purpose: {data_purpose}")
            self.log_callback(f"      aria-label: {aria_label[:50]}")

            # 텍스트 내용
            text = lecture_element.text[:100] if lecture_element.text else 'None'
            self.log_callback(f"      text: {text}")

            # 클릭 가능한 하위 요소 확인
            clickable_children = lecture_element.find_elements(By.CSS_SELECTOR, "a, button")
            self.log_callback(f"      클릭 가능한 하위 요소 수: {len(clickable_children)}")

        except Exception as e:
            self.log_callback(f"      ❌ 디버깅 실패: {str(e)}")