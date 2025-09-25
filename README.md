# Udemy 강의 대본 스크래퍼

Udemy 플랫폼의 동영상 강의에서 자막/대본을 자동으로 추출하여 Markdown 형식으로 저장하는 데스크톱 애플리케이션입니다.

## ✨ 주요 기능

- 🔐 **반자동 로그인**: 2FA 인증 지원 (이메일 인증 수동 처리)
- 🔍 **스마트 강의 검색**: 강의명 부분 매칭으로 쉬운 선택
- 📚 **구조 분석**: 섹션→강의 계층 구조 자동 파싱
- 📝 **자막 추출**: 다양한 자막 형식 지원 (VTT, JSON, DOM)
- 💾 **Markdown 저장**: 섹션별 체계적 파일 생성
- 🎯 **GUI 인터페이스**: 사용하기 쉬운 tkinter 기반 UI

## 🚀 빠른 시작

### 1. 설치

```bash
# 프로젝트 클론
git clone <repository_url>
cd udemy-script

# 의존성 설치
pip install selenium webdriver-manager beautifulsoup4 python-dotenv requests lxml
```

### 2. 실행

```bash
python ui.py
```

### 3. 사용법

1. **이메일/비밀번호 입력**: Udemy 계정 정보 입력
2. **강의명 입력**: 추출할 강의명 입력 (부분 매칭 지원)
3. **스크립트 추출 시작** 클릭
4. **이메일 인증**: 브라우저에서 이메일 인증 코드 입력 (수동)
5. **자동 진행**: 나머지 과정은 자동으로 실행

## 📁 출력 파일 구조

```
output_udemy_scripts/
└── [강의명]/
    ├── 00_강의_요약.md           # 전체 강의 구조 및 통계
    ├── 섹션_01_제목_total.md     # 섹션 1 모든 강의 대본  
    ├── 섹션_02_제목_total.md     # 섹션 2 모든 강의 대본
    ├── ...
    └── README.md                 # 사용 가이드
```

## 📝 Markdown 파일 형식

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

## ⚙️ 설정

### 환경변수 설정 (선택사항)

`env_sample.txt`를 참고하여 `.env` 파일 생성:

```bash
# .env 파일 생성
UDEMY_EMAIL=your_email@example.com
UDEMY_PASSWORD=your_password
OUTPUT_DIR=output_udemy_scripts
HEADLESS_MODE=false
DEBUG_MODE=true
```

### GUI 옵션

- **헤드리스 모드**: 백그라운드에서 브라우저 실행
- **진행률 표시**: 실시간 진행 상황 모니터링
- **로그 창**: 상세한 실행 로그 확인

## 🔧 프로젝트 구조

```
udemy-script/
├── ui.py              # GUI 메인 인터페이스
├── app.py             # 메인 워크플로우 컨트롤러  
├── auth.py            # 반자동 로그인 모듈
├── navigation.py      # 페이지 탐색 및 강의 선택
├── scraper.py         # 자막 추출 핵심 로직
├── file_utils.py      # Markdown 파일 생성
├── config.py          # 설정 관리
├── models.py          # 데이터 모델
└── requirements.txt   # 의존성 패키지
```

## 🔄 작동 원리

1. **브라우저 자동화**: Selenium으로 Chrome 브라우저 제어
2. **로그인 처리**: 이메일/패스워드 자동 입력 + 2FA 수동 처리
3. **강의 탐색**: My Learning 페이지에서 강의 검색/선택
4. **구조 분석**: DOM 파싱으로 섹션/강의 구조 추출
5. **자막 추출**: VTT 트랙, JSON API, DOM 요소 등 다중 방법
6. **파일 저장**: 섹션별 Markdown 파일 생성

## ⚠️ 주의사항

### 기술적 제약

- **DRM 보호 콘텐츠**: 일부 프리미엄 강의는 스크래핑 불가
- **자막 의존성**: 자막이 없는 강의는 추출 불가
- **브라우저 탐지**: 일부 자동화 탐지 시스템 우회 필요

### 사용 제한

- **개인 학습 목적으로만 사용**
- 저작권 보호 콘텐츠 재배포 금지
- Udemy 이용약관 준수 필수

## 🐛 문제 해결

### 로그인 문제

```
❌ 로그인 실패 - 자격 증명을 확인해주세요.
```

**해결법**: 이메일/비밀번호 확인, 2FA 설정 확인

### 강의 찾기 실패

```
❌ '강의명'과 일치하는 강의를 찾을 수 없습니다.
```

**해결법**: 
- 강의명을 더 구체적으로 입력
- 키워드만 입력 (부분 매칭)
- 로그에서 사용 가능한 강의 목록 확인

### 자막 추출 실패

```
⚠️ 자막을 활성화할 수 없습니다.
```

**해결법**:
- 강의에 자막이 있는지 확인
- 브라우저에서 수동으로 자막 활성화 후 재시도
- 다른 언어 자막 시도

### 브라우저 오류

```
❌ 브라우저 설정 실패
```

**해결법**:
- Chrome 브라우저 최신 버전 설치
- ChromeDriver 자동 업데이트 대기
- 헤드리스 모드 비활성화

## 🔧 고급 설정

### 성능 최적화

- `BETWEEN_LECTURES_DELAY`: 강의 간 대기시간 조정
- `WAIT_TIMEOUT`: 요소 대기 시간 조정
- `HEADLESS_MODE`: 백그라운드 실행으로 성능 향상

### 디버깅 모드

```python
DEBUG_MODE=true  # 상세 로그 출력
```

- 페이지 소스 확인
- 네트워크 요청 로그
- 상세 오류 메시지

## 📊 성능 정보

- **추출 속도**: 강의당 약 5-10초
- **메모리 사용량**: 평균 200-500MB
- **지원 파일 크기**: 섹션당 최대 10MB
- **동시 처리**: 단일 브라우저 인스턴스

## 🤝 기여

버그 리포트, 기능 제안, 코드 기여를 환영합니다!

### 개발 환경 설정

```bash
# 개발 모드로 실행
DEBUG_MODE=true python ui.py

# 테스트 실행
python -m pytest tests/

# 코드 포매팅
black *.py
```

## 📄 라이선스

이 프로젝트는 개인 학습 목적으로 제작되었습니다.

## 🔗 관련 링크

- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Udemy Terms of Service](https://www.udemy.com/terms/)
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager)

---

**Version**: 1.0.0  
**Created**: 2025년 9월 17일  
**Language**: Python 3.8+


