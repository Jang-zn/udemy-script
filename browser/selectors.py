"""
Udemy 웹사이트의 CSS 셀렉터 상수들
"""

class UdemySelectors:
    """Udemy 사이트의 CSS 셀렉터들을 관리하는 클래스"""

    # === 트랜스크립트 관련 ===
    TRANSCRIPT_BUTTONS = [
        "button[data-purpose='transcript-toggle']",
        "button[aria-label*='트랜스크립트']",
        "button[aria-label*='Transcript']",
        "button[aria-label*='transcript']",
        "button[aria-label*='대본']",
        "button[aria-label*='자막']",
        "button[aria-label*='Subtitles']",
        ".transcript-toggle"
    ]

    TRANSCRIPT_PANELS = [
        "[data-purpose='transcript-panel']",
        ".transcript--transcript-panel--JLceZ",
        ".transcript-panel",
        ".captions-panel"
    ]

    TRANSCRIPT_CUES = [
        "[data-purpose='transcript-cue']",
        ".transcript-cue",
        ".caption-cue"
    ]

    TRANSCRIPT_CUE_TEXT = [
        "[data-purpose='cue-text']",
        ".cue-text",
        ".caption-text"
    ]

    # === 비디오 플레이어 관련 ===
    VIDEO_AREAS = [
        "video",
        ".video-player",
        "[data-purpose='video-player']",
        ".vjs-tech",
        ".player-container",
        ".lecture-view"
    ]

    # === 강의 아이템 클릭 관련 ===
    LECTURE_CLICKABLE_ELEMENTS = [
        # 기본 링크와 버튼
        "a", "button",
        # 아이템 링크
        ".item-link", ".curriculum-item-link",
        # 커리큘럼 아이템
        "div[data-purpose^='curriculum-item']", "[data-purpose^='curriculum-item']",
        # 컨테이너들
        ".curriculum-item-link--item-container--HFnn0",
        ".curriculum-item--curriculum-item--1rHQL",
        # 제목 요소들
        "span[data-purpose='item-title']", "[data-purpose='item-title']",
        ".curriculum-item-link--curriculum-item-title--VBsdR",
        # 버튼들
        ".ud-btn", "button[aria-label*='재생']", "button[aria-label*='시작']",
        "button[aria-label*='Play']", "button[aria-label*='Start']"
    ]

    # === 섹션 관리 관련 ===
    SECTION_PANELS = [
        "div[data-purpose^='section-panel-']",
        ".curriculum-section"
    ]

    SECTION_BUTTONS = [
        "button[data-purpose^='section-panel-']",
        ".section-title-button",
        ".curriculum-section-title-button"
    ]

    # === 강의 목록 관련 ===
    LECTURE_ITEMS = [
        "[data-purpose^='curriculum-item-lecture-']",
        ".curriculum-item-link",
        ".lecture-item"
    ]

    LECTURE_TITLES = [
        "span[data-purpose='item-title']",
        ".item-title",
        ".lecture-title"
    ]

    # === 탐색 관련 ===
    MY_LEARNING_BUTTONS = [
        "a[href*='/home/my-courses/']",
        "a[data-purpose='header-dropdown-my-learning']",
        ".header-link[href*='learning']",
        "button[aria-label*='내 학습']",
        "button[aria-label*='My learning']"
    ]

    SEARCH_INPUTS = [
        "input[data-purpose='course-search-input']",
        "input[placeholder*='검색']",
        "input[placeholder*='Search']",
        ".search-input"
    ]

    COURSE_CARDS = [
        "[data-purpose='course-card-container']",
        ".course-card",
        ".my-courses-card"
    ]

    COURSE_TITLES = [
        "[data-purpose='course-title']",
        ".course-title",
        "h3", "h4"
    ]

class ClickStrategies:
    """클릭 전략들을 정의하는 클래스"""

    @staticmethod
    def get_scroll_options():
        """스크롤 옵션 반환"""
        return {
            "block": "center",
            "inline": "center",
            "behavior": "smooth"
        }

    @staticmethod
    def get_click_delays():
        """클릭 관련 지연시간 반환"""
        return {
            "after_scroll": 0.3,
            "after_click": 0.3,
            "hover_delay": 0.3,
            "page_load": 1.0
        }