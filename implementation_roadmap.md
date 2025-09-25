# Udemy 스크래퍼 구현 로드맵

## 🎯 개발 우선순위 및 마일스톤

### Phase 1: 기본 인프라 구축 (Day 1-2)

#### 1.1 프로젝트 구조 생성
```bash
udemy_scraper/
├── __init__.py
├── ui.py              # GUI 메인 인터페이스
├── app.py             # 워크플로우 컨트롤러
├── auth.py            # 로그인 모듈
├── navigation.py      # 페이지 탐색
├── scraper.py         # 자막 추출
├── config.py          # 설정 관리
├── file_utils.py      # 파일 처리
├── models.py          # 데이터 모델
└── utils.py           # 유틸리티 함수
```

#### 1.2 의존성 설정 및 환경 구성
- [x] requirements.txt 작성
- [x] .env.sample 템플릿 생성
- [x] config.py 기본 설정값 정의
- [x] logging 설정 및 디버그 모드

#### 1.3 기본 GUI 프레임워크
- [x] tkinter 기본 레이아웃
- [x] 입력 필드 3개 (이메일, 패스워드, 강의명)
- [x] 시작 버튼 및 상태 표시
- [x] .env 파일 자동 로드

### Phase 2: 인증 및 탐색 로직 (Day 3-5)

#### 2.1 Selenium 기반 브라우저 자동화 (반자동 로그인)
```python
# auth.py 핵심 구현
class UdemyAuth:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
    
    def setup_driver(self):
        # Chrome 옵션 설정
        # User-Agent 설정
        # 세션 저장 디렉토리 설정
    
    def semi_automatic_login(self, email, password):
        # 1. 저장된 세션 쿠키 로드 시도
        if self.load_saved_session():
            return True
            
        # 2. 로그인 페이지 이동
        # 3. 이메일/패스워드 자동 입력
        # 4. "이메일 인증 코드 입력하세요" 안내 표시
        # 5. 로그인 완료까지 대기 (수동 2FA)
        # 6. 세션 쿠키 저장
        
    def wait_for_manual_2fa(self):
        print("📧 이메일에서 인증 코드 확인 후 입력해주세요...")
        print("⏳ 로그인 완료까지 대기 중...")
        
        while not self.check_login_success():
            time.sleep(2)
        print("✅ 로그인 완료!")
        self.save_session_cookies()
```

#### 2.2 강의 탐색 및 선택
```python
# navigation.py 핵심 구현
class UdemyNavigator:
    def go_to_my_learning(self):
        # "My learning" 페이지 이동
        
    def search_course(self, course_name):
        # 강의명으로 검색
        # fuzzy matching 지원
        
    def select_course(self, course_element):
        # 강의 선택 및 커리큘럼 페이지 이동
```

#### 2.3 강의 구조 분석
```python
# models.py 데이터 모델
@dataclass
class Course:
    title: str
    sections: List[Section]

@dataclass  
class Section:
    title: str
    lectures: List[Lecture]

@dataclass
class Lecture:
    title: str
    duration: str
    video_url: str
    has_subtitles: bool
```

### Phase 3: 자막 추출 핵심 로직 (Day 6-9)

#### 3.1 자막 접근 메커니즘
```python
# scraper.py 핵심 구현
class SubtitleScraper:
    def extract_course_subtitles(self, course_url):
        # 강의 구조 파싱
        # 섹션별 순회
        # 각 강의별 자막 추출
        
    def extract_lecture_subtitles(self, lecture_url):
        # 동영상 플레이어 접근
        # CC 버튼 클릭
        # 자막 패널 활성화
        # 자막 데이터 추출
```

#### 3.2 자막 형식 처리
```python
# VTT 형식 파싱
def parse_vtt_subtitles(self, vtt_content):
    # WebVTT 타임스탬프 파싱
    # 텍스트 정리 및 정규화
    # Subtitle 객체 리스트 반환

# JSON API 형식 처리  
def parse_json_subtitles(self, json_data):
    # API 응답 데이터 파싱
    # 타임스탬프 변환
    # 다국어 처리
```

#### 3.3 다국어 및 에러 처리
```python
def detect_subtitle_language(self):
    # 사용 가능한 언어 감지
    # 한국어 우선 선택
    # 영어 대체 선택

def handle_extraction_errors(self):
    # DRM 보호 콘텐츠 감지
    # 자막 없는 강의 스킵
    # 네트워크 오류 재시도
```

### Phase 4: 파일 처리 및 통합 (Day 10-11)

#### 4.1 Markdown 생성
```python
# file_utils.py 핵심 구현
class MarkdownGenerator:
    def create_section_file(self, section, output_dir):
        # 섹션별 Markdown 파일 생성
        # 타임스탬프 포맷팅
        # 강의별 구분자 추가
        
    def format_timestamp(self, seconds):
        # "00:05:30" 형식으로 변환
        
    def sanitize_filename(self, title):
        # 파일명 특수문자 제거
        # 길이 제한 적용
```

#### 4.2 진행 상황 모니터링
```python
# app.py 워크플로우 통합
class UdemyScraperApp:
    def run_scraping_workflow(self):
        # 1. 로그인 처리
        # 2. 강의 선택
        # 3. 구조 분석
        # 4. 자막 추출 (진행률 표시)
        # 5. 파일 저장
        
    def update_progress(self, current, total, message):
        # GUI 상태 업데이트
        # 콘솔 로그 출력
```

### Phase 5: 테스트 및 최적화 (Day 12-14)

#### 5.1 통합 테스트
- [x] 다양한 강의 타입 테스트
- [x] 긴 강의 처리 테스트 (메모리 관리)
- [x] 네트워크 오류 시뮬레이션
- [x] DRM 보호 콘텐츠 처리

#### 5.2 성능 최적화
```python
# 메모리 최적화
def cleanup_browser_resources(self):
    # 불필요한 탭 정리
    # 캐시 클리어
    
# 배치 처리
def process_in_batches(self, lectures, batch_size=5):
    # 5개 강의마다 중간 저장
    # 메모리 사용량 모니터링
```

#### 5.3 에러 처리 강화
```python
# 복구 메커니즘
class RecoveryManager:
    def save_checkpoint(self, section_index, lecture_index):
        # 진행 상황 저장
        
    def resume_from_checkpoint(self):
        # 중단점부터 재시작
        
    def handle_browser_crash(self):
        # 브라우저 재시작
        # 세션 복구
```

## 🔧 구현 시 주의사항

### 1. Udemy 플랫폼 특성
- **동적 로딩**: 모든 요소에 Explicit Wait 적용
- **자동화 탐지**: User-Agent, 대기시간 랜덤화
- **세션 관리**: 로그인 상태 유지 및 확인

### 2. 안정성 확보
- **예외 처리**: 모든 Selenium 작업에 try-catch
- **재시도 로직**: 네트워크 오류 시 최대 3회 재시도
- **로그 기록**: 상세한 실행 로그 및 에러 스택 트레이스

### 3. 성능 고려사항
- **메모리 관리**: 대용량 강의 처리 시 메모리 누수 방지
- **병렬 처리**: 자막 추출과 파일 저장 비동기 처리
- **사용자 경험**: 실시간 진행 상황 표시

## 📋 체크리스트

### 필수 구현 항목
- [ ] tkinter GUI 기본 인터페이스
- [ ] Udemy 로그인 자동화
- [ ] "My learning" 페이지 탐색
- [ ] 강의 검색 및 선택
- [ ] 강의 구조 (섹션/강의) 파싱
- [ ] 자막 패널 접근 및 데이터 추출
- [ ] VTT/JSON 자막 형식 처리
- [ ] 섹션별 Markdown 파일 생성
- [ ] 진행 상황 모니터링
- [ ] 에러 처리 및 복구

### 추가 기능 (선택사항)
- [ ] 2FA 자동 처리
- [ ] 다국어 자막 선택
- [ ] 헤드리스 모드 지원
- [ ] 배치 처리 및 스케줄링
- [ ] 강의 완료 상태 추적

### 테스트 시나리오
- [ ] 짧은 강의 (1-2시간) 전체 추출
- [ ] 긴 강의 (10시간+) 안정성 테스트
- [ ] 네트워크 불안정 환경 테스트
- [ ] DRM 보호 강의 감지 테스트
- [ ] 자막 없는 강의 처리 테스트

---

**로드맵 작성일**: 2025년 9월 17일  
**예상 완료일**: 2025년 9월 30일  
**총 개발 기간**: 14일
