"""
Udemy 강의 검색 및 선택 모듈
"""

import time
import re
from typing import Optional, List
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from config import Config
from core.models import Course, Section, Lecture
from .base import BrowserBase


class CourseFinder(BrowserBase):
    def __init__(self, driver, wait, log_callback=None):
        super().__init__(driver, wait, log_callback)

    def go_to_my_learning(self) -> bool:
        """로그인 상태 확인하고 '내 학습' 페이지로 이동"""
        try:
            self.log_callback("🔍 로그인 상태 확인 중...")

            # 1. 먼저 로그인 상태 확인
            if not self._check_login_status():
                self.log_callback("❌ 로그인이 필요합니다!")
                self.log_callback("💡 브라우저에서 수동으로 로그인 후 다시 시도하세요.")
                return False

            self.log_callback("✅ 로그인 상태 확인됨")
            self.log_callback("📚 '내 학습' 페이지로 이동 중...")

            # 2. 이미 My Learning 페이지에 있는지 확인
            current_url = self.driver.current_url
            if 'my-courses' in current_url or 'my-learning' in current_url:
                self.log_callback("✅ 이미 내 학습 페이지에 있습니다")
                return True

            # 3. 드롭다운 메뉴 또는 직접 링크에서 "내 학습" 버튼 찾아서 클릭
            my_learning_selectors = [
                # 사용자가 제공한 실제 HTML 기준 선택자들
                "a[href='/home/my-courses/'][data-testid='my-courses']",
                "a[data-testid='my-courses']",
                "a[href='/home/my-courses/']",

                # XPath 선택자들 (CSS :contains 대신)
                "//a[contains(text(), '내 학습')]",
                "//a[contains(text(), 'My learning')]",
                "//a[contains(@href, '/home/my-courses')]",
                "//span[contains(text(), '내 학습')]/..",
                "//span[contains(text(), '내 학습으로 이동')]/..",

                # 헤더의 직접 링크들
                "[data-purpose='my-learning-nav']",
                ".header-my-learning",
                "a[href*='my-courses']",
                ".ud-btn[href='/home/my-courses/']"
            ]

            button_clicked = False
            for i, selector in enumerate(my_learning_selectors):
                try:
                    self.log_callback(f"🔍 시도 {i+1}/{len(my_learning_selectors)}: {selector}")

                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    self.log_callback(f"   발견된 요소 수: {len(elements)}")

                    for j, button in enumerate(elements):
                        if button and button.is_displayed() and button.is_enabled():
                            try:
                                self.log_callback(f"   요소 {j+1} 클릭 시도 중...")
                                button.click()
                                self.log_callback("✅ '내 학습' 버튼 클릭 완료")
                                button_clicked = True
                                break
                            except Exception as click_error:
                                self.log_callback(f"   클릭 실패: {str(click_error)}")
                                continue

                    if button_clicked:
                        break

                except Exception as e:
                    self.log_callback(f"   ❌ 선택자 실패: {str(e)}")
                    continue

            if not button_clicked:
                # 페이지 정보 출력
                self.log_callback("❌ 모든 '내 학습' 버튼 선택자 실패")
                self.log_callback(f"🔍 현재 URL: {self.driver.current_url}")
                self.log_callback(f"🔍 페이지 제목: {self.driver.title}")

                # 페이지에 있는 모든 링크 텍스트 확인
                links = self.driver.find_elements(By.TAG_NAME, "a")
                self.log_callback(f"🔍 페이지의 모든 링크 개수: {len(links)}")
                for i, link in enumerate(links[:10]):  # 처음 10개만
                    try:
                        text = link.text.strip()
                        href = link.get_attribute('href')
                        if text and href:
                            self.log_callback(f"   링크 {i+1}: '{text}' -> {href}")
                    except:
                        continue
                return False

            # My Learning 페이지 로드 대기
            time.sleep(Config.PAGE_LOAD_DELAY)

            # My Learning 페이지 도착 확인
            if 'my-courses' in self.driver.current_url or 'my-learning' in self.driver.current_url:
                self.log_callback("✅ My Learning 페이지 도착 확인")
                return True
            else:
                self.log_callback(f"⚠️ 예상된 페이지와 다름: {self.driver.current_url}")
                return True  # 일단 진행해보기

        except Exception as e:
            self.log_callback(f"❌ My Learning 이동 실패: {str(e)}")
            return False

    def search_and_select_course(self, course_name: str) -> Optional[Course]:
        """강의 검색 및 선택"""
        try:
            self.log_callback(f"🔍 강의 검색 시작: '{course_name}'")

            # 1. 검색 입력 필드 찾기
            search_input = self._find_search_input()
            if not search_input:
                self.log_callback("❌ 검색 입력 필드를 찾을 수 없습니다.")
                # 기존 강의에서 찾아보기
                return self._search_from_existing_courses(course_name)

            # 2. 검색어 입력
            self.log_callback(f"📝 검색어 입력: '{course_name}'")
            search_input.clear()
            search_input.send_keys(course_name)

            # 입력 완료 후 대기 (검색 필드 처리 시간)
            time.sleep(2)

            # 3. 검색 버튼 클릭
            if not self._click_search_button():
                self.log_callback("⚠️ 검색 버튼 클릭 실패, Enter키로 검색 시도")
                search_input.send_keys("\n")

            # 4. 검색 결과 대기
            self._wait_for_search_results(course_name)

            # 5. 검색 결과에서 강의 선택
            course = self._search_from_existing_courses(course_name)
            if course:
                return course
            else:
                self.log_callback(f"❌ '{course_name}' 강의를 찾을 수 없습니다.")
                return None

        except Exception as e:
            self.log_callback(f"❌ 강의 검색 실패: {str(e)}")
            return None

    def _find_search_input(self):
        """My Learning 페이지 전용 검색 입력 필드 찾기"""
        try:
            # 실제 HTML 구조에 기반한 정확한 선택자들
            search_selectors = [
                # 가장 정확한 선택자 (제공된 HTML 기준)
                "input[placeholder='내 강의 검색']",
                ".search-my-courses-field--autosuggest--8G-XL input",
                ".autosuggest-module--autosuggest-input--cL5WV",
                "input.ud-text-input[placeholder*='내 강의']",

                # 영어 버전 대응
                "input[placeholder='Search my courses']",
                "input[placeholder*='Search']",

                # 일반적인 백업 선택자
                ".search-my-courses-field input",
                "form.search-my-courses-field input",
                ".autosuggest-input",
                "input[type='text'][role='combobox']"
            ]

            for i, selector in enumerate(search_selectors):
                try:
                    self.log_callback(f"🔍 검색 필드 시도 {i+1}/{len(search_selectors)}: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for j, element in enumerate(elements):
                        if element.is_displayed():
                            self.log_callback(f"✅ 내 강의 검색 필드 발견: {selector}")
                            return element
                        else:
                            self.log_callback(f"   요소 {j+1} 숨겨져 있음")

                except Exception as e:
                    self.log_callback(f"   선택자 실패: {str(e)}")
                    continue

            self.log_callback("⚠️ 내 강의 검색 필드를 찾을 수 없음")

            # 현재 페이지 정보 출력
            self.log_callback(f"🔍 현재 URL: {self.driver.current_url}")
            self.log_callback(f"🔍 페이지 제목: {self.driver.title}")

            return None

        except Exception as e:
            self.log_callback(f"❌ 검색 입력 필드 찾기 실패: {str(e)}")
            return None

    def _click_search_button(self) -> bool:
        """My Learning 검색 버튼 클릭"""
        try:
            # 제공된 실제 HTML 구조에 기반한 정확한 검색 버튼 선택자
            search_button_selectors = [
                # 가장 정확한 선택자 (제공된 HTML 기준 - 전체 클래스 체인)
                "button.ud-btn.ud-btn-medium.ud-btn-primary.ud-btn-text-sm.ud-btn-icon.ud-btn-icon-medium[type='submit']",
                "button[type='submit'].ud-btn.ud-btn-medium.ud-btn-primary.ud-btn-text-sm.ud-btn-icon.ud-btn-icon-medium",

                # 핵심 클래스들만 조합
                "button.ud-btn-primary.ud-btn-icon[type='submit']",
                "button[type='submit'].ud-btn-primary.ud-btn-icon",

                # form 컨텍스트 내 검색 버튼
                ".search-my-courses-field button[type='submit']",
                "form.search-my-courses-field--form button[type='submit']",
                ".search-my-courses-field--form button[type='submit']",

                # SVG 아이콘을 포함한 버튼 직접 찾기
                "button[type='submit']:has(svg[aria-label='검색'])",
                "button[type='submit']:has(svg[aria-label='Search'])",
                "button:has(svg use[xlink\\:href='#icon-search'])",

                # 일반 백업 선택자들
                "button[type='submit'].ud-btn-primary",
                "button.ud-btn-icon[type='submit']",
                "button[type='submit']"
            ]

            for i, selector in enumerate(search_button_selectors):
                try:
                    self.log_callback(f"🔍 검색 버튼 시도 {i+1}/{len(search_button_selectors)}: {selector}")

                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.log_callback(f"   발견된 요소 수: {len(elements)}")

                    for j, button in enumerate(elements):
                        try:
                            if button.is_displayed() and button.is_enabled():
                                # 버튼의 상세 정보 로깅
                                button_classes = button.get_attribute("class")
                                button_type = button.get_attribute("type")
                                self.log_callback(f"   버튼 {j+1}: type='{button_type}', classes='{button_classes}'")

                                # SVG 아이콘이 있는지 확인
                                try:
                                    svg = button.find_element(By.CSS_SELECTOR, "svg")
                                    aria_label = svg.get_attribute("aria-label")
                                    self.log_callback(f"   SVG 발견: aria-label='{aria_label}'")

                                    # 검색 아이콘인지 확인
                                    if aria_label and ('검색' in aria_label or 'Search' in aria_label.lower()):
                                        self.log_callback(f"   ✅ 검색 아이콘 확인됨")
                                        button.click()
                                        self.log_callback(f"✅ 검색 버튼 클릭 완료: {selector}")
                                        return True
                                    else:
                                        # use 태그로도 확인
                                        try:
                                            use_elem = svg.find_element(By.CSS_SELECTOR, "use")
                                            href = use_elem.get_attribute("xlink:href") or use_elem.get_attribute("href")
                                            self.log_callback(f"   USE 태그: href='{href}'")
                                            if href and 'search' in href:
                                                button.click()
                                                self.log_callback(f"✅ 검색 버튼 클릭 완료: {selector}")
                                                return True
                                        except:
                                            pass

                                except:
                                    # SVG가 없어도 submit 타입이면 시도
                                    if button_type == "submit":
                                        self.log_callback(f"   SVG 없는 submit 버튼 클릭 시도")
                                        button.click()
                                        self.log_callback(f"✅ Submit 버튼 클릭 완료: {selector}")
                                        return True
                            else:
                                self.log_callback(f"   버튼 {j+1} 클릭 불가 (숨겨짐 또는 비활성화)")

                        except Exception as click_error:
                            self.log_callback(f"   버튼 {j+1} 클릭 실패: {str(click_error)}")
                            continue

                except Exception as e:
                    self.log_callback(f"   선택자 실패: {str(e)}")
                    continue

            # 모든 선택자 실패시 JavaScript로 시도
            self.log_callback("🔧 JavaScript로 검색 버튼 클릭 시도...")
            try:
                js_script = """
                // 검색 버튼을 찾는 JavaScript
                var buttons = document.querySelectorAll('button[type="submit"]');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var svg = btn.querySelector('svg');
                    if (svg) {
                        var ariaLabel = svg.getAttribute('aria-label');
                        if (ariaLabel && (ariaLabel.includes('검색') || ariaLabel.toLowerCase().includes('search'))) {
                            btn.click();
                            return 'SUCCESS: ' + btn.className;
                        }
                        var use = svg.querySelector('use');
                        if (use) {
                            var href = use.getAttribute('xlink:href') || use.getAttribute('href');
                            if (href && href.includes('search')) {
                                btn.click();
                                return 'SUCCESS: ' + btn.className;
                            }
                        }
                    }
                }
                return 'FAILED: No search button found';
                """

                result = self.driver.execute_script(js_script)
                self.log_callback(f"JavaScript 실행 결과: {result}")

                if result.startswith("SUCCESS"):
                    self.log_callback("✅ JavaScript로 검색 버튼 클릭 완료")
                    return True

            except Exception as js_error:
                self.log_callback(f"JavaScript 실행 실패: {str(js_error)}")

            self.log_callback("⚠️ 모든 방법으로 검색 버튼을 찾을 수 없음")
            return False

        except Exception as e:
            self.log_callback(f"❌ 검색 버튼 클릭 실패: {str(e)}")
            return False

    def _wait_for_search_results(self, course_name: str):
        """검색 결과 로드 대기"""
        try:
            self.log_callback("⏳ 검색 결과 로딩 대기 중...")
            time.sleep(3)  # 검색 결과 로딩 대기

            # 로딩 인디케이터가 사라질 때까지 대기
            for i in range(10):
                try:
                    loading_elements = self.driver.find_elements(By.CSS_SELECTOR,
                        ".loading, .spinner, [data-purpose='loader']")
                    if not loading_elements:
                        break
                    time.sleep(1)
                except:
                    break

            # 추가 대기
            time.sleep(2)
            self.log_callback("✅ 검색 결과 로딩 완료")

        except Exception as e:
            self.log_callback(f"⚠️ 검색 결과 대기 중 오류: {str(e)}")

    def _search_from_existing_courses(self, course_name: str) -> Optional[Course]:
        """기존 강의 목록에서 검색"""
        try:
            self.log_callback(f"📋 기존 강의 목록에서 '{course_name}' 검색...")

            # 강의 카드들 찾기
            course_cards = self._find_course_cards()
            if not course_cards:
                self.log_callback("❌ 강의 카드를 찾을 수 없습니다.")
                return None

            self.log_callback(f"🔍 총 {len(course_cards)}개 강의 카드 발견")

            # 일치하는 강의 찾기
            matching_course = self._find_matching_course(course_cards, course_name)
            if matching_course:
                return self._click_and_enter_course(matching_course, course_name)
            else:
                self.log_callback(f"❌ '{course_name}'과 일치하는 강의를 찾을 수 없습니다.")
                self._list_available_courses(course_cards)
                return None

        except Exception as e:
            self.log_callback(f"❌ 기존 강의 검색 실패: {str(e)}")
            return None

    def _find_course_cards(self) -> List:
        """강의 카드 요소들 찾기"""
        try:
            # 다양한 강의 카드 선택자들
            card_selectors = [
                "[data-purpose='enrolled-course-card']",
                ".card-component",
                ".course-card",
                ".my-course-card",
                ".enrolled-course-card",
                "[data-purpose='course-card']",
                ".course-item"
            ]

            all_cards = []

            for selector in card_selectors:
                try:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        self.log_callback(f"✅ {selector}로 {len(cards)}개 카드 발견")
                        all_cards.extend(cards)
                        # 첫 번째 성공한 선택자의 결과 사용
                        return cards
                except Exception as e:
                    self.log_callback(f"   선택자 {selector} 실패: {str(e)}")
                    continue

            if not all_cards:
                # 모든 선택자 실패 시 일반적인 요소들로 시도
                self.log_callback("🔍 일반 요소들로 강의 카드 검색...")
                try:
                    # div 요소 중에서 강의처럼 보이는 것들 찾기
                    potential_cards = self.driver.find_elements(By.CSS_SELECTOR,
                        "div[class*='card'], div[class*='course'], a[href*='course']")

                    # 필터링: 텍스트가 있고 클릭 가능해 보이는 것들
                    filtered_cards = []
                    for card in potential_cards:
                        try:
                            if (card.text.strip() and
                                card.is_displayed() and
                                len(card.text.strip()) > 10):  # 의미있는 텍스트가 있는지
                                filtered_cards.append(card)
                        except:
                            continue

                    if filtered_cards:
                        self.log_callback(f"✅ 일반 요소로 {len(filtered_cards)}개 카드 발견")
                        return filtered_cards

                except Exception as e:
                    self.log_callback(f"   일반 요소 검색 실패: {str(e)}")

            return all_cards

        except Exception as e:
            self.log_callback(f"❌ 강의 카드 찾기 실패: {str(e)}")
            return []

    def _find_matching_course(self, course_cards: List, target_name: str) -> Optional:
        """일치하는 강의 찾기"""
        try:
            self.log_callback(f"🔍 '{target_name}'과 일치하는 강의 검색 중...")

            best_match = None
            best_score = 0.0

            for i, card in enumerate(course_cards):
                try:
                    # 강의 제목 추출
                    course_title = self._extract_course_title(card)
                    if not course_title:
                        continue

                    # 유사도 계산
                    score = self._calculate_match_score(course_title, target_name)

                    self.log_callback(f"   카드 {i+1}: '{course_title}' (유사도: {score:.2f})")

                    if score > best_score:
                        best_score = score
                        best_match = card

                except Exception as e:
                    self.log_callback(f"   카드 {i+1} 분석 실패: {str(e)}")
                    continue

            if best_match and best_score >= 0.3:  # 최소 30% 유사도
                final_title = self._extract_course_title(best_match)
                self.log_callback(f"✅ 최적 일치 강의: '{final_title}' (유사도: {best_score:.2f})")
                return best_match
            else:
                self.log_callback(f"❌ 충분한 유사도의 강의를 찾을 수 없음 (최고: {best_score:.2f})")
                return None

        except Exception as e:
            self.log_callback(f"❌ 강의 일치 검사 실패: {str(e)}")
            return None

    def _extract_course_title(self, card_element) -> Optional[str]:
        """강의 카드에서 제목 추출"""
        try:
            # 제목을 찾을 수 있는 다양한 선택자들
            title_selectors = [
                "h3", "h2", "h4",
                ".course-title",
                "[data-purpose='course-title']",
                ".card-title",
                "a[href*='course']",
                ".title"
            ]

            for selector in title_selectors:
                try:
                    elements = card_element.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        title = element.text.strip()
                        if title and len(title) > 3:  # 의미있는 제목인지 확인
                            return title
                except:
                    continue

            # 선택자로 찾지 못한 경우 카드의 전체 텍스트에서 추출
            full_text = card_element.text.strip()
            if full_text:
                # 첫 번째 줄이나 가장 긴 줄을 제목으로 추정
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                if lines:
                    # 가장 긴 줄을 제목으로 선택
                    title_candidates = [line for line in lines if len(line) > 10]
                    if title_candidates:
                        return max(title_candidates, key=len)
                    else:
                        return lines[0]  # 첫 번째 줄

            return None

        except Exception as e:
            return None

    def _calculate_match_score(self, course_title: str, target: str) -> float:
        """강의 제목과 검색어 간의 유사도 점수 계산"""
        try:
            # 소문자로 변환하여 비교
            title_lower = course_title.lower()
            target_lower = target.lower()

            # 완전 일치
            if title_lower == target_lower:
                return 1.0

            # 포함 관계
            if target_lower in title_lower:
                return 0.8
            if title_lower in target_lower:
                return 0.7

            # 단어 단위 일치 검사
            title_words = set(title_lower.split())
            target_words = set(target_lower.split())

            if title_words and target_words:
                common_words = title_words.intersection(target_words)
                return len(common_words) / len(target_words.union(title_words))

            return 0.0

        except:
            return 0.0

    def _list_available_courses(self, course_cards: List):
        """사용 가능한 강의 목록 출력"""
        try:
            self.log_callback("📚 사용 가능한 강의 목록:")
            for i, card in enumerate(course_cards[:10]):  # 최대 10개만
                try:
                    title = self._extract_course_title(card)
                    if title:
                        self.log_callback(f"   {i+1}. {title}")
                except:
                    continue
        except:
            pass

    def _click_and_enter_course(self, course_card, course_name: str) -> Optional[Course]:
        """강의 카드 클릭하여 강의 페이지로 이동"""
        try:
            self.log_callback(f"🖱️ 강의 카드 클릭하여 '{course_name}' 강의로 이동...")

            # 강의 제목 다시 추출
            course_title = self._extract_course_title(course_card)

            # 클릭 가능한 요소 찾기 (링크 우선)
            clickable_element = course_card
            try:
                # 카드 내의 링크 찾기
                links = course_card.find_elements(By.CSS_SELECTOR, "a[href*='course']")
                if links:
                    clickable_element = links[0]
                    self.log_callback("📎 강의 링크로 클릭")
            except:
                self.log_callback("🖱️ 카드 자체를 클릭")

            # 클릭 실행
            clickable_element.click()
            self.log_callback("✅ 강의 카드 클릭 완료")

            # 페이지 로딩 대기
            time.sleep(Config.PAGE_LOAD_DELAY)

            # 강의 페이지 도착 확인
            if 'course' in self.driver.current_url:
                self.log_callback("✅ 강의 페이지 도착 확인")

                # Course 객체 생성
                course = Course(
                    title=course_title or course_name,
                    instructor="",  # 추후 추출 가능
                    description=""  # 추후 추출 가능
                )

                return course
            else:
                self.log_callback(f"⚠️ 예상과 다른 페이지: {self.driver.current_url}")
                return None

        except Exception as e:
            self.log_callback(f"❌ 강의 클릭 실패: {str(e)}")
            return None

    def _check_login_status(self) -> bool:
        """로그인 상태 확인"""
        try:
            # 로그인 상태를 나타내는 요소들 확인
            login_indicators = [
                # 사용자 프로필 관련 요소들
                "button[data-purpose='user-avatar']",
                ".user-avatar",
                "button[aria-label*='account menu']",

                # 드롭다운 메뉴 (제공된 HTML 기준)
                ".ud-block-list-item-content",
                "a[href='/home/my-courses/']",

                # 내 학습 링크
                "//a[contains(@href, '/home/my-courses')]",
                "//a[contains(text(), '내 학습')]",
                "//a[contains(text(), 'My learning')]",

                # 기타 로그인 상태 지시자
                "[data-purpose='my-learning-nav']",
                ".header-my-learning"
            ]

            for i, selector in enumerate(login_indicators):
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                self.log_callback(f"✅ 로그인 확인: {selector}")
                                return True

                except Exception as e:
                    continue

            # 로그인 버튼이 있는지도 확인 (로그인 안된 상태)
            login_buttons = [
                "//a[contains(text(), 'Log in')]",
                "//a[contains(text(), '로그인')]",
                "//button[contains(text(), 'Log in')]",
                "a[href*='login']"
            ]

            for selector in login_buttons:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                self.log_callback(f"❌ 로그인 필요 (로그인 버튼 발견): {selector}")
                                return False

                except:
                    continue

            self.log_callback("⚠️ 로그인 상태 불명확 - 로그인된 것으로 가정")
            return True

        except Exception as e:
            self.log_callback(f"⚠️ 로그인 상태 확인 실패: {str(e)} - 로그인된 것으로 가정")
            return True