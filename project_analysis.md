# Udemy 강의 대본 스크래퍼 프로젝트 분석 및 계획서

## 📋 프로젝트 개요

**Udemy 강의 대본 스크래퍼**는 Udemy 플랫폼의 동영상 강의에서 자막/대본을 자동 추출하여 Markdown 형식으로 저장하는 데스크톱 애플리케이션입니다. 기존 인프런 스크래퍼의 성공적인 워크플로우를 Udemy에 적용하는 프로젝트입니다.

### 🎯 핵심 기능

1. **사용자 인증**: Udemy 계정 로그인 (2FA 지원)
2. **강의 탐색**: "My learning" 페이지에서 강의 검색/선택
3. **구조 분석**: 섹션→강의 계층 구조 파싱
4. **자막 추출**: 타임스탬프와 함께 자막 데이터 스크래핑
5. **파일 저장**: 섹션별 Markdown 파일로 체계적 저장

### 📊 기대 효과

- 강의 내용 복습 및 검색 용이성 향상
- 오프라인 학습 자료 확보
- 강의 내용 정리 및 노트 작성 시간 단축

## 🏗️ 프로젝트 아키텍처

### 모듈 구조 설계

```
udemy_scraper/
├── ui.py              # tkinter GUI 인터페이스
├── app.py             # 메인 워크플로우 컨트롤러
├── auth.py            # Udemy 로그인/인증 처리
├── navigation.py      # 페이지 탐색 및 강의 선택
├── scraper.py         # 자막 추출 핵심 로직
├── config.py          # 설정 및 환경변수 관리
├── file_utils.py      # 파일 저장 및 Markdown 생성
├── requirements.txt   # 의존성 패키지 목록
├── .env.sample        # 환경변수 템플릿
└── README.md          # 설치/사용 가이드
```

### 데이터 플로우

```
GUI 입력 → 인증 → 강의 선택 → 구조 분석 → 자막 추출 → 파일 저장
   ↓        ↓        ↓          ↓          ↓          ↓
ui.py → auth.py → navigation.py → scraper.py → file_utils.py
```

### 출력 파일 구조

```
output_udemy_scripts/
└── [강의명]/
    ├── 섹션_1_[섹션제목]_total.md
    ├── 섹션_2_[섹션제목]_total.md
    └── ...
```

### Markdown 파일 형식

```markdown
# 섹션 1: 섹션 제목

## 강의 1 - 강의 제목

**00:00:15**  
안녕하세요, 이번 강의에서는...

**00:00:32**  
첫 번째로 다룰 내용은...

## 강의 2 - 두 번째 강의 제목

**00:00:05**  
이전 강의에 이어서...
```

## 🛠️ 기술 스택

### 핵심 기술

- **언어**: Python 3.8+
- **GUI 프레임워크**: tkinter (Python 내장)
- **웹 자동화**: Selenium WebDriver
- **HTML 파싱**: BeautifulSoup4
- **브라우저 드라이버**: webdriver-manager (Chrome/Edge)

### 주요 라이브러리

```python
# requirements.txt
selenium>=4.15.0
webdriver-manager>=4.0.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
requests>=2.31.0
lxml>=4.9.0
```

### 플랫폼 지원

- **Primary**: macOS (현재 환경)
- **Cross-platform**: Windows 10/11, Linux Ubuntu 20.04+
- **브라우저**: Chrome (headless 모드 지원)

## 📅 단계별 개발 계획

### Phase 1: 기본 인프라 구축 (1-2일)

```python
✓ 프로젝트 구조 생성
✓ requirements.txt 및 의존성 설정
✓ config.py - 환경설정 및 상수 정의
✓ 기본 GUI 레이아웃 (ui.py)
```

### Phase 2: 인증 및 탐색 로직 (2-3일)

```python
✓ auth.py - Udemy 로그인 자동화
✓ navigation.py - "My learning" 페이지 탐색
✓ 강의 검색 및 선택 기능
✓ 세션 관리 및 에러 처리
```

### Phase 3: 자막 추출 핵심 로직 (3-4일)

```python
✓ scraper.py - 강의 구조 분석
✓ 자막 패널 접근 및 데이터 추출
✓ 타임스탬프 파싱 및 매핑
✓ 다국어 자막 지원
```

### Phase 4: 파일 처리 및 완성 (1-2일)

```python
✓ file_utils.py - Markdown 파일 생성
✓ 섹션별 파일 저장 로직
✓ 진행상황 모니터링 UI 연동
✓ 에러 처리 및 복구 메커니즘
```

### Phase 5: 테스트 및 최적화 (1-2일)

```python
✓ 전체 워크플로우 통합 테스트
✓ 다양한 강의 타입 테스트
✓ 성능 최적화 및 안정성 개선
✓ 사용자 가이드 작성
```

## 🎯 핵심 구현 전략

### 1. 자막 추출 전략

```python
# Udemy 자막 접근 방법 (인프런과 차이점)
1. 동영상 플레이어 → CC(자막) 버튼 클릭
2. 자막 패널 활성화 후 전체 로딩
3. VTT/WebVTT 형식 또는 JSON API 데이터 추출
4. 타임스탬프 → "HH:MM:SS" 형식 변환
```

### 2. 안정성 확보 방안

```python
# 브라우저 자동화 탐지 우회
- User-Agent 로테이션
- 랜덤 대기시간 (1-3초)
- 마우스 움직임 시뮬레이션
- 헤드리스 모드 옵션 제공

# 복구 메커니즘
- 섹션별 체크포인트 저장
- 실패 시 마지막 성공 지점부터 재시작
- 네트워크 오류 시 자동 재시도 (최대 3회)
```

### 3. 성능 최적화

```python
# 메모리 관리
- 섹션 완료 시 브라우저 탭 정리
- 대용량 강의 대응 배치 처리
- 자막 데이터 스트리밍 저장

# 병렬 처리 고려사항
- 단일 브라우저 인스턴스 사용 (Udemy 세션 유지)
- 자막 추출과 파일 저장 비동기 처리
```

### 4. 데이터 구조 설계

```python
# 강의 데이터 모델
class Course:
    title: str
    sections: List[Section]

class Section:
    title: str
    lectures: List[Lecture]

class Lecture:
    title: str
    duration: str
    subtitles: List[Subtitle]

class Subtitle:
    timestamp: str  # "00:05:30"
    text: str
```

## ⚠️ 주요 도전과제 및 해결방안

### 1. Udemy vs 인프런 차이점

| 구분 | 인프런 | Udemy | 해결방안 |
|------|--------|--------|----------|
| **자막 형식** | HTML data-index | VTT/JSON API | 다중 파서 구현 |
| **DRM 보호** | 없음 | 일부 적용 | DRM 감지 및 스킵 |
| **2FA** | 없음 | 지원 필요 | 수동 입력 대기 |
| **다국어** | 한국어 | 한/영/기타 | 언어 선택 UI |

### 2. 기술적 리스크

- **자동화 탐지**: User-Agent, 대기시간 랜덤화
- **동적 로딩**: Explicit Wait 활용
- **세션 만료**: 자동 재로그인 로직
- **Rate Limiting**: 적절한 딜레이 구현

## 🔒 보안 및 정책 준수

### 기본 보안

- `.env` 파일로 인증 정보 관리
- 로그에 비밀번호 출력 금지
- 적절한 요청 간격 유지 (rate limiting)

### 사용 제한

- **개인 학습 목적으로만 사용**
- 저작권 보호 콘텐츠 재배포 금지
- Udemy 이용약관 준수 필수

## 📦 설치 및 실행 가이드

```bash
# 1. 프로젝트 클론
git clone [repository_url]
cd udemy_script_scraper

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 설정 (선택사항)
cp .env.sample .env
# .env 파일에 기본 이메일/비밀번호 설정

# 4. 실행
python ui.py
```

## 🎨 GUI 인터페이스 설계

### tkinter 기반 데스크톱 앱

```
┌─────────────────────────────────────┐
│        Udemy 강의 대본 스크래퍼        │
├─────────────────────────────────────┤
│                                     │
│ 이메일:     [____________________]  │
│ 비밀번호:   [____________________]  │
│ 강의명:     [____________________]  │
│                                     │
│        [스크립트 추출 시작]          │
│                                     │
│ 상태: 준비 완료                      │
└─────────────────────────────────────┘
```

### GUI 특징

- **심플한 3필드 UI**: 이메일, 비밀번호, 강의명만 입력
- **자동 설정**: 저장 경로 자동 생성 (`output_udemy_scripts/`)
- **기본값 로딩**: `.env` 파일에서 이메일/비밀번호 자동 로드
- **상태 표시**: 하단에 간단한 진행 상태 메시지
- **키보드 지원**: Enter 키로 시작, Ctrl+V 붙여넣기

## 🚀 다음 단계

이제 실제 구현을 시작할 준비가 완료되었습니다. 다음과 같은 순서로 진행하면 됩니다:

1. **프로젝트 구조 생성** - 디렉토리 및 기본 파일들
2. **의존성 설정** - requirements.txt 및 환경 설정
3. **GUI 프로토타입** - 기본 tkinter 인터페이스
4. **Udemy 로그인 테스트** - 실제 사이트 연동 확인

---

**문서 작성일**: 2025년 9월 17일  
**프로젝트 상태**: 분석 완료, 구현 대기  
**예상 개발 기간**: 7-10일


