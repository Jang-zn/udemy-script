"""
Udemy 페이지 탐색 및 강의 선택 모듈
"""

import time
import re
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from config import Config
from models import Course, Section, Lecture

class UdemyNavigator:
    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print
    
    def go_to_my_learning(self) -> bool:
        """'내 학습' 버튼 클릭해서 My Learning 페이지로 이동"""
        try:
            self.log_callback("📚 '내 학습' 버튼 클릭 중...")

            # "내 학습" 버튼 찾아서 클릭
            my_learning_selectors = [
                "//a[contains(text(), 'My learning')]",
                "//a[contains(text(), '내 학습')]",
                "//a[contains(@href, '/home/my-courses')]",
                "//a[contains(@href, 'my-learning')]",
                "[data-purpose='my-learning-nav']",
                ".header-my-learning",
                "a[href*='my-courses']"
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
                        if button and button.is_displayed():
                            self.log_callback(f"   요소 {j+1} 클릭 시도 중...")
                            button.click()
                            self.log_callback("✅ '내 학습' 버튼 클릭 완료")
                            button_clicked = True
                            break
                        else:
                            self.log_callback(f"   요소 {j+1} 숨겨져 있음")

                    if button_clicked:
                        break

                except Exception as e:
                    self.log_callback(f"   ❌ 선택자 실패: {str(e)}")
                    continue

            if not button_clicked:
                self.log_callback("❌ '내 학습' 버튼을 찾을 수 없습니다. 직접 URL로 이동합니다.")
                self.log_callback(f"🔍 현재 URL: {self.driver.current_url}")

                # 페이지에 있는 모든 링크 확인
                links = self.driver.find_elements(By.TAG_NAME, "a")
                self.log_callback(f"🔍 페이지의 링크 개수: {len(links)}")
                for i, link in enumerate(links[:15]):  # 처음 15개만
                    try:
                        text = link.text.strip()
                        href = link.get_attribute('href')
                        if text and href:
                            self.log_callback(f"   링크 {i+1}: '{text}' -> {href[:50]}...")
                    except:
                        continue

                self.driver.get(Config.UDEMY_MY_LEARNING_URL)

            time.sleep(Config.PAGE_LOAD_DELAY)

            # 페이지 로딩 확인 (검색 input 또는 강의 목록)
            try:
                self.log_callback("⏳ My Learning 페이지 로딩 확인 중...")
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='search']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='검색']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='course-card']")),
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'course-card')]"))
                    )
                )
                self.log_callback("✅ My Learning 페이지 로드 완료")
                return True

            except TimeoutException:
                self.log_callback("⚠️ My Learning 페이지 로딩을 확인할 수 없습니다.")
                self.log_callback(f"🔍 현재 페이지 URL: {self.driver.current_url}")
                self.log_callback(f"🔍 페이지 제목: {self.driver.title}")
                return True  # 일단 진행

        except Exception as e:
            self.log_callback(f"❌ My Learning 페이지 이동 실패: {str(e)}")
            import traceback
            self.log_callback(f"🔍 스택 트레이스: {traceback.format_exc()}")
            return False
    
    def search_and_select_course(self, course_name: str) -> Optional[Course]:
        """검색 input에 강의명 입력해서 검색 후 선택"""
        try:
            self.log_callback(f"🔍 강의 검색 중: '{course_name}'")
            
            # 1. 검색 input 찾기
            search_input = self._find_search_input()
            if not search_input:
                self.log_callback("⚠️ 검색 기능을 찾을 수 없습니다. 기존 강의 목록에서 검색합니다.")
                return self._search_from_existing_courses(course_name)
            
            # 2. 검색어 입력
            self.log_callback(f"📝 검색어 입력: '{course_name}'")
            search_input.clear()
            search_input.send_keys(course_name)
            time.sleep(1)
            
            # 3. 검색 버튼 클릭 또는 Enter
            if not self._click_search_button():
                # 검색 버튼이 없으면 Enter로 검색
                from selenium.webdriver.common.keys import Keys
                search_input.send_keys(Keys.RETURN)

            # 4. 검색 완료 대기 (로딩 완료 체크)
            self._wait_for_search_results(course_name)
            
            # 4. 검색 결과에서 강의 카드 찾기
            course_cards = self._find_course_cards()
            
            if not course_cards:
                self.log_callback("❌ 검색 결과에서 강의를 찾을 수 없습니다.")
                return None
            
            self.log_callback(f"📋 검색 결과: {len(course_cards)}개의 강의를 찾았습니다.")
            
            # 5. 가장 적합한 강의 선택
            selected_card = self._find_matching_course(course_cards, course_name)
            
            if not selected_card:
                self.log_callback(f"❌ '{course_name}'과 일치하는 강의를 찾을 수 없습니다.")
                self._list_available_courses(course_cards)
                return None
            
            # 6. 강의 클릭 및 이동
            course = self._click_and_enter_course(selected_card, course_name)
            return course
            
        except Exception as e:
            self.log_callback(f"❌ 강의 검색 중 오류: {str(e)}")
            return None
    
    def _find_search_input(self):
        """검색 input 요소 찾기"""
        try:
            # 실제 Udemy 검색 input 선택자
            search_selectors = [
                "#u912-form-group--53",  # 실제 검색 input ID
                "#u912-form-group--53 input",  # input 태그로 명확히
                "input[placeholder*='search']",
                "input[placeholder*='Search']",
                "input[placeholder*='검색']",
                "input[type='search']",
                "[data-purpose='search-input']",
                ".search-input"
            ]
            
            for selector in search_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        self.log_callback(f"✅ 검색 input 찾음: {selector}")
                        return element
                except:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _click_search_button(self) -> bool:
        """검색 버튼 클릭"""
        try:
            # 실제 Udemy 검색 버튼 선택자
            search_button_selectors = [
                "#u912-tabs--49-content-0 > div > div.learning-filter--row--Z4aPP.learning-filter--learning-filter--IM03g > div.learning-filter--search-field--lad99 > form > div > div > button",  # 실제 버튼 경로
                ".learning-filter--search-field--lad99 button",  # 더 간단한 선택자
                "button[type='submit']",
                "button[aria-label*='Search']",
                "button[aria-label*='search']",
                "button[aria-label*='검색']",
                ".search-button",
                "[data-purpose='search-button']"
            ]
            
            for selector in search_button_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button and button.is_displayed():
                        button.click()
                        self.log_callback("✅ 검색 버튼 클릭 완료")
                        return True
                except:
                    continue
            
            return False

        except Exception:
            return False

    def _wait_for_search_results(self, course_name: str):
        """검색 결과 로딩 완료 대기"""
        try:
            self.log_callback("⏳ 검색 결과 로딩 대기 중...")

            # 방법 1: 검색어가 포함된 강의 제목이 나타나기를 대기
            wait_conditions = [
                # 검색 결과 강의 타이틀 출현
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3[data-purpose='course-title-url']")),
                # 로딩 스피너 사라짐
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-spinner")),
                # 검색 결과 없음 메시지
                EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), 'No results')]")),
                # 강의 카드 출현
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/course-dashboard-redirect/']"))
            ]

            # 최대 10초 대기
            for i in range(10):
                # 강의 타이틀이 나타났는지 확인
                titles = self.driver.find_elements(By.CSS_SELECTOR, "h3[data-purpose='course-title-url']")
                if titles:
                    self.log_callback(f"✅ 검색 결과 로딩 완료 ({len(titles)}개 강의)")
                    time.sleep(1)  # 안정화를 위한 추가 대기
                    return

                # 검색 결과 없음 메시지 확인
                no_results = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'No results') or contains(text(), '결과 없음')]")
                if no_results:
                    self.log_callback("⚠️ 검색 결과가 없습니다")
                    return

                time.sleep(1)
                self.log_callback(f"   대기 중... {i+1}/10초")

            self.log_callback("⚠️ 검색 결과 로딩 타임아웃 - 계속 진행")

        except Exception as e:
            self.log_callback(f"⚠️ 검색 결과 대기 중 오류: {str(e)}")

    def _search_from_existing_courses(self, course_name: str) -> Optional[Course]:
        """기존 강의 목록에서 텍스트 매칭으로 검색 (fallback)"""
        try:
            self.log_callback("🔍 기존 강의 목록에서 검색합니다...")
            
            # 페이지에서 강의 카드들 찾기
            course_cards = self._find_course_cards()
            
            if not course_cards:
                self.log_callback("❌ 강의 카드를 찾을 수 없습니다.")
                return None
            
            self.log_callback(f"📋 총 {len(course_cards)}개의 강의를 찾았습니다.")
            
            # 강의명으로 매칭
            selected_card = self._find_matching_course(course_cards, course_name)
            
            if not selected_card:
                self.log_callback(f"❌ '{course_name}'과 일치하는 강의를 찾을 수 없습니다.")
                self._list_available_courses(course_cards)
                return None
            
            # 강의 클릭 및 이동
            course = self._click_and_enter_course(selected_card, course_name)
            return course
            
        except Exception as e:
            self.log_callback(f"❌ 기존 강의 목록 검색 중 오류: {str(e)}")
            return None
    
    def _find_course_cards(self) -> List:
        """강의 카드 요소들 찾기"""
        try:
            self.log_callback("🔍 강의 카드 요소들 검색 중...")

            # 실제 Udemy 강의 카드 선택자 (우선순위 순)
            selectors = [
                "h3[data-purpose='course-title-url']",  # 실제 강의 타이틀 h3
                "h3.course-card-title-module--course-title--wmFXN",  # 타이틀 클래스
                "h3[data-purpose='course-title-url'] > a",  # 타이틀 내 링크
                "a[href*='/course-dashboard-redirect/']",  # 강의 대시보드 링크
                "[data-testid='course-card']",
                ".my-courses-card",
                ".course-card--course-card--1QM2W",
                "div[class*='course-card']",
                "a[href*='/course/']",
                ".card-container",
                "[data-purpose='course-card']",
                ".course-item",
                ".my-course-card"
            ]

            for i, selector in enumerate(selectors):
                try:
                    self.log_callback(f"🔍 시도 {i+1}/{len(selectors)}: {selector}")
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.log_callback(f"   발견된 카드 수: {len(cards)}")

                    if cards:
                        self.log_callback(f"✅ 강의 카드 발견 (선택자: {selector}, 개수: {len(cards)})")
                        return cards
                except Exception as e:
                    self.log_callback(f"   ❌ 선택자 실패: {str(e)}")
                    continue

            # XPath로도 시도
            self.log_callback("🔍 XPath 선택자로 재시도...")
            xpath_selectors = [
                "//div[contains(@class, 'course-card')]",
                "//a[contains(@href, '/course/')]",
                "//div[contains(@data-testid, 'course')]",
                "//div[contains(text(), '강의') or contains(text(), 'Course')]/..",
                "//div[contains(@class, 'card')]",
                "//article",
                "//div[contains(@class, 'item')]"
            ]

            for i, xpath in enumerate(xpath_selectors):
                try:
                    self.log_callback(f"🔍 XPath 시도 {i+1}/{len(xpath_selectors)}: {xpath}")
                    cards = self.driver.find_elements(By.XPATH, xpath)
                    self.log_callback(f"   발견된 카드 수: {len(cards)}")

                    if cards:
                        self.log_callback(f"✅ 강의 카드 발견 (XPath: {xpath}, 개수: {len(cards)})")
                        return cards
                except Exception as e:
                    self.log_callback(f"   ❌ XPath 실패: {str(e)}")
                    continue

            # 모든 시도 실패 시 페이지 정보 출력
            self.log_callback("❌ 모든 강의 카드 선택자 실패")
            self.log_callback(f"🔍 현재 URL: {self.driver.current_url}")
            self.log_callback(f"🔍 페이지 제목: {self.driver.title}")

            # 페이지에 있는 모든 div 요소 클래스 확인
            divs = self.driver.find_elements(By.TAG_NAME, "div")
            self.log_callback(f"🔍 페이지의 div 개수: {len(divs)}")

            unique_classes = set()
            for div in divs[:50]:  # 처음 50개만
                try:
                    classes = div.get_attribute('class')
                    if classes:
                        for cls in classes.split():
                            if any(keyword in cls.lower() for keyword in ['course', 'card', 'item', 'learning']):
                                unique_classes.add(cls)
                except:
                    continue

            if unique_classes:
                self.log_callback("🔍 관련된 클래스들:")
                for cls in sorted(unique_classes)[:20]:
                    self.log_callback(f"   .{cls}")

            return []

        except Exception as e:
            self.log_callback(f"❌ 강의 카드 찾기 실패: {str(e)}")
            import traceback
            self.log_callback(f"🔍 스택 트레이스: {traceback.format_exc()}")
            return []
    
    def _find_matching_course(self, course_cards: List, target_name: str) -> Optional:
        """강의명과 일치하는 강의 카드 찾기"""
        try:
            target_lower = target_name.lower()
            best_match = None
            best_score = 0
            
            for card in course_cards:
                try:
                    # 강의 제목 텍스트 추출
                    course_title = self._extract_course_title(card)
                    
                    if not course_title:
                        continue
                    
                    # 매칭 점수 계산
                    score = self._calculate_match_score(course_title.lower(), target_lower)
                    
                    self.log_callback(f"  📖 '{course_title}' (매칭 점수: {score:.2f})")
                    
                    if score > best_score:
                        best_score = score
                        best_match = card
                        
                except Exception as e:
                    continue
            
            if best_match and best_score > 0.3:  # 30% 이상 매칭
                title = self._extract_course_title(best_match)
                self.log_callback(f"✅ 최적 매칭 강의: '{title}' (점수: {best_score:.2f})")
                return best_match
            
            return None
            
        except Exception as e:
            self.log_callback(f"❌ 강의 매칭 중 오류: {str(e)}")
            return None
    
    def _extract_course_title(self, card_element) -> Optional[str]:
        """강의 카드에서 제목 추출"""
        try:
            # 실제 Udemy 제목 선택자 (우선순위)
            title_selectors = [
                "h3[data-purpose='course-title-url'] a",  # 실제 타이틀 링크
                "h3.course-card-title-module--course-title--wmFXN a",
                "a[href*='/course-dashboard-redirect/']",
                "h3", "h4", "h2",
                "[data-purpose='course-title']",
                ".course-card--course-title--vXFUL",
                ".course-title",
                "a[href*='/course/']",
                ".card-title"
            ]
            
            for selector in title_selectors:
                try:
                    element = card_element.find_element(By.CSS_SELECTOR, selector)
                    title = element.get_attribute('title') or element.text.strip()
                    if title:
                        return title
                except:
                    continue
            
            # 전체 텍스트에서 추출
            full_text = card_element.text.strip()
            if full_text:
                # 첫 번째 줄을 제목으로 가정
                lines = full_text.split('\n')
                return lines[0] if lines else full_text
            
            return None
            
        except Exception:
            return None
    
    def _calculate_match_score(self, course_title: str, target: str) -> float:
        """강의명 매칭 점수 계산 (0-1)"""
        try:
            # 정확한 매칭
            if target in course_title:
                return 1.0
            
            # 키워드 매칭
            target_words = set(target.split())
            course_words = set(course_title.split())
            
            if not target_words:
                return 0.0
            
            matching_words = target_words.intersection(course_words)
            return len(matching_words) / len(target_words)
            
        except Exception:
            return 0.0
    
    def _list_available_courses(self, course_cards: List):
        """사용 가능한 강의 목록 출력"""
        try:
            self.log_callback("\n📚 사용 가능한 강의 목록:")
            for i, card in enumerate(course_cards[:10], 1):  # 최대 10개만
                title = self._extract_course_title(card)
                if title:
                    self.log_callback(f"  {i}. {title}")
        except Exception:
            pass
    
    def _click_and_enter_course(self, course_card, course_name: str) -> Optional[Course]:
        """강의 카드 클릭하고 강의 페이지로 이동"""
        try:
            # 강의 제목 추출
            course_title = self._extract_course_title(course_card)

            self.log_callback(f"🖱️ 강의 클릭: '{course_title}'")

            # h3 안의 a 태그를 찾아서 클릭
            try:
                link = course_card.find_element(By.TAG_NAME, "a")
                self.log_callback(f"🔗 링크 URL: {link.get_attribute('href')}")
                self.driver.execute_script("arguments[0].click();", link)
            except:
                # a 태그를 찾을 수 없으면 course_card 자체 클릭
                self.log_callback("⚠️ a 태그를 찾을 수 없어 course_card 클릭")
                self.driver.execute_script("arguments[0].click();", course_card)

            time.sleep(3)
            
            # 강의 페이지 로딩 대기
            try:
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".curriculum-item")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-purpose='curriculum-item']")),
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'curriculum')]")),
                        EC.url_contains("/learn/")
                    )
                )
                
                self.log_callback("✅ 강의 페이지 진입 완료")
                
                # Course 객체 생성
                course = Course(title=course_title or course_name)
                return course
                
            except TimeoutException:
                self.log_callback("⚠️ 강의 페이지 로딩 타임아웃")
                return Course(title=course_title or course_name)
                
        except Exception as e:
            self.log_callback(f"❌ 강의 페이지 진입 실패: {str(e)}")
            return None
    
    def analyze_curriculum(self, course: Course) -> bool:
        """강의 커리큘럼 구조 분석"""
        try:
            self.log_callback("📖 커리큘럼 구조 분석 중...")
            
            # 커리큘럼 섹션들 찾기
            sections = self._find_curriculum_sections()
            
            if not sections:
                self.log_callback("❌ 커리큘럼 섹션을 찾을 수 없습니다.")
                return False
            
            self.log_callback(f"📁 {len(sections)}개의 섹션을 찾았습니다.")
            
            # 각 섹션 분석
            for section_idx, section_element in enumerate(sections):
                section = self._analyze_section(section_element, section_idx)
                if section:
                    course.sections.append(section)
                    self.log_callback(f"  📁 섹션 {section_idx + 1}: {section.title} ({section.lecture_count}개 강의)")
            
            self.log_callback(f"✅ 커리큘럼 분석 완료: {course.total_sections}개 섹션, {course.total_lectures}개 강의")
            return True
            
        except Exception as e:
            self.log_callback(f"❌ 커리큘럼 분석 중 오류: {str(e)}")
            return False
    
    def _find_curriculum_sections(self) -> List:
        """커리큘럼 섹션 요소들 찾기"""
        try:
            self.log_callback("🔍 커리큘럼 섹션 찾는 중...")

            # 1. 먼저 커리큘럼 컨테이너를 최상단으로 스크롤
            self._scroll_curriculum_to_top()

            # 2. 실제 HTML 구조에 맞는 섹션 선택자
            selectors = [
                # 실제 HTML 구조: div[data-purpose="section-panel-X"]
                "div[data-purpose^='section-panel-']",
                # 백업 선택자들
                "div[class*='accordion-panel-module--panel--']",
                "button[id*='accordion-panel-title--']",
                "[data-purpose*='section']"
            ]

            for selector in selectors:
                try:
                    self.log_callback(f"   시도: {selector}")
                    sections = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.log_callback(f"   발견: {len(sections)}개")
                    if sections:
                        # 섹션들을 순서대로 정렬 (DOM 순서대로)
                        return sections
                except Exception as e:
                    self.log_callback(f"   실패: {str(e)}")
                    continue

            return []

        except Exception as e:
            self.log_callback(f"❌ 섹션 찾기 오류: {str(e)}")
            return []

    def _scroll_curriculum_to_top(self):
        """커리큘럼 영역을 최상단으로 스크롤"""
        try:
            self.log_callback("🔝 커리큘럼 영역 최상단으로 스크롤...")

            # 커리큘럼 컨테이너 찾기
            curriculum_selectors = [
                "div[data-purpose='curriculum-section-container']",
                ".curriculum-section-container",
                ".curriculum-content",
                "div[class*='curriculum']"
            ]

            curriculum_container = None
            for selector in curriculum_selectors:
                try:
                    curriculum_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if curriculum_container:
                        break
                except:
                    continue

            if curriculum_container:
                # 커리큘럼 영역을 최상단으로 스크롤
                self.driver.execute_script("arguments[0].scrollTop = 0;", curriculum_container)
                time.sleep(1)
                self.log_callback("✅ 커리큘럼 스크롤 완료")
            else:
                # 페이지 전체를 최상단으로 스크롤
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                self.log_callback("✅ 페이지 스크롤 완료")

        except Exception as e:
            self.log_callback(f"⚠️ 스크롤 중 오류: {str(e)}")
            # 에러가 나도 계속 진행
    
    def _analyze_section(self, section_element, section_idx: int) -> Optional[Section]:
        """개별 섹션 분석"""
        try:
            # 섹션 제목 추출
            section_title = self._extract_section_title(section_element)

            # Section 객체 생성
            section = Section(
                title=section_title or f"섹션 {section_idx + 1}",
                section_index=section_idx
            )

            self.log_callback(f"  📝 섹션 분석: {section.title}")

            # 섹션과 연결된 컨텐츠 영역 찾기
            content_area = self._find_section_content_area(section_element)
            if not content_area:
                self.log_callback(f"    ⚠️ 컨텐츠 영역을 찾을 수 없습니다")
                return section

            # 섹션 내 강의들 찾기 (비디오만)
            lectures = self._find_video_lectures(content_area)

            self.log_callback(f"    🎥 비디오 강의: {len(lectures)}개")

            for lecture_idx, lecture_element in enumerate(lectures):
                lecture = self._analyze_lecture(lecture_element, lecture_idx)
                if lecture:
                    section.lectures.append(lecture)

            return section

        except Exception as e:
            self.log_callback(f"❌ 섹션 분석 중 오류: {str(e)}")
            import traceback
            self.log_callback(f"🔍 상세 오류: {traceback.format_exc()}")
            return None

    def _find_section_content_area(self, section_element):
        """섹션과 연결된 컨텐츠 영역 찾기"""
        try:
            # section_element의 ID에서 숫자 추출
            element_id = section_element.get_attribute('id')
            if element_id and 'accordion-panel-title--' in element_id:
                panel_id = element_id.replace('accordion-panel-title--', '')
                # 해당하는 컨텐츠 패널 찾기
                content_selector = f"div[aria-labelledby='accordion-panel-title--{panel_id}']"
                content_area = self.driver.find_element(By.CSS_SELECTOR, content_selector)
                return content_area

            return None
        except Exception as e:
            self.log_callback(f"    ❌ 컨텐츠 영역 찾기 실패: {str(e)}")
            return None

    def _find_video_lectures(self, content_area):
        """컨텐츠 영역에서 비디오 강의만 찾기"""
        try:
            # 모든 강의 아이템 찾기
            lecture_items = content_area.find_elements(By.CSS_SELECTOR, "li.curriculum-item-link--curriculum-item--OVP5S")

            video_lectures = []
            for item in lecture_items:
                # 비디오 아이콘이 있는지 확인
                try:
                    video_icon = item.find_element(By.CSS_SELECTOR, "svg use[xlink:href='#icon-video']")
                    if video_icon:
                        video_lectures.append(item)
                except:
                    # 비디오 아이콘이 없으면 건너뛰기
                    continue

            return video_lectures
        except Exception as e:
            self.log_callback(f"    ❌ 비디오 강의 찾기 실패: {str(e)}")
            return []

    def _extract_section_title(self, section_element):
        """섹션 제목 추출"""
        try:
            # span 태그에서 제목 추출
            title_span = section_element.find_element(By.TAG_NAME, "span")
            return title_span.text.strip() if title_span else None
        except:
            return None

    def _analyze_lecture(self, lecture_element, lecture_idx: int):
        """개별 강의 분석"""
        try:
            from models import Lecture

            # 강의 제목 추출
            title_element = lecture_element.find_element(By.CSS_SELECTOR, "span[data-purpose='item-title']")
            title = title_element.text.strip() if title_element else f"강의 {lecture_idx + 1}"

            # 재생 시간 추출
            duration = None
            try:
                duration_elements = lecture_element.find_elements(By.CSS_SELECTOR, ".curriculum-item-link--metadata--XK804 span")
                for elem in duration_elements:
                    text = elem.text.strip()
                    if '분' in text or 'min' in text:
                        duration = text
                        break
            except:
                pass

            lecture = Lecture(
                title=title,
                lecture_index=lecture_idx,
                duration=duration,
                has_subtitles=False  # 나중에 확인
            )

            return lecture

        except Exception as e:
            self.log_callback(f"    ❌ 강의 분석 실패: {str(e)}")
            return None

    def start_complete_scraping_workflow(self, course: Course) -> bool:
        """완전한 스크래핑 워크플로우 시작"""
        try:
            self.log_callback("🚀 완전한 스크래핑 워크플로우 시작!")

            # 커리큘럼 분석부터 시작
            if not self.analyze_curriculum(course):
                self.log_callback("❌ 커리큘럼 분석 실패")
                return False

            total_sections = len(course.sections)
            self.log_callback(f"📊 총 {total_sections}개 섹션 스크래핑 시작")

            # 각 섹션 순차 처리
            for section_idx, section in enumerate(course.sections):
                self.log_callback(f"\n📁 섹션 {section_idx + 1}/{total_sections}: {section.title}")

                if not self._process_section(section, section_idx):
                    self.log_callback(f"⚠️ 섹션 {section_idx + 1} 처리 실패 - 계속 진행")
                    continue

                self.log_callback(f"✅ 섹션 {section_idx + 1} 완료")

            self.log_callback("\n🎉 모든 섹션 스크래핑 완료!")
            return True

        except Exception as e:
            self.log_callback(f"❌ 스크래핑 워크플로우 오류: {str(e)}")
            import traceback
            self.log_callback(f"🔍 상세 오류: {traceback.format_exc()}")
            return False

    def _process_section(self, section: Section, section_idx: int) -> bool:
        """개별 섹션 처리 (아코디언 열기 + 비디오 처리)"""
        try:
            # 1. 섹션 아코디언 열기
            if not self._open_section_accordion(section_idx):
                self.log_callback(f"❌ 섹션 {section_idx + 1} 아코디언 열기 실패")
                return False

            # 2. 섹션 내 비디오 강의들 처리
            return self._process_section_videos(section, section_idx)

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 처리 중 오류: {str(e)}")
            return False

    def _open_section_accordion(self, section_idx: int) -> bool:
        """섹션 아코디언 패널 열기 (실제 DOM 구조 기반)"""
        try:
            self.log_callback(f"📂 섹션 {section_idx + 1} 아코디언 열기...")

            # 1. 먼저 모든 섹션 패널 요소들을 다시 찾기
            section_panels = self.driver.find_elements(By.CSS_SELECTOR, "div[data-purpose^='section-panel-']")

            if section_idx >= len(section_panels):
                self.log_callback(f"❌ 섹션 인덱스 {section_idx + 1}가 범위를 벗어남 (총 {len(section_panels)}개 섹션)")
                return False

            # 2. 해당 섹션 패널 요소 가져오기
            target_section_panel = section_panels[section_idx]

            # 3. 해당 섹션 패널 내에서 버튼 찾기
            section_button_selectors = [
                "button[id*='accordion-panel-title--']",  # 실제 HTML 구조의 버튼
                ".ud-accordion-panel-toggler button",
                "button.js-panel-toggler",
                ".accordion-panel-module--panel-toggler--WUiNu"
            ]

            section_button = None
            for selector in section_button_selectors:
                try:
                    section_button = target_section_panel.find_element(By.CSS_SELECTOR, selector)
                    if section_button:
                        break
                except:
                    continue

            if not section_button:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 버튼을 찾을 수 없습니다")
                return False

            # 4. 아코디언이 이미 열려있는지 확인
            aria_expanded = section_button.get_attribute('aria-expanded')
            if aria_expanded == 'true':
                self.log_callback(f"📂 섹션 {section_idx + 1} 이미 열려있음")
                return True

            # 5. 아코디언 클릭하여 열기
            self.log_callback(f"🖱️ 섹션 {section_idx + 1} 버튼 클릭...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", section_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", section_button)
            time.sleep(3)  # 아코디언 애니메이션 대기

            # 6. 열렸는지 확인
            aria_expanded = section_button.get_attribute('aria-expanded')
            if aria_expanded == 'true':
                self.log_callback(f"✅ 섹션 {section_idx + 1} 아코디언 열기 성공")
                return True
            else:
                self.log_callback(f"⚠️ 섹션 {section_idx + 1} 아코디언 상태 확인 불가 - 계속 진행")
                return True  # 일단 성공으로 처리

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 아코디언 열기 오류: {str(e)}")
            return False

    def _process_section_videos(self, section: Section, section_idx: int) -> bool:
        """섹션 내 모든 비디오 강의 처리"""
        try:
            # 컨텐츠 영역 찾기
            content_area = self._find_section_content_area_by_index(section_idx)
            if not content_area:
                self.log_callback(f"❌ 섹션 {section_idx + 1} 컨텐츠 영역 찾기 실패")
                return False

            # 비디오 강의들 찾기
            video_lectures = self._find_video_lectures(content_area)
            if not video_lectures:
                self.log_callback(f"⚠️ 섹션 {section_idx + 1}에 비디오 강의가 없습니다")
                return True

            self.log_callback(f"🎥 섹션 {section_idx + 1}에서 {len(video_lectures)}개 비디오 발견")

            # 각 비디오 순차 처리
            for video_idx, video_element in enumerate(video_lectures):
                if not self._process_single_video(video_element, video_idx, section_idx):
                    self.log_callback(f"⚠️ 비디오 {video_idx + 1} 처리 실패 - 계속 진행")
                    continue

            return True

        except Exception as e:
            self.log_callback(f"❌ 섹션 {section_idx + 1} 비디오 처리 오류: {str(e)}")
            return False

    def _find_section_content_area_by_index(self, section_idx: int):
        """섹션 인덱스로 컨텐츠 영역 찾기 (실제 DOM 구조 기반)"""
        try:
            # 1. 다시 모든 섹션 패널들을 찾기
            section_panels = self.driver.find_elements(By.CSS_SELECTOR, "div[data-purpose^='section-panel-']")

            if section_idx >= len(section_panels):
                self.log_callback(f"❌ 섹션 인덱스 {section_idx + 1}가 범위를 벗어남")
                return None

            # 2. 해당 섹션 패널 가져오기
            target_section_panel = section_panels[section_idx]

            # 3. 섹션 패널 내에서 컨텐츠 영역 찾기
            content_selectors = [
                ".accordion-panel-module--content-wrapper--TkHqe",  # 실제 HTML의 컨텐츠 래퍼
                ".ud-accordion-panel-content",
                ".accordion-panel-module--content--0dD7R",
                "ul.ud-unstyled-list"  # 강의 목록이 들어있는 ul
            ]

            for selector in content_selectors:
                try:
                    content_area = target_section_panel.find_element(By.CSS_SELECTOR, selector)
                    if content_area and content_area.is_displayed():
                        return content_area
                except:
                    continue

            # 4. 백업: 전체 섹션 패널을 컨텐츠 영역으로 사용
            return target_section_panel

        except Exception as e:
            self.log_callback(f"❌ 컨텐츠 영역 찾기 실패: {str(e)}")
            return None

    def _process_single_video(self, video_element, video_idx: int, section_idx: int) -> bool:
        """단일 비디오 강의 처리 (클릭 -> 자막 추출 -> 다음)"""
        try:
            # 비디오 제목 추출
            video_title = self._extract_video_title(video_element)
            self.log_callback(f"\n🎬 비디오 {video_idx + 1}: {video_title}")

            # 1. 비디오 클릭
            if not self._click_video(video_element):
                self.log_callback(f"❌ 비디오 {video_idx + 1} 클릭 실패")
                return False

            # 2. 비디오 페이지 로딩 대기
            if not self._wait_for_video_page():
                self.log_callback(f"❌ 비디오 {video_idx + 1} 페이지 로딩 실패")
                return False

            # 3. 자막 버튼 클릭하여 자막 패널 열기
            if not self._open_transcript_panel():
                self.log_callback(f"⚠️ 비디오 {video_idx + 1} 자막 패널 열기 실패")
                # 자막이 없어도 계속 진행
                return True

            # 4. 자막 내용 추출 및 저장
            transcript_content = self._extract_transcript_content()
            if transcript_content:
                self._save_transcript(transcript_content, video_title, section_idx, video_idx)

            # 5. 자막 패널 닫기
            self._close_transcript_panel()

            return True

        except Exception as e:
            self.log_callback(f"❌ 비디오 {video_idx + 1} 처리 중 오류: {str(e)}")
            return False

    def _extract_video_title(self, video_element) -> str:
        """비디오 요소에서 제목 추출"""
        try:
            title_element = video_element.find_element(By.CSS_SELECTOR, "span[data-purpose='item-title']")
            return title_element.text.strip() if title_element else "제목 없음"
        except:
            return "제목 없음"

    def _click_video(self, video_element) -> bool:
        """비디오 요소 클릭 (실제 HTML 구조 기반)"""
        try:
            # 실제 HTML에서 클릭 가능한 요소들
            click_selectors = [
                ".item-link",  # 실제 HTML의 클릭 가능한 div
                "div[data-purpose^='curriculum-item']",  # curriculum-item-0-0 같은 div
                "div.item-link--common--j8WLy",  # 실제 클래스명
                "a",  # 백업용 링크
                "button"  # 백업용 버튼
            ]

            clicked_element = None
            for selector in click_selectors:
                try:
                    clicked_element = video_element.find_element(By.CSS_SELECTOR, selector)
                    if clicked_element:
                        break
                except:
                    continue

            if not clicked_element:
                # 마지막 시도: video_element 자체 클릭
                clicked_element = video_element

            # 클릭 실행
            self.log_callback(f"  🖱️ 비디오 요소 클릭...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", clicked_element)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", clicked_element)
            time.sleep(3)  # 페이지 로딩 대기

            return True

        except Exception as e:
            self.log_callback(f"  ❌ 비디오 클릭 실패: {str(e)}")
            return False

    def _wait_for_video_page(self) -> bool:
        """비디오 페이지 로딩 대기"""
        try:
            self.log_callback("  ⏳ 비디오 페이지 로딩 대기...")

            # 비디오 플레이어나 자막 버튼 등장 대기
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "video")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-purpose*='transcript']"))
                )
            )

            self.log_callback("  ✅ 비디오 페이지 로딩 완료")
            return True

        except TimeoutException:
            self.log_callback("  ⚠️ 비디오 페이지 로딩 타임아웃")
            return False
        except Exception as e:
            self.log_callback(f"  ❌ 비디오 페이지 대기 오류: {str(e)}")
            return False

    def _open_transcript_panel(self) -> bool:
        """자막 패널 열기"""
        try:
            self.log_callback("  📝 자막 패널 열기...")

            # 자막 버튼 선택자들 (사용자가 제공한 구조 기반)
            transcript_button_selectors = [
                "button[data-purpose*='transcript']",
                "button[aria-label*='transcript']",
                "button[aria-label*='자막']",
                ".video-viewer--transcript-toggle-button--WPnFm",
                "[data-testid='transcript-button']",
                "button[title*='transcript']",
                "button[title*='자막']"
            ]

            transcript_button = None
            for selector in transcript_button_selectors:
                try:
                    transcript_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if transcript_button and transcript_button.is_displayed():
                        break
                except:
                    continue

            if not transcript_button:
                self.log_callback("  ❌ 자막 버튼을 찾을 수 없습니다")
                return False

            # 자막 패널이 이미 열려있는지 확인
            aria_pressed = transcript_button.get_attribute('aria-pressed')
            if aria_pressed == 'true':
                self.log_callback("  📝 자막 패널 이미 열려있음")
                return True

            # 자막 버튼 클릭
            self.driver.execute_script("arguments[0].click();", transcript_button)
            time.sleep(2)

            # 자막 패널이 열렸는지 확인
            transcript_panel_selectors = [
                ".video-viewer--transcript--3aocl",
                "[data-purpose*='transcript']",
                ".transcript-panel",
                "div[class*='transcript']"
            ]

            for selector in transcript_panel_selectors:
                try:
                    panel = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if panel and panel.is_displayed():
                        self.log_callback("  ✅ 자막 패널 열기 성공")
                        return True
                except:
                    continue

            self.log_callback("  ⚠️ 자막 패널 상태 확인 불가")
            return True  # 일단 성공으로 처리

        except Exception as e:
            self.log_callback(f"  ❌ 자막 패널 열기 오류: {str(e)}")
            return False

    def _extract_transcript_content(self) -> Optional[str]:
        """자막 내용 추출"""
        try:
            self.log_callback("  📖 자막 내용 추출...")

            # 자막 텍스트 선택자들 (사용자가 제공한 구조 기반)
            transcript_text_selectors = [
                ".video-viewer--transcript--3aocl p",
                "div[class*='transcript'] p",
                "[data-purpose*='transcript'] p",
                ".transcript-text p",
                ".transcript-content p",
                ".caption-line",
                ".transcript-line"
            ]

            transcript_lines = []

            for selector in transcript_text_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for element in elements:
                            text = element.text.strip()
                            if text:
                                transcript_lines.append(text)

                        if transcript_lines:
                            break
                except:
                    continue

            if not transcript_lines:
                self.log_callback("  ❌ 자막 텍스트를 찾을 수 없습니다")
                return None

            # 자막 텍스트 결합
            transcript_content = "\n".join(transcript_lines)
            self.log_callback(f"  ✅ 자막 추출 완료 ({len(transcript_lines)}줄)")

            return transcript_content

        except Exception as e:
            self.log_callback(f"  ❌ 자막 추출 오류: {str(e)}")
            return None

    def _save_transcript(self, content: str, video_title: str, section_idx: int, video_idx: int):
        """자막 내용 저장"""
        try:
            from file_utils import MarkdownGenerator

            # 파일명 생성
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
            filename = f"섹션{section_idx + 1:02d}_비디오{video_idx + 1:02d}_{safe_title}.md"

            # 마크다운 생성
            generator = MarkdownGenerator()
            generator.add_title(video_title)
            generator.add_text(content)

            # 저장
            output_path = Config.get_output_directory() / filename
            generator.save_to_file(output_path)

            self.log_callback(f"  💾 자막 저장: {filename}")

        except Exception as e:
            self.log_callback(f"  ❌ 자막 저장 실패: {str(e)}")

    def _close_transcript_panel(self):
        """자막 패널 닫기"""
        try:
            self.log_callback("  📝 자막 패널 닫기...")

            # 자막 버튼 다시 클릭하여 패널 닫기
            transcript_button_selectors = [
                "button[data-purpose*='transcript']",
                "button[aria-label*='transcript']",
                ".video-viewer--transcript-toggle-button--WPnFm"
            ]

            for selector in transcript_button_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button and button.is_displayed():
                        aria_pressed = button.get_attribute('aria-pressed')
                        if aria_pressed == 'true':  # 패널이 열려있으면 닫기
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                            self.log_callback("  ✅ 자막 패널 닫기 완료")
                            return
                except:
                    continue

        except Exception as e:
            self.log_callback(f"  ⚠️ 자막 패널 닫기 실패: {str(e)}")  # 에러여도 계속 진행
