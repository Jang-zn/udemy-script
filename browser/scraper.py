"""
Udemy 자막 추출 모듈
"""

import time
import json
import re
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from core.models import Lecture, Subtitle
from config import Config

class SubtitleScraper:
    def __init__(self, driver, wait, log_callback=None):
        self.driver = driver
        self.wait = wait
        self.log_callback = log_callback or print
    
    def extract_lecture_subtitles(self, lecture: Lecture) -> bool:
        """강의 자막 추출 (Udemy 워크플로우)"""
        try:
            if not lecture.video_url:
                self.log_callback("     ⚠️ 강의 URL이 없습니다.")
                return False
            
            # 1. 영상 강의인지 확인 (xlink:href="#icon-video" 아이콘 체크)
            if not self._is_video_lecture(lecture):
                self.log_callback("     ⚠️ 동영상 강의가 아닙니다. 스킵합니다.")
                return False
            
            # 2. 강의 클릭해서 영상 페이지로 이동
            if not self._click_lecture_item(lecture):
                return False
            
            # 3. 영상 재생 대기
            if not self._wait_for_video_player():
                return False
            
            # 4. 마우스를 영상 영역으로 이동 후 대본 버튼 클릭
            if not self._click_transcript_button():
                self.log_callback("     ⚠️ 대본 버튼을 찾을 수 없습니다.")
                return False
            
            # 5. 우측 대본 영역에서 대본 추출
            subtitles = self._extract_transcript_from_sidebar()
            
            if subtitles:
                lecture.subtitles = subtitles
                lecture.has_subtitles = True
                self.log_callback(f"     ✅ 대본 추출 완료: {len(subtitles)}개 항목")
                
                # 6. 대본 버튼 다시 눌러서 영상 목록으로 복귀
                self._close_transcript_panel()
                return True
            else:
                self.log_callback("     ⚠️ 대본 데이터를 찾을 수 없습니다.")
                self._close_transcript_panel()
                return False
                
        except Exception as e:
            self.log_callback(f"     ❌ 자막 추출 중 오류: {str(e)}")
            return False
    
    def _is_video_lecture(self, lecture: Lecture) -> bool:
        """영상 강의인지 확인 (xlink:href="#icon-video" 아이콘 체크)"""
        try:
            # TODO: 실제 강의 아이템 요소에서 비디오 아이콘 확인
            # 현재는 lecture 객체에 저장된 정보로 판단
            return lecture.has_subtitles  # 임시로 사용
            
        except Exception:
            return True  # 기본적으로 비디오로 가정
    
    def _click_lecture_item(self, lecture: Lecture) -> bool:
        """강의 아이템 클릭해서 영상 페이지로 이동"""
        try:
            self.log_callback(f"     🖱️ 강의 클릭: {lecture.title}")
            
            # TODO: 실제 강의 아이템 클릭 로직 구현
            # 현재는 URL로 직접 이동
            if lecture.video_url:
                self.driver.get(lecture.video_url)
                time.sleep(Config.PAGE_LOAD_DELAY)
                return True
            
            return False
            
        except Exception as e:
            self.log_callback(f"     ❌ 강의 클릭 실패: {str(e)}")
            return False
    
    def _wait_for_video_player(self) -> bool:
        """동영상 플레이어 로딩 대기"""
        try:
            self.log_callback("     ⏳ 동영상 플레이어 로딩 대기...")
            
            # 동영상 플레이어 요소들
            player_selectors = [
                "video",
                ".video-player",
                "[data-purpose='video-player']",
                ".vjs-tech",
                "iframe[src*='player']"
            ]
            
            for selector in player_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    self.log_callback("     ✅ 동영상 플레이어 로드 완료")
                    time.sleep(2)  # 추가 대기
                    return True
                except TimeoutException:
                    continue
            
            self.log_callback("     ⚠️ 동영상 플레이어를 찾을 수 없습니다.")
            return False
            
        except Exception as e:
            self.log_callback(f"     ❌ 동영상 플레이어 대기 중 오류: {str(e)}")
            return False
    
    def _click_transcript_button(self) -> bool:
        """마우스를 영상 영역으로 이동 후 대본 버튼 클릭"""
        try:
            self.log_callback("     🎬 영상 영역으로 마우스 이동 중...")
            
            # 1. 영상 영역 찾기
            video_area = self._find_video_area()
            if not video_area:
                self.log_callback("     ❌ 영상 영역을 찾을 수 없습니다.")
                return False
            
            # 2. 마우스를 영상 영역으로 이동
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.move_to_element(video_area).perform()
            time.sleep(1)
            
            # 3. 대본 버튼 찾기 및 클릭
            transcript_button = self._find_transcript_button()
            if not transcript_button:
                self.log_callback("     ❌ 대본 버튼을 찾을 수 없습니다.")
                return False
            
            # 4. 대본 버튼 클릭
            actions.click(transcript_button).perform()
            self.log_callback("     ✅ 대본 버튼 클릭 완료")
            
            # 5. 대본 패널 로딩 대기
            time.sleep(3)
            return self._wait_for_transcript_panel()
            
        except Exception as e:
            self.log_callback(f"     ❌ 대본 버튼 클릭 중 오류: {str(e)}")
            return False
    
    def _find_video_area(self):
        """영상 영역 찾기"""
        try:
            # TODO: 실제 영상 영역 선택자로 교체 필요
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
    
    def _find_transcript_button(self):
        """대본 버튼 찾기"""
        try:
            # TODO: 실제 대본 버튼 선택자로 교체 필요
            transcript_selectors = [
                "button[aria-label*='Transcript']",
                "button[aria-label*='transcript']",
                "button[aria-label*='대본']",
                "button[data-purpose='transcript-toggle']",
                ".transcript-button",
                "button[title*='Transcript']"
            ]
            
            for selector in transcript_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        return element
                except:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _wait_for_transcript_panel(self) -> bool:
        """대본 패널 로딩 대기"""
        try:
            self.log_callback("     ⏳ 대본 패널 로딩 대기...")
            
            # TODO: 실제 대본 패널 선택자로 교체 필요
            panel_selectors = [
                ".transcript-panel",
                ".sidebar-transcript", 
                "[data-purpose='transcript-container']",
                ".transcript-container"
            ]
            
            for selector in panel_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    self.log_callback("     ✅ 대본 패널 로드 완료")
                    return True
                except:
                    continue
            
            self.log_callback("     ⚠️ 대본 패널을 확인할 수 없지만 진행합니다.")
            return True
            
        except Exception:
            return False
    
    def _click_subtitle_button(self) -> bool:
        """자막 버튼 클릭"""
        try:
            # CC 버튼 선택자들
            cc_selectors = [
                "button[aria-label*='Captions']",
                "button[aria-label*='Subtitles']",
                "button[aria-label*='CC']",
                ".vjs-captions-button",
                ".vjs-subtitles-button",
                "[data-purpose='captions-dropdown-trigger']",
                "button[class*='caption']",
                "button[class*='subtitle']"
            ]
            
            for selector in cc_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button and button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", button)
                        self.log_callback("     ✅ 자막 버튼 클릭 성공")
                        return True
                except:
                    continue
            
            # XPath로도 시도
            xpath_selectors = [
                "//button[contains(@aria-label, 'Caption')]",
                "//button[contains(@aria-label, 'Subtitle')]", 
                "//button[contains(text(), 'CC')]",
                "//button[contains(@class, 'caption')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, xpath)
                    if button and button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", button)
                        self.log_callback("     ✅ 자막 버튼 클릭 성공 (XPath)")
                        return True
                except:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def _try_alternative_subtitle_methods(self) -> bool:
        """대체 자막 활성화 방법들"""
        try:
            # 키보드 단축키 시도 (C 키)
            try:
                from selenium.webdriver.common.keys import Keys
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys("c")
                time.sleep(1)
                self.log_callback("     ✅ 키보드 단축키로 자막 활성화 시도")
                return True
            except:
                pass
            
            # 우클릭 메뉴 시도
            try:
                video = self.driver.find_element(By.TAG_NAME, "video")
                ActionChains(self.driver).context_click(video).perform()
                time.sleep(1)
                # 자막 메뉴 항목 클릭 시도
                caption_menu = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Caption') or contains(text(), 'Subtitle')]")
                caption_menu.click()
                return True
            except:
                pass
            
            return False
            
        except Exception:
            return False
    
    def _extract_transcript_from_sidebar(self) -> List[Subtitle]:
        """우측 대본 패널에서 대본 추출"""
        try:
            self.log_callback("     📖 대본 데이터 추출 중...")
            
            # 1. 대본 패널 영역 찾기
            transcript_panel = self._find_transcript_panel_area()
            if not transcript_panel:
                self.log_callback("     ❌ 대본 패널을 찾을 수 없습니다.")
                return []
            
            # 2. 스크롤을 최상단으로 이동
            self._scroll_transcript_to_top(transcript_panel)
            
            # 3. 모든 대본 요소들 수집 (스크롤하면서)
            all_subtitles = []
            
            # 첫 번째 시도: 현재 보이는 모든 대본 요소 한번에 수집
            subtitles = self._extract_all_transcript_elements(transcript_panel)
            if subtitles:
                self.log_callback(f"     ✅ 대본 추출 성공: {len(subtitles)}개 항목")
                return subtitles
            
            # 두 번째 시도: 스크롤하면서 수집 (인프런 방식)
            subtitles = self._extract_with_scrolling(transcript_panel)
            if subtitles:
                self.log_callback(f"     ✅ 스크롤 대본 추출 성공: {len(subtitles)}개 항목")
                return subtitles
            
            return []
            
        except Exception as e:
            self.log_callback(f"     ❌ 대본 추출 중 오류: {str(e)}")
            return []
    
    def _find_transcript_panel_area(self):
        """대본 패널 영역 찾기"""
        try:
            # TODO: 실제 대본 패널 영역 선택자로 교체 필요
            panel_selectors = [
                ".transcript-panel",
                ".sidebar-transcript",
                "[data-purpose='transcript-container']",
                ".transcript-container",
                ".transcript-sidebar"
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
    
    def _scroll_transcript_to_top(self, panel_element):
        """대본 패널을 최상단으로 스크롤"""
        try:
            self.driver.execute_script("arguments[0].scrollTop = 0;", panel_element)
            time.sleep(1)
        except Exception:
            pass
    
    def _extract_all_transcript_elements(self, panel_element) -> List[Subtitle]:
        """패널 내 모든 대본 요소 한번에 추출"""
        try:
            # TODO: 실제 대본 요소 선택자로 교체 필요
            transcript_item_selectors = [
                "[data-purpose='transcript-cue']",
                ".transcript-item",
                ".transcript-cue",
                ".caption-item"
            ]
            
            for selector in transcript_item_selectors:
                try:
                    elements = panel_element.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return self._parse_transcript_elements(elements)
                except:
                    continue
            
            return []
            
        except Exception:
            return []
    
    def _extract_with_scrolling(self, panel_element) -> List[Subtitle]:
        """스크롤하면서 대본 요소 수집 (인프런 방식)"""
        try:
            all_subtitles = []
            seen_texts = set()
            scroll_attempts = 0
            max_scrolls = 50
            
            while scroll_attempts < max_scrolls:
                # 현재 보이는 대본 요소들 수집
                current_elements = self._get_visible_transcript_elements(panel_element)
                
                new_items_found = False
                for element in current_elements:
                    subtitle = self._parse_single_transcript_element(element)
                    if subtitle and subtitle.text not in seen_texts:
                        all_subtitles.append(subtitle)
                        seen_texts.add(subtitle.text)
                        new_items_found = True
                
                # 스크롤 다운
                self.driver.execute_script(
                    "arguments[0].scrollTop += arguments[0].clientHeight / 2;", 
                    panel_element
                )
                time.sleep(0.5)
                
                # 새로운 항목이 없으면 종료
                if not new_items_found:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                
                # 끝에 도달했는지 확인
                if self._is_at_bottom(panel_element):
                    break
            
            # 타임스탬프 순으로 정렬
            all_subtitles.sort(key=lambda x: x.start_seconds)
            return all_subtitles
            
        except Exception as e:
            self.log_callback(f"     ❌ 스크롤 추출 중 오류: {str(e)}")
            return []
    
    def _get_visible_transcript_elements(self, panel_element):
        """현재 보이는 대본 요소들 가져오기"""
        try:
            # TODO: 실제 대본 요소 선택자로 교체 필요
            selectors = [
                "[data-purpose='transcript-cue']",
                ".transcript-item",
                ".transcript-cue"
            ]
            
            for selector in selectors:
                try:
                    elements = panel_element.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return elements
                except:
                    continue
            
            return []
            
        except Exception:
            return []
    
    def _parse_transcript_elements(self, elements) -> List[Subtitle]:
        """대본 요소들을 파싱해서 Subtitle 객체로 변환"""
        try:
            subtitles = []
            
            for element in elements:
                subtitle = self._parse_single_transcript_element(element)
                if subtitle:
                    subtitles.append(subtitle)
            
            return subtitles
            
        except Exception:
            return []
    
    def _parse_single_transcript_element(self, element) -> Optional[Subtitle]:
        """단일 대본 요소 파싱"""
        try:
            # 텍스트 추출
            text = element.text.strip()
            if not text:
                return None
            
            # 타임스탬프 추출 (data 속성 또는 텍스트에서)
            timestamp_seconds = self._extract_timestamp_from_element(element)
            timestamp_formatted = self._seconds_to_timestamp(timestamp_seconds)
            
            return Subtitle(
                timestamp=timestamp_formatted,
                text=text,
                start_seconds=timestamp_seconds,
                end_seconds=timestamp_seconds
            )
            
        except Exception:
            return None
    
    def _extract_timestamp_from_element(self, element) -> float:
        """요소에서 타임스탬프 추출"""
        try:
            # TODO: 실제 타임스탬프 추출 로직 구현
            # data 속성에서 시간 정보 추출
            time_attrs = ['data-time', 'data-start', 'data-timestamp']
            
            for attr in time_attrs:
                value = element.get_attribute(attr)
                if value:
                    try:
                        return float(value)
                    except:
                        continue
            
            # 클릭 이벤트에서 시간 정보 추출
            onclick = element.get_attribute('onclick')
            if onclick:
                import re
                time_match = re.search(r'(\d+\.?\d*)', onclick)
                if time_match:
                    return float(time_match.group(1))
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _is_at_bottom(self, panel_element) -> bool:
        """스크롤이 끝에 도달했는지 확인"""
        try:
            script = """
            var element = arguments[0];
            return element.scrollTop + element.clientHeight >= element.scrollHeight - 10;
            """
            return self.driver.execute_script(script, panel_element)
        except:
            return False
    
    def _close_transcript_panel(self):
        """대본 패널 닫기 (대본 버튼 다시 클릭)"""
        try:
            self.log_callback("     🔄 대본 패널 닫는 중...")
            
            # 대본 버튼 다시 찾아서 클릭
            transcript_button = self._find_transcript_button()
            if transcript_button:
                transcript_button.click()
                self.log_callback("     ✅ 대본 패널 닫기 완료")
                time.sleep(2)
            
        except Exception as e:
            self.log_callback(f"     ⚠️ 대본 패널 닫기 실패: {str(e)}")
    
    def _extract_subtitle_data(self) -> List[Subtitle]:
        """자막 데이터 추출 (기존 방식 - 백업용)"""
        return self._extract_transcript_from_sidebar()
    
    def _extract_from_vtt_track(self) -> List[Subtitle]:
        """VTT 트랙에서 자막 추출"""
        try:
            # HTML5 video track 요소들 찾기
            tracks = self.driver.find_elements(By.TAG_NAME, "track")
            
            for track in tracks:
                src = track.get_attribute("src")
                kind = track.get_attribute("kind")
                
                if kind == "captions" or kind == "subtitles":
                    if src:
                        return self._download_and_parse_vtt(src)
            
            return []
            
        except Exception:
            return []
    
    def _download_and_parse_vtt(self, vtt_url: str) -> List[Subtitle]:
        """VTT 파일 다운로드 및 파싱"""
        try:
            import requests
            
            # 현재 세션의 쿠키 가져오기
            cookies = {}
            for cookie in self.driver.get_cookies():
                cookies[cookie['name']] = cookie['value']
            
            # VTT 파일 다운로드
            headers = {
                'User-Agent': self.driver.execute_script("return navigator.userAgent;")
            }
            
            response = requests.get(vtt_url, cookies=cookies, headers=headers)
            response.raise_for_status()
            
            # VTT 내용 파싱
            return self._parse_vtt_content(response.text)
            
        except Exception as e:
            self.log_callback(f"     ❌ VTT 다운로드 실패: {str(e)}")
            return []
    
    def _parse_vtt_content(self, vtt_content: str) -> List[Subtitle]:
        """VTT 내용 파싱"""
        try:
            subtitles = []
            lines = vtt_content.strip().split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 타임스탬프 라인 찾기 (00:00:00.000 --> 00:00:05.000)
                if '-->' in line:
                    timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})', line)
                    if timestamp_match:
                        start_time = timestamp_match.group(1)
                        end_time = timestamp_match.group(2)
                        
                        # 다음 라인부터 자막 텍스트 수집
                        i += 1
                        subtitle_text = []
                        
                        while i < len(lines) and lines[i].strip():
                            subtitle_text.append(lines[i].strip())
                            i += 1
                        
                        if subtitle_text:
                            # 타임스탬프를 HH:MM:SS 형식으로 변환
                            formatted_time = self._convert_vtt_timestamp(start_time)
                            start_seconds = self._timestamp_to_seconds(start_time)
                            end_seconds = self._timestamp_to_seconds(end_time)
                            
                            subtitle = Subtitle(
                                timestamp=formatted_time,
                                text=' '.join(subtitle_text),
                                start_seconds=start_seconds,
                                end_seconds=end_seconds
                            )
                            subtitles.append(subtitle)
                
                i += 1
            
            return subtitles
            
        except Exception as e:
            self.log_callback(f"     ❌ VTT 파싱 실패: {str(e)}")
            return []
    
    def _extract_from_subtitle_elements(self) -> List[Subtitle]:
        """DOM의 자막 요소들에서 추출"""
        try:
            subtitle_selectors = [
                ".vjs-text-track-display",
                ".captions-text",
                ".subtitle-text",
                "[class*='caption']",
                "[class*='subtitle']"
            ]
            
            for selector in subtitle_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # 현재 표시된 자막만 가져올 수 있음 (제한적)
                        return self._extract_current_subtitle(elements[0])
                except:
                    continue
            
            return []
            
        except Exception:
            return []
    
    def _extract_from_api_calls(self) -> List[Subtitle]:
        """네트워크 API 호출에서 자막 데이터 추출"""
        try:
            # 브라우저 네트워크 로그에서 자막 관련 요청 찾기
            logs = self.driver.get_log('performance')
            
            for log in logs:
                message = json.loads(log['message'])
                
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    
                    # 자막 관련 URL 패턴
                    if any(pattern in url.lower() for pattern in ['caption', 'subtitle', '.vtt', '.srt']):
                        try:
                            # 응답 내용 가져오기
                            request_id = message['message']['params']['requestId']
                            response = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            
                            if 'body' in response:
                                return self._parse_subtitle_response(response['body'])
                        except:
                            continue
            
            return []
            
        except Exception:
            return []
    
    def _extract_from_dom_subtitles(self) -> List[Subtitle]:
        """DOM에서 자막 정보 추출 (최후 수단)"""
        try:
            # 페이지 소스에서 자막 데이터 패턴 찾기
            page_source = self.driver.page_source
            
            # JSON 형태의 자막 데이터 찾기
            subtitle_patterns = [
                r'"captions":\s*(\[.*?\])',
                r'"subtitles":\s*(\[.*?\])',
                r'"tracks":\s*(\[.*?\])',
            ]
            
            for pattern in subtitle_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    try:
                        data = json.loads(match)
                        subtitles = self._parse_json_subtitles(data)
                        if subtitles:
                            return subtitles
                    except:
                        continue
            
            return []
            
        except Exception:
            return []
    
    def _parse_json_subtitles(self, data) -> List[Subtitle]:
        """JSON 형태의 자막 데이터 파싱"""
        try:
            subtitles = []
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # 시간과 텍스트 정보 추출
                        text = item.get('text', '')
                        start_time = item.get('start', item.get('startTime', 0))
                        end_time = item.get('end', item.get('endTime', 0))
                        
                        if text and start_time is not None:
                            formatted_time = self._seconds_to_timestamp(float(start_time))
                            
                            subtitle = Subtitle(
                                timestamp=formatted_time,
                                text=text.strip(),
                                start_seconds=float(start_time),
                                end_seconds=float(end_time) if end_time else float(start_time)
                            )
                            subtitles.append(subtitle)
            
            return subtitles
            
        except Exception:
            return []
    
    def _convert_vtt_timestamp(self, vtt_time: str) -> str:
        """VTT 타임스탬프를 HH:MM:SS 형식으로 변환"""
        try:
            # 00:00:15.500 -> 00:00:15
            return vtt_time.split('.')[0]
        except:
            return "00:00:00"
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """타임스탬프를 초 단위로 변환"""
        try:
            # 00:05:30.500 -> 330.5 seconds
            parts = timestamp.split(':')
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds_part = parts[2].split('.') if '.' in parts[2] else [parts[2], '0']
            seconds = float(seconds_part[0])
            milliseconds = float(seconds_part[1]) / 1000 if len(seconds_part) > 1 else 0
            
            return hours * 3600 + minutes * 60 + seconds + milliseconds
        except:
            return 0.0
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """초를 HH:MM:SS 형식으로 변환"""
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        except:
            return "00:00:00"
    
    def _extract_current_subtitle(self, subtitle_element) -> List[Subtitle]:
        """현재 표시된 자막만 추출 (제한적)"""
        try:
            text = subtitle_element.text.strip()
            if text:
                # 현재 시간 가져오기 (비디오 요소에서)
                try:
                    video = self.driver.find_element(By.TAG_NAME, "video")
                    current_time = float(video.get_attribute("currentTime") or 0)
                    formatted_time = self._seconds_to_timestamp(current_time)
                    
                    return [Subtitle(
                        timestamp=formatted_time,
                        text=text,
                        start_seconds=current_time,
                        end_seconds=current_time
                    )]
                except:
                    return [Subtitle(
                        timestamp="00:00:00",
                        text=text,
                        start_seconds=0.0,
                        end_seconds=0.0
                    )]
            
            return []
            
        except Exception:
            return []
    
    def _parse_subtitle_response(self, response_body: str) -> List[Subtitle]:
        """API 응답에서 자막 파싱"""
        try:
            # VTT 형식인지 확인
            if 'WEBVTT' in response_body:
                return self._parse_vtt_content(response_body)
            
            # JSON 형식인지 확인
            try:
                data = json.loads(response_body)
                return self._parse_json_subtitles(data)
            except:
                pass
            
            return []
            
        except Exception:
            return []
