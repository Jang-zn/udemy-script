"""
데이터 모델 클래스들
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Subtitle:
    """자막 데이터 모델"""
    timestamp: str  # "00:05:30" 형식
    text: str
    start_seconds: float = 0.0
    end_seconds: float = 0.0

@dataclass
class Lecture:
    """강의 데이터 모델"""
    title: str
    duration: str
    video_url: Optional[str] = None
    has_subtitles: bool = False
    subtitles: List[Subtitle] = None
    lecture_index: int = 0
    
    def __post_init__(self):
        if self.subtitles is None:
            self.subtitles = []

@dataclass
class Section:
    """섹션 데이터 모델"""
    title: str
    lectures: List[Lecture] = None
    section_index: int = 0
    
    def __post_init__(self):
        if self.lectures is None:
            self.lectures = []
    
    @property
    def total_duration(self) -> str:
        """섹션 총 재생시간 계산"""
        # 추후 구현 (강의 duration 파싱 필요)
        return "계산 중..."
    
    @property
    def lecture_count(self) -> int:
        """섹션 내 강의 수"""
        return len(self.lectures)

@dataclass
class Course:
    """강의 데이터 모델"""
    title: str
    instructor: str = ""
    description: str = ""
    sections: List[Section] = None
    total_duration: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.sections is None:
            self.sections = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def total_lectures(self) -> int:
        """전체 강의 수"""
        return sum(section.lecture_count for section in self.sections)
    
    @property
    def total_sections(self) -> int:
        """전체 섹션 수"""
        return len(self.sections)

@dataclass
class ScrapingProgress:
    """스크래핑 진행 상황 모델"""
    current_section: int = 0
    current_lecture: int = 0
    total_sections: int = 0
    total_lectures: int = 0
    completed_lectures: int = 0
    errors: List[str] = None
    start_time: datetime = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def progress_percentage(self) -> float:
        """진행률 계산 (0-100%)"""
        if self.total_lectures == 0:
            return 0.0
        return (self.completed_lectures / self.total_lectures) * 100
    
    @property
    def estimated_time_remaining(self) -> str:
        """예상 남은 시간 (추후 구현)"""
        return "계산 중..."
    
    def add_error(self, error_message: str):
        """에러 추가"""
        self.errors.append(f"[{datetime.now().strftime('%H:%M:%S')}] {error_message}")
    
    def get_status_message(self) -> str:
        """현재 상태 메시지 반환"""
        return f"섹션 {self.current_section}/{self.total_sections} - 강의 {self.current_lecture}/{self.total_lectures} ({self.progress_percentage:.1f}%)"


