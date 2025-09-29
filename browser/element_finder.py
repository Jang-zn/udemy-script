"""
UI 요소 찾기 및 상호작용 유틸리티 모듈
"""

import time
from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from .selectors import UdemySelectors, ClickStrategies


class ElementFinder:
    """UI 요소 찾기 및 상호작용을 담당하는 클래스"""

    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print

    def find_transcript_button(self) -> Optional:
        """트랜스크립트 버튼 찾기 (호버 상태 유지)"""
        try:
            delays = ClickStrategies.get_click_delays()

            # 페이지 로딩 대기
            time.sleep(delays["page_load"])

            # 비디오 영역 찾기
            video_area = self.find_video_area()
            if not video_area:
                return None

            actions = ActionChains(self.driver)

            # 비디오 영역에 마우스 이동하고 호버 상태 유지
            actions.move_to_element(video_area).perform()
            time.sleep(delays["hover_delay"])

            # 여러 번 시도 (컨트롤바가 안정화될 때까지)
            for attempt in range(3):
                # 호버 상태 재설정
                actions.move_to_element(video_area).perform()
                time.sleep(delays["hover_delay"])

                for selector in UdemySelectors.TRANSCRIPT_BUTTONS:
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

    def find_video_area(self) -> Optional:
        """비디오 영역 찾기"""
        try:
            for selector in UdemySelectors.VIDEO_AREAS:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        return element
                except:
                    continue
            return None
        except Exception:
            return None

    def find_transcript_panel(self) -> Optional:
        """트랜스크립트 패널 찾기"""
        try:
            for selector in UdemySelectors.TRANSCRIPT_PANELS:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        return element
                except:
                    continue
            return None
        except Exception:
            return None


class ClickHandler:
    """클릭 작업을 담당하는 클래스"""

    def __init__(self, driver, log_callback=None):
        self.driver = driver
        self.log_callback = log_callback or print

    def click_element_with_strategies(self, element, scroll_to_view=True) -> bool:
        """여러 전략으로 요소 클릭 시도"""
        try:
            delays = ClickStrategies.get_click_delays()

            if scroll_to_view:
                self._scroll_to_element(element)
                time.sleep(delays["after_scroll"])

            # 전략 1: ActionChains로 클릭
            if self._try_action_chains_click(element):
                time.sleep(delays["after_click"])
                return True

            # 전략 2: 일반 클릭
            if self._try_normal_click(element):
                time.sleep(delays["after_click"])
                return True

            # 전략 3: JavaScript 클릭
            if self._try_javascript_click(element):
                time.sleep(delays["after_click"])
                return True

            return False

        except Exception:
            return False

    def click_lecture_item(self, video_element) -> bool:
        """강의 아이템 클릭 (강화된 로직)"""
        try:
            # 현재 재생 중인지 확인
            is_current = video_element.get_attribute("aria-current") == "true"
            if is_current:
                return True

            # 모든 클릭 가능한 요소들을 찾아서 시도
            for selector in UdemySelectors.LECTURE_CLICKABLE_ELEMENTS:
                try:
                    elements = video_element.find_elements(By.CSS_SELECTOR, selector)
                    for clickable in elements:
                        if clickable.is_displayed() and clickable.is_enabled():
                            if self.click_element_with_strategies(clickable):
                                return True
                except:
                    continue

            # 요소 자체에 직접 클릭 시도
            return self.click_element_with_strategies(video_element)

        except Exception:
            return False

    def _scroll_to_element(self, element):
        """요소를 화면 중앙으로 스크롤"""
        try:
            scroll_options = ClickStrategies.get_scroll_options()
            self.driver.execute_script(
                "arguments[0].scrollIntoView(arguments[1]);",
                element,
                scroll_options
            )
        except:
            pass

    def _try_action_chains_click(self, element) -> bool:
        """ActionChains로 클릭 시도"""
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(element).click().perform()
            return True
        except:
            return False

    def _try_normal_click(self, element) -> bool:
        """일반 클릭 시도"""
        try:
            element.click()
            return True
        except:
            return False

    def _try_javascript_click(self, element) -> bool:
        """JavaScript 클릭 시도"""
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            return False


class SectionNavigator:
    """섹션 탐색을 담당하는 클래스"""

    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print
        self.click_handler = ClickHandler(driver, log_callback)

    def open_section_accordion(self, section_idx: int) -> bool:
        """섹션 아코디언 열기"""
        try:
            self.log_callback(f"📂 섹션 {section_idx + 1} 아코디언 열기...")

            # 섹션 패널 찾기
            section_element = self._find_section_panel(section_idx)
            if not section_element:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 패널을 찾을 수 없음")
                return False

            self.log_callback(f"✅ 섹션 패널 발견: {section_element.tag_name}")

            # 섹션이 이미 열려있는지 확인
            if self._is_section_expanded(section_element):
                self.log_callback(f"✅ 섹션 {section_idx + 1}이 이미 열려있음")
                return True

            # 섹션 버튼 찾기 및 클릭
            section_button = self._find_section_button(section_element, section_idx)
            if not section_button:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 버튼을 찾을 수 없음")
                return False

            # 클릭 시도
            if self.click_handler.click_element_with_strategies(section_button):
                self.log_callback(f"🔓 섹션 {section_idx + 1} 아코디언 열기 중...")
                time.sleep(2)  # 아코디언 애니메이션 대기

                # 콘텐츠 로딩 대기
                if self._wait_for_section_content(section_idx):
                    self.log_callback(f"✅ 섹션 {section_idx + 1} 아코디언 열림 및 콘텐츠 로드 완료")
                    return True
                else:
                    self.log_callback(f"⚠️ 섹션 {section_idx + 1} 콘텐츠 로딩 실패")
                    return False
            else:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 버튼 클릭 실패")
                return False

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 아코디언 열기 실패: {str(e)}")
            return False

    def _find_section_panel(self, section_idx: int):
        """섹션 패널 찾기"""
        selectors = [
            f"div[data-purpose='section-panel-{section_idx}']",
            f"div[data-purpose='section-panel-{section_idx + 1}']",
            f"div[data-purpose^='section-panel-']:nth-child({section_idx + 1})",
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

    def _find_section_button(self, section_element, section_idx: int):
        """섹션 버튼 찾기"""
        button_selectors = [
            f"button[data-purpose='section-panel-{section_idx}']",
            f"button[data-purpose='section-panel-{section_idx + 1}']",
            "button",
            ".section-title-button",
            ".curriculum-section-title-button"
        ]

        for selector in button_selectors:
            try:
                button = section_element.find_element(By.CSS_SELECTOR, selector)
                if button and button.is_displayed():
                    return button
            except:
                continue

        return None

    def _is_section_expanded(self, section_element) -> bool:
        """섹션이 열려있는지 확인"""
        try:
            # aria-expanded 확인
            aria_expanded = section_element.get_attribute("aria-expanded")
            if aria_expanded == "true":
                return True

            # 버튼의 aria-expanded 확인
            try:
                button = section_element.find_element(By.CSS_SELECTOR, "button")
                button_expanded = button.get_attribute("aria-expanded")
                if button_expanded == "true":
                    return True
            except:
                pass

            return False
        except:
            return False

    def _wait_for_section_content(self, section_idx: int) -> bool:
        """섹션 콘텐츠 로딩 대기"""
        try:
            # 강의 아이템들이 나타날 때까지 대기
            content_selectors = [
                f"div[data-purpose='section-panel-{section_idx}'] [data-purpose^='curriculum-item-lecture-']",
                f"div[data-purpose='section-panel-{section_idx + 1}'] [data-purpose^='curriculum-item-lecture-']",
                ".curriculum-item-link"
            ]

            for selector in content_selectors:
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    return True
                except:
                    continue

            return False
        except:
            return False