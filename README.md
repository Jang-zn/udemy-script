# Udemy Script Scraper

Udemy 강의의 자막(Transcript)을 자동으로 추출하여 마크다운 형식으로 저장하는 도구입니다.

## 📋 목차

- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 설정](#설치-및-설정)
- [사용 방법](#사용-방법)
- [작동 방식](#작동-방식)
- [주요 컴포넌트 설명](#주요-컴포넌트-설명)
- [출력 결과](#출력-결과)
- [문제 해결](#문제-해결)
- [개발 가이드](#개발-가이드)

## 🎯 주요 기능

- **자동 강의 자막 추출**: Udemy 강의의 트랜스크립트를 자동으로 추출
- **섹션별 구조화**: 섹션과 강의 단위로 체계적으로 저장
- **자동 병합**: 섹션별로 모든 강의 자막을 하나의 마크다운 파일로 통합
- **GUI 지원**: 간단한 PySide6 기반 GUI 제공
- **디버그 모드**: Chrome DevTools Protocol을 활용한 디버그 브라우저 모드 지원
- **재시도 로직**: 실패 시 자동 재시도로 안정성 향상

## 🛠 기술 스택

### 코어 기술
- **Python 3.10+**: 메인 프로그래밍 언어
- **Selenium 4.15+**: 웹 브라우저 자동화
- **PySide6**: GUI 프레임워크
- **BeautifulSoup4**: HTML 파싱 (필요시)

### 주요 라이브러리
```txt
selenium>=4.15.0
webdriver-manager>=4.0.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
requests>=2.31.0
lxml>=4.9.0
```

## 📁 프로젝트 구조

```
udemy-script/
├── main.py                    # 프로그램 진입점
├── app.py                     # 메인 워크플로우 컨트롤러
├── section_merger.py          # 섹션별 자막 병합 기능
├── file_utils.py              # 파일 유틸리티 (deprecated)
│
├── browser/                   # 브라우저 자동화 모듈
│   ├── auth.py               # Udemy 인증 및 브라우저 설정
│   ├── navigation.py         # 페이지 네비게이션
│   ├── transcript_scraper.py # 자막 추출 메인 로직
│   ├── transcript_extractor.py # 트랜스크립트 추출 헬퍼
│   ├── element_finder.py     # DOM 요소 검색 유틸
│   ├── smart_waiter.py       # 스마트 대기 로직
│   ├── curriculum_analyzer.py # 강의 구조 분석
│   ├── course_finder.py      # 강의 검색
│   ├── selectors.py          # CSS 셀렉터 정의
│   ├── manager.py            # 브라우저 관리
│   └── base.py               # 베이스 클래스
│
├── config/                    # 설정 관리
│   └── settings.py           # 전역 설정
│
├── core/                      # 핵심 데이터 모델
│   └── models.py             # 데이터 클래스 정의
│
├── gui/                       # GUI 관련
│   └── simple_ui.py          # 간단한 GUI 구현
│
├── utils/                     # 유틸리티
│   └── file_utils.py         # 파일 처리 유틸
│
├── output/                    # 결과물 저장 디렉토리
├── sessions/                  # 브라우저 세션 저장
├── requirements.txt           # 의존성 목록
└── env_sample.txt            # 환경변수 샘플
```

## 📦 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd udemy-script
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정 (선택사항)

```bash
cp env_sample.txt .env
```

`.env` 파일 내용:
```
# Udemy 계정 정보 (선택사항 - GUI에서 직접 입력 가능)
UDEMY_EMAIL=your_email@example.com
UDEMY_PASSWORD=your_password

# 기본 설정
OUTPUT_DIR=output
HEADLESS_MODE=false
DEBUG_MODE=true
```

> **참고**: `HEADLESS_MODE`는 항상 `false`로 설정됩니다 (2FA 수동 입력 필요).

## 🚀 사용 방법

### GUI 모드 (권장)

```bash
python main.py
```

GUI에서:
1. **"디버그 브라우저"** 버튼 클릭 → Chrome 브라우저가 열리고 Udemy 로그인 수동 진행
2. 로그인 완료 후 원하는 강의로 이동
3. GUI에서 **강의명 입력** (부분 일치 검색 지원)
4. **"브라우저 연결"** 버튼 클릭 → 자동으로 자막 추출 시작

### 프로그래밍 방식

```python
from app import UdemyScraperApp

def log_callback(message):
    print(message)

def progress_callback(current, total):
    print(f"진행률: {current}/{total}")

def status_callback(status):
    print(f"상태: {status}")

# 스크래퍼 초기화
app = UdemyScraperApp(
    progress_callback=progress_callback,
    status_callback=status_callback,
    log_callback=log_callback
)

# 워크플로우 실행
success = app.run_workflow(course_name="Spring Boot 3")

if success:
    print("✅ 스크래핑 완료!")
else:
    print("❌ 스크래핑 실패")
```

## ⚙️ 작동 방식

### 전체 워크플로우

```
1. 브라우저 초기화
   ↓
2. Udemy 로그인 (수동 or 자동)
   ↓
3. My Learning 페이지 이동
   ↓
4. 강의 검색 및 선택
   ↓
5. 커리큘럼 구조 분석
   ↓
6. 섹션별 처리
   ├─ 섹션 아코디언 열기
   ├─ 강의 목록 파싱
   └─ 각 강의별 처리
      ├─ 강의 클릭
      ├─ 비디오 로딩 대기
      ├─ 트랜스크립트 패널 열기
      ├─ 자막 내용 추출
      ├─ 파일 저장 (.txt)
      └─ 섹션 목록으로 복귀
   ↓
7. 섹션별 통합 파일 생성
   ├─ 섹션 내 모든 .txt 파일 수집
   ├─ 마크다운 형식으로 병합
   ├─ Section_XX_제목_total.md 생성
   └─ 원본 섹션 폴더 삭제
   ↓
8. 완료
```

### 핵심 알고리즘

#### 1. 트랜스크립트 추출 (transcript_scraper.py:35-75)

```python
def start_complete_scraping_workflow(course: Course) -> bool:
    # 초기 상태 확인 (normal body)
    ensure_normal_body_state()

    # 모든 섹션 순회
    for section in course.sections:
        # 섹션 아코디언 열기
        open_section_accordion(section_idx)

        # 섹션 내 비디오 처리
        process_section_videos(section)

        # 섹션별 통합 파일 생성
        create_section_merged_file(section_idx)
```

#### 2. 강의 타입 감지 (transcript_scraper.py:446-491)

```python
def _get_lecture_type_from_element(lecture_element) -> str:
    # SVG 아이콘 기반 강의 타입 감지
    # - video: 비디오 강의 (자막 추출)
    # - document: 문서/아티클 (스킵)
    # - quiz: 퀴즈 (스킵)
    # - resource: 다운로드 리소스 (스킵)
```

#### 3. 섹션 병합 (section_merger.py:18-39)

```python
def merge_all_sections() -> bool:
    # 모든 Section_XX_제목 폴더 찾기
    section_dirs = find_section_directories()

    for section_dir in section_dirs:
        # 섹션 내 모든 .txt 파일 수집
        txt_files = section_dir.glob("*.txt")

        # 마크다운 형식으로 병합
        markdown_content = create_section_markdown(txt_files)

        # 통합 파일 저장
        save(f"Section_XX_제목_total.md", markdown_content)

        # 원본 폴더 삭제
        shutil.rmtree(section_dir)
```

## 🧩 주요 컴포넌트 설명

### 1. app.py - UdemyScraperApp

메인 워크플로우를 조율하는 컨트롤러 클래스

**주요 메서드:**
- `run_workflow(course_name)`: 전체 스크래핑 워크플로우 실행
- `_initialize_components()`: 브라우저 및 컴포넌트 초기화
- `_select_course(course_name)`: 강의 검색 및 선택
- `_analyze_course_structure(course)`: 커리큘럼 구조 분석
- `_extract_all_subtitles(course)`: 모든 자막 추출

**콜백 시스템:**
```python
progress_callback(current, total)  # 진행률 업데이트
status_callback(message)           # 상태 메시지
log_callback(message)              # 로그 메시지
```

### 2. browser/transcript_scraper.py - TranscriptScraper

자막 추출의 핵심 로직을 담당

**주요 기능:**
- 섹션별 강의 순회
- DOM 상태 관리 (normal body ↔ script body)
- 강의 타입 감지 (비디오/문서/퀴즈)
- 트랜스크립트 추출 및 저장
- 섹션별 통합 파일 자동 생성

**핵심 메서드:**
- `start_complete_scraping_workflow()`: 전체 워크플로우 시작 (line 35)
- `_process_section()`: 개별 섹션 처리 (line 126)
- `_process_single_lecture()`: 개별 강의 처리 (line 209)
- `_get_lecture_type_from_element()`: 강의 타입 감지 (line 446)

### 3. browser/auth.py - UdemyAuth

브라우저 초기화 및 인증 관리

**주요 기능:**
- Chrome WebDriver 설정
- 디버그 모드 브라우저 실행 (`launch_debug_browser()`)
- 기존 브라우저 연결 (`connect_to_existing_browser()`)
- 세션 관리

### 4. browser/element_finder.py

DOM 요소 검색 및 클릭 처리

**클래스:**
- `ElementFinder`: 트랜스크립트 버튼, 비디오 영역 등 검색
- `ClickHandler`: 안전한 클릭 처리 (JavaScript 폴백 포함)
- `SectionNavigator`: 섹션 아코디언 제어

### 5. browser/transcript_extractor.py

트랜스크립트 추출 세부 로직

**주요 기능:**
- 트랜스크립트 패널 열기/닫기
- 자막 콘텐츠 로딩 대기
- 타임스탬프 및 텍스트 추출

### 6. section_merger.py - SectionMerger

섹션별 자막 파일 병합

**주요 메서드:**
- `merge_all_sections()`: 모든 섹션 병합 (line 18)
- `_merge_section(section_dir)`: 개별 섹션 병합 (line 56)
- `_create_section_markdown()`: 마크다운 생성 (line 106)

### 7. config/settings.py - Config

전역 설정 관리

**주요 설정:**
```python
UDEMY_BASE_URL = "https://www.udemy.com"
WAIT_TIMEOUT = 10  # 요소 대기 시간
MAX_RETRIES = 3    # 최대 재시도 횟수
HEADLESS_MODE = False  # 항상 False (2FA 필요)
```

### 8. core/models.py

데이터 모델 정의

**데이터 클래스:**
- `Subtitle`: 자막 데이터 (타임스탬프, 텍스트)
- `Lecture`: 강의 정보 (제목, 시간, 자막)
- `Section`: 섹션 정보 (제목, 강의 목록)
- `Course`: 강의 전체 정보 (섹션, 메타데이터)
- `ScrapingProgress`: 진행 상황 추적

### 9. gui/simple_ui.py - SimpleUdemyGUI

PySide6 기반 GUI

**주요 기능:**
- 디버그 브라우저 실행
- 브라우저 연결 및 스크래핑 시작
- 실시간 로그 및 진행률 표시

## 📂 출력 결과

### 디렉토리 구조

```
output/
└── 강의명/
    ├── Section_01_섹션제목1_total.md
    ├── Section_02_섹션제목2_total.md
    └── Section_03_섹션제목3_total.md
```

### 통합 파일 형식 (Section_XX_제목_total.md)

```markdown
# Section 1 통합 대본

**강의명**: Spring Boot 3 마스터하기
**섹션**: Section 1
**총 강의 수**: 10개
**생성일**: 2025-09-30 12:34:56

---

## 1. 강의 제목 1

[강의 자막 내용...]

---

## 2. 강의 제목 2

[강의 자막 내용...]

---
```

## 🔧 문제 해결

### 1. 브라우저가 열리지 않음

**원인**: ChromeDriver 버전 불일치

**해결**:
```bash
pip install --upgrade webdriver-manager
```

### 2. 트랜스크립트 버튼을 찾을 수 없음

**원인**: Udemy UI 변경

**해결**: `browser/selectors.py`에서 CSS 셀렉터 업데이트 필요
```python
# browser/selectors.py
TRANSCRIPT_BUTTON = [
    "button[data-purpose='transcript-toggle']",
    # 새로운 셀렉터 추가
]
```

### 3. Stale Element Reference 오류

**원인**: DOM 업데이트로 인한 요소 참조 손실

**해결**: 이미 구현된 fresh element 재검색 로직 활용
- `transcript_scraper.py:174-187` 참고

### 4. 강의 타입 감지 실패

**원인**: SVG 아이콘 구조 변경

**해결**: `_get_lecture_type_from_element()` 메서드 업데이트
- `transcript_scraper.py:446-491` 참고

## 🛠 개발 가이드

### 새로운 기능 추가하기

#### 1. 새로운 파일 포맷 추가 (예: JSON)

```python
# utils/file_utils.py에 추가
class JsonGenerator:
    def create_section_file(self, section, output_dir, section_idx):
        data = {
            "section": section.title,
            "lectures": [
                {"title": lecture.title, "subtitles": lecture.subtitles}
                for lecture in section.lectures
            ]
        }

        with open(output_dir / f"section_{section_idx}.json", 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

#### 2. 새로운 셀렉터 추가

```python
# browser/selectors.py에 추가
class UdemySelectors:
    # 기존 셀렉터...

    NEW_ELEMENT = [
        "selector1",
        "selector2",  # 폴백
    ]
```

#### 3. 진행률 콜백 활용

```python
from app import UdemyScraperApp

def custom_progress(current, total):
    percentage = (current / total) * 100
    print(f"진행: {percentage:.1f}%")
    # 데이터베이스 업데이트, 웹훅 호출 등

app = UdemyScraperApp(progress_callback=custom_progress)
```

### 디버깅 팁

#### 1. 브라우저 상태 확인

```python
# 현재 URL 확인
print(driver.current_url)

# 페이지 소스 저장
with open('debug_page.html', 'w') as f:
    f.write(driver.page_source)
```

#### 2. 로그 레벨 조정

```python
# config/settings.py
DEBUG_MODE = True  # 상세 로그 활성화
```

#### 3. 스크린샷 캡처

```python
# 디버깅 시 스크린샷 저장
driver.save_screenshot('debug_screenshot.png')
```

### 테스트 가이드

```python
# test_scraper.py (예시)
import pytest
from app import UdemyScraperApp

def test_course_selection():
    app = UdemyScraperApp()
    course = app._select_course("Spring Boot")
    assert course is not None
    assert "Spring" in course.title

def test_section_merge():
    from section_merger import SectionMerger
    merger = SectionMerger("output/test_course")
    success = merger.merge_all_sections()
    assert success == True
```

### 코드 스타일

- PEP 8 준수
- Docstring 필수 (Google 스타일)
- Type Hints 권장

```python
def process_lecture(lecture: Lecture, section_idx: int) -> bool:
    """
    강의를 처리하고 자막을 추출합니다.

    Args:
        lecture: 처리할 강의 객체
        section_idx: 섹션 인덱스

    Returns:
        bool: 성공 여부
    """
    pass
```

## 📝 라이선스

이 프로젝트는 개인 학습 및 연구 목적으로 제작되었습니다.

## 🤝 기여 가이드

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 연락처

문제가 발생하거나 질문이 있으시면 Issue를 생성해주세요.

---

**마지막 업데이트**: 2025-09-30