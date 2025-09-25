"""
브라우저 작업을 위한 공통 베이스 클래스
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BrowserBase:
    """모든 브라우저 작업 클래스의 베이스 클래스"""

    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print

    def human_like_typing(self, element, text):
        """인간처럼 타이핑 시뮬레이션"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def human_like_click(self, element):
        """인간처럼 클릭 시뮬레이션"""
        time.sleep(random.uniform(0.5, 1.0))
        element.click()
        time.sleep(random.uniform(0.5, 1.5))

    def wait_for_element(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """요소 대기"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            return None

    def wait_for_clickable_element(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """클릭 가능한 요소 대기"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((by, selector)))
        except TimeoutException:
            return None

    def find_element_safe(self, selector, by=By.CSS_SELECTOR):
        """안전한 요소 찾기 (예외 없이)"""
        try:
            return self.driver.find_element(by, selector)
        except NoSuchElementException:
            return None

    def find_elements_safe(self, selector, by=By.CSS_SELECTOR):
        """안전한 요소들 찾기 (예외 없이)"""
        try:
            return self.driver.find_elements(by, selector)
        except:
            return []

    def try_click_with_selectors(self, selectors, element_name="요소"):
        """여러 선택자로 클릭 시도"""
        for i, selector in enumerate(selectors):
            try:
                self.log_callback(f"🔍 {element_name} 클릭 시도 {i+1}/{len(selectors)}: {selector}")

                if selector.startswith("//"):
                    elements = self.find_elements_safe(selector, By.XPATH)
                else:
                    elements = self.find_elements_safe(selector, By.CSS_SELECTOR)

                for j, element in enumerate(elements):
                    if element and element.is_displayed() and element.is_enabled():
                        try:
                            self.human_like_click(element)
                            self.log_callback(f"✅ {element_name} 클릭 완료")
                            return True
                        except Exception as e:
                            self.log_callback(f"   요소 {j+1} 클릭 실패: {str(e)}")
                            continue

            except Exception as e:
                self.log_callback(f"   선택자 {i+1} 실패: {str(e)}")
                continue

        self.log_callback(f"❌ 모든 {element_name} 선택자 실패")
        return False

    def extract_text_with_selectors(self, container, selectors, default_text="텍스트 없음"):
        """여러 선택자로 텍스트 추출 시도"""
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    element = container.find_element(By.XPATH, selector)
                else:
                    element = container.find_element(By.CSS_SELECTOR, selector)

                text = element.text.strip()
                if text:
                    return text
            except:
                continue

        return default_text

    def scroll_to_element(self, element):
        """요소로 스크롤"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
        except Exception as e:
            self.log_callback(f"⚠️ 스크롤 실패: {str(e)}")

    def scroll_to_top(self):
        """페이지 상단으로 스크롤"""
        try:
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception as e:
            self.log_callback(f"⚠️ 상단 스크롤 실패: {str(e)}")

    def wait_for_page_load(self, expected_url_part=None, timeout=10):
        """페이지 로딩 대기"""
        try:
            if expected_url_part:
                for i in range(timeout):
                    if expected_url_part in self.driver.current_url:
                        time.sleep(1)  # 추가 안정화 시간
                        return True
                    time.sleep(1)
                return False
            else:
                time.sleep(2)  # 기본 대기
                return True
        except:
            return False

    def get_page_info(self):
        """현재 페이지 정보 반환"""
        try:
            return {
                'url': self.driver.current_url,
                'title': self.driver.title
            }
        except:
            return {'url': 'unknown', 'title': 'unknown'}