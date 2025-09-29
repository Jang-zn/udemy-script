"""
트랜스크립트/자막 추출 전담 모듈
"""

import time
from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .selectors import UdemySelectors, ClickStrategies
from .element_finder import ElementFinder, ClickHandler


class TranscriptExtractor:
    """자막/트랜스크립트 추출 전담 클래스"""

    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print
        self.element_finder = ElementFinder(driver, wait, log_callback)
        self.click_handler = ClickHandler(driver, log_callback)

    def extract_transcript_from_video(self) -> Optional[str]:
        """비디오에서 트랜스크립트 추출 (전체 워크플로우)"""
        try:
            self.log_callback("    🎬 비디오 트랜스크립트 추출 시작...")

            # 1. 트랜스크립트 패널 열기
            if not self.open_transcript_panel():
                return None

            # 2. 트랜스크립트 내용 추출
            content = self.extract_transcript_content()

            # 3. 패널 닫기 (선택사항)
            # self.close_transcript_panel()

            return content

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 추출 실패: {str(e)}")
            return None

    def open_transcript_panel(self) -> bool:
        """트랜스크립트 패널 열기"""
        try:
            self.log_callback("    🔍 트랜스크립트 버튼 찾는 중...")

            # 1. 트랜스크립트 버튼 찾기
            transcript_button = self.element_finder.find_transcript_button()
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
            video_area = self.element_finder.find_video_area()
            if video_area:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(video_area).perform()
                delays = ClickStrategies.get_click_delays()
                time.sleep(delays["hover_delay"])

            # 4. 트랜스크립트 버튼 클릭
            self.log_callback("    🖱️ 트랜스크립트 버튼 클릭 중...")
            if not self.click_handler.click_element_with_strategies(transcript_button, scroll_to_view=False):
                self.log_callback("    ❌ 트랜스크립트 버튼 클릭 실패")
                return False

            # 5. 패널 열릴 때까지 대기
            if self._wait_for_panel_open(transcript_button):
                self.log_callback("    ✅ 트랜스크립트 패널 열기 완료")
                return True
            else:
                self.log_callback("    ❌ 트랜스크립트 패널 열기 실패")
                return False

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 패널 열기 중 오류: {str(e)}")
            return False

    def close_transcript_panel(self) -> bool:
        """트랜스크립트 패널 닫기"""
        try:
            self.log_callback("    🔄 트랜스크립트 패널 닫는 중...")

            # 1. 비디오 영역으로 마우스 이동
            video_area = self.element_finder.find_video_area()
            if video_area:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(video_area).perform()
                delays = ClickStrategies.get_click_delays()
                time.sleep(delays["hover_delay"])

            # 2. 트랜스크립트 버튼 찾기
            transcript_button = self.element_finder.find_transcript_button()
            if not transcript_button:
                self.log_callback("    ⚠️ 트랜스크립트 버튼을 찾을 수 없음")
                return False

            # 3. 현재 패널 상태 확인
            is_expanded = transcript_button.get_attribute('aria-expanded') == 'true'
            if not is_expanded:
                self.log_callback("    ℹ️ 트랜스크립트 패널이 이미 닫혀있습니다.")
                return True

            # 4. 패널 닫기
            if self.click_handler.click_element_with_strategies(transcript_button, scroll_to_view=False):
                time.sleep(2)
                self.log_callback("    ✅ 트랜스크립트 패널 닫기 완료")
                return True
            else:
                self.log_callback("    ❌ 트랜스크립트 패널 닫기 실패")
                return False

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 패널 닫기 중 오류: {str(e)}")
            return False

    def extract_transcript_content(self) -> Optional[str]:
        """트랜스크립트 내용 추출"""
        try:
            self.log_callback("    📖 트랜스크립트 내용 추출 중...")
            time.sleep(2)

            # 1. 트랜스크립트 패널 찾기
            transcript_panel = self.element_finder.find_transcript_panel()
            if not transcript_panel:
                self.log_callback("    ❌ 트랜스크립트 패널을 찾을 수 없습니다.")
                return None

            self.log_callback(f"    ✅ 트랜스크립트 패널 발견: {transcript_panel.tag_name}")

            # 2. cue 요소들 찾기
            cue_elements = self._find_transcript_cues(transcript_panel)
            if not cue_elements:
                self.log_callback("    ❌ 트랜스크립트 cue 요소가 없습니다.")
                self._debug_panel_contents(transcript_panel)
                return None

            self.log_callback(f"    📊 트랜스크립트 cue 요소 {len(cue_elements)}개 발견")

            # 3. 텍스트 추출
            transcript_lines = self._extract_text_from_cues(cue_elements)

            if transcript_lines:
                total_text = "\\n".join(transcript_lines)
                self.log_callback(f"    ✅ 트랜스크립트 추출 완료: {len(transcript_lines)}개 항목, 총 {len(total_text)}자")
                return total_text
            else:
                self.log_callback("    ❌ 추출된 텍스트가 없습니다.")
                return None

        except Exception as e:
            self.log_callback(f"    ❌ 트랜스크립트 내용 추출 중 오류: {str(e)}")
            return None

    def _wait_for_panel_open(self, transcript_button) -> bool:
        """패널이 열릴 때까지 대기"""
        try:
            # aria-expanded가 true가 될 때까지 대기
            self.wait.until(
                lambda driver: transcript_button.get_attribute('aria-expanded') == 'true'
            )

            # 패널 콘텐츠가 로드될 때까지 추가 대기
            self.wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    ", ".join(UdemySelectors.TRANSCRIPT_PANELS)
                ))
            )
            return True
        except:
            time.sleep(1)  # 폴백
            return transcript_button.get_attribute('aria-expanded') == 'true'

    def _find_transcript_cues(self, panel_element) -> List:
        """트랜스크립트 cue 요소들 찾기"""
        for selector in UdemySelectors.TRANSCRIPT_CUES:
            try:
                elements = panel_element.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except:
                continue
        return []

    def _extract_text_from_cues(self, cue_elements) -> List[str]:
        """cue 요소들에서 텍스트 추출"""
        transcript_lines = []

        for i, cue_element in enumerate(cue_elements):
            try:
                # 텍스트 요소 찾기
                text_element = self._find_cue_text_element(cue_element)
                if text_element:
                    text = text_element.text.strip()
                    if text:
                        transcript_lines.append(text)
                        if i < 3:  # 처음 3개만 로그
                            self.log_callback(f"      {i+1}. '{text[:30]}...'")
            except Exception as e:
                if i < 3:
                    self.log_callback(f"      ❌ {i+1}번째 cue 추출 실패: {str(e)}")
                continue

        return transcript_lines

    def _find_cue_text_element(self, cue_element):
        """cue 요소에서 텍스트 요소 찾기"""
        for selector in UdemySelectors.TRANSCRIPT_CUE_TEXT:
            try:
                text_element = cue_element.find_element(By.CSS_SELECTOR, selector)
                if text_element:
                    return text_element
            except:
                continue

        # 텍스트 요소를 찾지 못했다면 cue 요소 자체에서 텍스트 추출
        return cue_element

    def _debug_panel_contents(self, panel_element):
        """패널 내용 디버깅"""
        try:
            self.log_callback("    🔍 패널 내용 디버깅:")
            self.log_callback(f"      패널 태그: {panel_element.tag_name}")
            self.log_callback(f"      패널 클래스: {panel_element.get_attribute('class')}")

            # 모든 자식 요소들 확인
            children = panel_element.find_elements(By.CSS_SELECTOR, "*")
            self.log_callback(f"      자식 요소 수: {len(children)}")

            # 처음 5개 자식 요소 정보
            for i, child in enumerate(children[:5]):
                tag = child.tag_name
                classes = child.get_attribute('class') or 'no-class'
                data_purpose = child.get_attribute('data-purpose') or 'no-data-purpose'
                text_preview = child.text[:50] if child.text else 'no-text'
                self.log_callback(f"        {i+1}. {tag}.{classes} [{data_purpose}]: {text_preview}")

        except Exception as e:
            self.log_callback(f"    ❌ 디버깅 중 오류: {str(e)}")


class VideoNavigator:
    """비디오 탐색 및 로딩 관리 클래스"""

    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print

    def wait_for_video_page_load(self) -> bool:
        """비디오 페이지 로딩 대기"""
        try:
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
                        ", ".join(UdemySelectors.VIDEO_AREAS)
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