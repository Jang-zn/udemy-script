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
        # 순환 import 방지를 위해 lazy import
        self._smart_waiter = None

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

                # 스마트 대기: 아코디언이 실제로 열릴 때까지 대기
                if self._wait_for_section_expand_smart(section_element, section_idx):
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
        """섹션 패널 찾기 (개선된 로직)"""
        selectors = [
            # 정확한 data-purpose 매칭
            f"div[data-purpose='section-panel-{section_idx}']",
            f"div[data-purpose='section-panel-{section_idx + 1}']",

            # nth-child 선택자들
            f"div[data-purpose^='section-panel-']:nth-child({section_idx + 1})",
            f".curriculum-section:nth-child({section_idx + 1})",
            f"section:nth-child({section_idx + 1})",

            # 클래스 기반 선택자들
            f".curriculum-section:nth-of-type({section_idx + 1})",
            f".section-panel:nth-of-type({section_idx + 1})",

            # 광범위한 선택자들
            f"*[data-purpose^='section-panel-']:nth-child({section_idx + 1})",
            f"*[class*='section']:nth-child({section_idx + 1})"
        ]

        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.is_displayed():
                    self.log_callback(f"✅ 섹션 패널 발견: {selector}")
                    return element
            except:
                continue

        # 모든 섹션 패널을 찾아서 인덱스로 선택
        try:
            all_sections = self.driver.find_elements(By.CSS_SELECTOR, "div[data-purpose^='section-panel-'], .curriculum-section")
            if section_idx < len(all_sections):
                element = all_sections[section_idx]
                if element and element.is_displayed():
                    self.log_callback(f"✅ 섹션 패널 인덱스로 발견: {section_idx}")
                    return element
        except:
            pass

        return None

    def _find_section_button(self, section_element, section_idx: int):
        """섹션 버튼 찾기 (개선된 로직)"""
        button_selectors = [
            f"button[data-purpose='section-panel-{section_idx}']",
            f"button[data-purpose='section-panel-{section_idx + 1}']",
            "button[aria-expanded]",
            "button",
            ".section-title-button",
            ".curriculum-section-title-button",
            "h3 button",
            ".section-header button",
            "[role='button']"
        ]

        for selector in button_selectors:
            try:
                buttons = section_element.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button and button.is_displayed() and button.is_enabled():
                        # 버튼이 실제 섹션 제어 버튼인지 확인
                        if self._is_section_control_button(button, section_idx):
                            return button
            except:
                continue

        return None

    def _is_section_control_button(self, button, section_idx: int) -> bool:
        """버튼이 섹션 제어 버튼인지 확인"""
        try:
            # aria-expanded 속성이 있는 버튼 우선
            if button.get_attribute("aria-expanded") is not None:
                return True

            # data-purpose에 section이 포함된 버튼
            data_purpose = button.get_attribute("data-purpose") or ""
            if "section" in data_purpose.lower():
                return True

            # 클래스명에 section이 포함된 버튼
            class_name = button.get_attribute("class") or ""
            if "section" in class_name.lower():
                return True

            # 버튼 텍스트나 부모 요소에서 섹션 정보 확인
            button_text = button.text.strip()
            if button_text and ("섹션" in button_text or "Section" in button_text):
                return True

            return False
        except:
            return False

    def _is_section_expanded(self, section_element) -> bool:
        """섹션이 열려있는지 확인 (개선된 로직)"""
        try:
            # 1. 섹션 요소 자체의 aria-expanded 확인
            aria_expanded = section_element.get_attribute("aria-expanded")
            if aria_expanded == "true":
                return True

            # 2. 모든 버튼의 aria-expanded 확인
            try:
                buttons = section_element.find_elements(By.CSS_SELECTOR, "button")
                for button in buttons:
                    button_expanded = button.get_attribute("aria-expanded")
                    if button_expanded == "true":
                        return True
            except:
                pass

            # 3. 클래스명으로 확장 상태 확인
            try:
                class_name = section_element.get_attribute("class") or ""
                if "expanded" in class_name.lower() or "open" in class_name.lower():
                    return True
            except:
                pass

            # 4. 자식 콘텐츠가 보이는지 확인 (실제 콘텐츠 요소들)
            try:
                content_selectors = [
                    "[data-purpose*='curriculum-item']",
                    ".curriculum-item",
                    "a[href*='lecture']"
                ]

                for selector in content_selectors:
                    elements = section_element.find_elements(By.CSS_SELECTOR, selector)
                    visible_elements = [elem for elem in elements if elem.is_displayed()]
                    if visible_elements:
                        return True
            except:
                pass

            # 5. data-state 속성 확인
            try:
                data_state = section_element.get_attribute("data-state")
                if data_state == "open" or data_state == "expanded":
                    return True
            except:
                pass

            return False
        except:
            return False

    def _debug_section_expansion(self, section_element, section_idx: int):
        """섹션 확장 디버깅 정보 출력"""
        try:
            self.log_callback(f"    🔍 섹션 {section_idx + 1} 디버깅 정보:")

            # 기본 속성들
            aria_expanded = section_element.get_attribute("aria-expanded")
            class_name = section_element.get_attribute("class") or ""
            data_state = section_element.get_attribute("data-state") or ""

            self.log_callback(f"       aria-expanded: {aria_expanded}")
            self.log_callback(f"       class: {class_name[:100]}...")
            self.log_callback(f"       data-state: {data_state}")

            # 버튼 상태 확인
            buttons = section_element.find_elements(By.CSS_SELECTOR, "button")
            self.log_callback(f"       버튼 개수: {len(buttons)}")
            for i, button in enumerate(buttons[:3]):  # 처음 3개만
                btn_expanded = button.get_attribute("aria-expanded")
                btn_class = button.get_attribute("class") or ""
                self.log_callback(f"       버튼{i+1}: aria-expanded={btn_expanded}, class={btn_class[:50]}...")

            # 콘텐츠 요소 확인
            content_count = len(section_element.find_elements(By.CSS_SELECTOR, "[data-purpose*='curriculum-item']"))
            visible_content_count = len([elem for elem in section_element.find_elements(By.CSS_SELECTOR, "[data-purpose*='curriculum-item']") if elem.is_displayed()])

            self.log_callback(f"       콘텐츠 요소: 총 {content_count}개, 보이는 것 {visible_content_count}개")

        except Exception as e:
            self.log_callback(f"       디버깅 실패: {str(e)}")

    def _wait_for_section_expand_smart(self, section_element, section_idx: int, max_wait_seconds=10) -> bool:
        """섹션이 실제로 열릴 때까지 스마트 대기 (개선된 로직)"""
        try:
            import time
            self.log_callback(f"    ⏳ 섹션 {section_idx + 1} 확장 대기 중...")

            # 즉시 상태 확인 (이미 열려있을 수 있음)
            if self._is_section_expanded(section_element) and self._has_visible_content(section_element, section_idx):
                self.log_callback(f"    ✅ 섹션 {section_idx + 1}이 이미 확장되어 있음")
                return True

            start_time = time.time()
            attempt = 0

            while time.time() - start_time < max_wait_seconds:
                try:
                    attempt += 1

                    # 1. aria-expanded 상태 확인
                    is_expanded = self._is_section_expanded(section_element)
                    has_content = self._has_visible_content(section_element, section_idx)

                    if attempt % 5 == 0 or attempt <= 3:  # 처음 3번과 5번마다 상태 로그
                        self.log_callback(f"    🔄 시도 {attempt}: expanded={is_expanded}, content={has_content}")

                    if is_expanded and has_content:
                        self.log_callback(f"    ✅ 섹션 {section_idx + 1} 확장 및 콘텐츠 로딩 완료 (시도 {attempt})")
                        return True

                    # 콘텐츠가 없다면 더 자세한 디버깅
                    if is_expanded and not has_content and attempt == 5:
                        self._debug_section_expansion(section_element, section_idx)

                    time.sleep(0.5)  # 조금 더 긴 간격

                except Exception as inner_e:
                    self.log_callback(f"    🔄 시도 {attempt} 섹션 상태 확인 중... ({str(inner_e)[:30]})")
                    time.sleep(0.5)

            self.log_callback(f"    ❌ 섹션 {section_idx + 1} 확장 대기 시간 초과 (총 {attempt}번 시도)")

            # 마지막으로 한 번 더 상태 확인 및 강제 통과 검토
            final_expanded = self._is_section_expanded(section_element)
            final_content = self._has_visible_content(section_element, section_idx)
            self.log_callback(f"    📊 최종 상태: expanded={final_expanded}, content={final_content}")

            # aria-expanded가 true라면 콘텐츠가 없어도 통과 (빈 섹션일 수 있음)
            if final_expanded:
                self.log_callback(f"    ⚠️ 섹션이 열렸지만 콘텐츠 미확인 - 통과 처리")
                return True

            return False

        except Exception as e:
            self.log_callback(f"    ❌ 섹션 확장 대기 실패: {str(e)}")
            return False

    def _has_visible_content(self, section_element, section_idx: int) -> bool:
        """섹션에 실제 보이는 콘텐츠가 있는지 확인"""
        try:
            # 다양한 콘텐츠 셀렉터로 확인
            content_selectors = [
                "[data-purpose*='curriculum-item']",
                ".curriculum-item",
                "a[href*='lecture']",
                "button[aria-label*='재생']",
                "*[title*='분']"
            ]

            for selector in content_selectors:
                try:
                    elements = section_element.find_elements(By.CSS_SELECTOR, selector)
                    visible_elements = [elem for elem in elements if elem.is_displayed()]
                    if visible_elements:
                        return True
                except:
                    continue

            return False

        except:
            return False

    def _wait_for_section_content(self, section_idx: int) -> bool:
        """섹션 콘텐츠 로딩 대기 (기존 방식 - 호환성용)"""
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