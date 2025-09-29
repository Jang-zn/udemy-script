"""
Udemy 스크래퍼 메인 워크플로우 컨트롤러
"""

import time
from typing import Callable, Optional
from config import Config
from browser.auth import UdemyAuth
from browser.navigation import UdemyNavigator
from browser.transcript_scraper import TranscriptScraper
from utils.file_utils import MarkdownGenerator
from core.models import Course, ScrapingProgress

class UdemyScraperApp:
    def __init__(self, 
                 progress_callback: Optional[Callable] = None,
                 status_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        """
        메인 스크래퍼 앱 초기화
        
        Args:
            progress_callback: 진행률 업데이트 콜백 (current, total)
            status_callback: 상태 메시지 업데이트 콜백 (message)
            log_callback: 로그 메시지 콜백 (message)
        """
        self.progress_callback = progress_callback or (lambda c, t: None)
        self.status_callback = status_callback or (lambda m: None)
        self.log_callback = log_callback or print
        
        # 컴포넌트 초기화
        self.auth = None
        self.navigator = None
        self.scraper = None
        self.markdown_generator = None
        
        # 진행 상황 추적
        self.progress = ScrapingProgress()
        
    def run_workflow(self, course_name: str) -> bool:
        """
        전체 스크래핑 워크플로우 실행

        Args:
            course_name: 추출할 강의명

        Returns:
            bool: 성공 여부
        """
        try:
            # 1. 초기화
            if not self._initialize_components():
                return False
            
            # 2. 강의 선택
            self.status_callback("강의 검색 중...")
            course = self._select_course(course_name)
            if not course:
                return False
            
            # 3. 강의 구조 분석
            self.status_callback("강의 구조 분석 중...")
            if not self._analyze_course_structure(course):
                return False

            # 4. 자막 추출
            self.status_callback("자막 추출 시작...")
            if not self._extract_all_subtitles(course):
                return False

            # 5. 파일 저장
            self.status_callback("파일 저장 중...")
            if not self._save_course_files(course, course_name):
                return False
            
            self.log_callback("🎉 모든 작업이 완료되었습니다!")
            return True
            
        except Exception as e:
            self.log_callback(f"❌ 워크플로우 실행 중 오류: {str(e)}")
            return False
        finally:
            self.cleanup()
    
    def _initialize_components(self) -> bool:
        """컴포넌트 초기화"""
        try:
            self.log_callback("🔧 컴포넌트 초기화 중...")
            
            # 필요한 디렉토리 생성
            Config.ensure_directories()
            
            # Auth 컴포넌트 초기화
            self.auth = UdemyAuth(
                headless=Config.HEADLESS_MODE,
                log_callback=self.log_callback
            )

            if not self.auth.setup_driver():
                self.log_callback("❌ 브라우저 초기화 실패")
                return False
            
            # 다른 컴포넌트들 초기화
            self.navigator = UdemyNavigator(
                driver=self.auth.driver,
                wait=self.auth.wait,
                log_callback=self.log_callback
            )
            
            self.scraper = TranscriptScraper(
                driver=self.auth.driver,
                wait=self.auth.wait,
                log_callback=self.log_callback
            )
            
            self.markdown_generator = MarkdownGenerator(
                log_callback=self.log_callback
            )
            
            self.log_callback("✅ 컴포넌트 초기화 완료")
            return True
            
        except Exception as e:
            self.log_callback(f"❌ 컴포넌트 초기화 실패: {str(e)}")
            return False
    
    def _select_course(self, course_name: str) -> Optional[Course]:
        """강의 선택"""
        try:
            # My Learning 페이지로 이동
            if not self.navigator.go_to_my_learning():
                return None
            
            # 강의 검색 및 선택
            course = self.navigator.search_and_select_course(course_name)
            if course:
                self.log_callback(f"✅ 강의 선택 완료: {course.title}")
            else:
                self.log_callback(f"❌ 강의를 찾을 수 없습니다: {course_name}")
            
            return course
            
        except Exception as e:
            self.log_callback(f"❌ 강의 선택 중 오류: {str(e)}")
            return None
    
    def _analyze_course_structure(self, course: Course) -> bool:
        """강의 구조 분석"""
        try:
            # 커리큘럼 분석
            success = self.navigator.analyze_curriculum(course)
            if success:
                self.progress.total_sections = course.total_sections
                self.progress.total_lectures = course.total_lectures
                
                self.log_callback(f"📚 강의 구조 분석 완료:")
                self.log_callback(f"   - 총 섹션: {course.total_sections}개")
                self.log_callback(f"   - 총 강의: {course.total_lectures}개")
            else:
                self.log_callback("❌ 강의 구조 분석 실패")
            
            return success
            
        except Exception as e:
            self.log_callback(f"❌ 강의 구조 분석 중 오류: {str(e)}")
            return False
    
    def _extract_all_subtitles(self, course: Course) -> bool:
        """모든 강의의 자막 추출 (리팩토링된 TranscriptScraper 사용)"""
        try:
            self.log_callback("🎬 자막 추출 시작...")

            # 새로운 TranscriptScraper의 전체 워크플로우 사용
            success = self.scraper.start_complete_scraping_workflow(course)

            if success:
                # 진행률 업데이트 (완료로 설정)
                self.progress.completed_lectures = self.progress.total_lectures
                self.progress_callback(
                    self.progress.completed_lectures,
                    self.progress.total_lectures
                )
                self.log_callback("✅ 모든 강의 자막 추출 완료")
            else:
                self.log_callback("❌ 자막 추출 중 오류 발생")

            return success
            
        except Exception as e:
            self.log_callback(f"❌ 자막 추출 중 오류: {str(e)}")
            return False
    
    def _save_course_files(self, course: Course, course_name: str) -> bool:
        """강의 파일 저장"""
        try:
            output_dir = Config.get_course_output_dir(course_name)
            
            self.log_callback(f"💾 파일 저장 시작: {output_dir}")
            
            # 각 섹션별로 Markdown 파일 생성
            for section_idx, section in enumerate(course.sections):
                self.log_callback(f"  📄 섹션 {section_idx + 1} 파일 생성 중...")
                
                success = self.markdown_generator.create_section_file(
                    section, output_dir, section_idx + 1
                )
                
                if success:
                    self.log_callback(f"     ✅ 저장 완료")
                else:
                    self.log_callback(f"     ❌ 저장 실패")
                    return False
            
            # 전체 요약 파일 생성 (선택사항)
            self.markdown_generator.create_course_summary(course, output_dir)
            
            self.log_callback(f"✅ 모든 파일 저장 완료: {output_dir}")
            return True
            
        except Exception as e:
            self.log_callback(f"❌ 파일 저장 중 오류: {str(e)}")
            return False
    
    def cleanup(self):
        """리소스 정리"""
        try:
            if self.auth:
                self.auth.cleanup()
            self.log_callback("🧹 리소스 정리 완료")
        except Exception as e:
            self.log_callback(f"⚠️ 리소스 정리 중 오류: {str(e)}")
    
    def get_progress_info(self) -> dict:
        """현재 진행 상황 정보 반환"""
        return {
            'current_section': self.progress.current_section,
            'total_sections': self.progress.total_sections,
            'current_lecture': self.progress.current_lecture,
            'total_lectures': self.progress.total_lectures,
            'completed_lectures': self.progress.completed_lectures,
            'progress_percentage': self.progress.progress_percentage,
            'errors': len(self.progress.errors),
            'status_message': self.progress.get_status_message()
        }


