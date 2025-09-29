"""
파일 처리 유틸리티 - 트랜스크립트 저장 및 관리
"""

import os
import re
from pathlib import Path
from typing import List, Dict
from core.models import Section, Lecture, Subtitle

class TranscriptFileManager:
    """트랜스크립트 파일 관리 클래스"""

    def __init__(self, output_dir: str = "transcripts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def save_lecture_transcript(self, section: Section, lecture: Lecture) -> bool:
        """개별 강의 트랜스크립트를 마크다운 파일로 저장"""
        try:
            if not lecture.subtitles:
                return False

            # 파일명 생성: 섹션명_영상명.md
            filename = self._create_lecture_filename(section, lecture)
            filepath = self.output_dir / filename

            # 마크다운 내용 생성
            content = self._create_lecture_markdown_content(section, lecture)

            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ 강의 트랜스크립트 저장: {filename}")
            return True

        except Exception as e:
            print(f"❌ 강의 트랜스크립트 저장 실패: {str(e)}")
            return False

    def combine_section_transcripts(self, section: Section, lectures: List[Lecture]) -> bool:
        """섹션 내 모든 강의 트랜스크립트를 하나의 파일로 결합"""
        try:
            # 파일명 생성: 섹션명_total.md
            filename = self._create_section_filename(section)
            filepath = self.output_dir / filename

            # 마크다운 내용 생성
            content = self._create_section_markdown_content(section, lectures)

            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ 섹션 통합 트랜스크립트 저장: {filename}")

            # 개별 강의 파일들 삭제
            self._cleanup_individual_lecture_files(section, lectures)

            return True

        except Exception as e:
            print(f"❌ 섹션 트랜스크립트 결합 실패: {str(e)}")
            return False

    def _create_lecture_filename(self, section: Section, lecture: Lecture) -> str:
        """강의별 파일명 생성"""
        # 파일명에 사용할 수 없는 문자 제거
        section_name = self._sanitize_filename(section.title)
        lecture_name = self._sanitize_filename(lecture.title)

        return f"{section_name}_{lecture_name}.md"

    def _create_section_filename(self, section: Section) -> str:
        """섹션별 통합 파일명 생성"""
        section_name = self._sanitize_filename(section.title)
        return f"{section_name}_total.md"

    def _sanitize_filename(self, filename: str) -> str:
        """파일명에 사용할 수 없는 문자 제거"""
        # Windows/Linux 파일명 제한 문자 제거
        invalid_chars = r'[<>:"/\\|?*\n\r\t]'
        sanitized = re.sub(invalid_chars, '_', filename)

        # 연속된 언더스코어를 하나로 변경
        sanitized = re.sub(r'_+', '_', sanitized)

        # 앞뒤 공백 및 언더스코어 제거
        sanitized = sanitized.strip(' _')

        # 길이 제한 (200자)
        if len(sanitized) > 200:
            sanitized = sanitized[:200]

        return sanitized or "untitled"

    def _create_lecture_markdown_content(self, section: Section, lecture: Lecture) -> str:
        """강의별 마크다운 내용 생성"""
        content_lines = []

        # 헤더
        content_lines.append(f"# {section.title}")
        content_lines.append(f"## {lecture.title}")
        content_lines.append("")

        # 메타데이터
        content_lines.append("### 정보")
        content_lines.append(f"- **섹션**: {section.title}")
        content_lines.append(f"- **강의**: {lecture.title}")
        if lecture.video_url:
            content_lines.append(f"- **URL**: {lecture.video_url}")
        content_lines.append(f"- **트랜스크립트 항목 수**: {len(lecture.subtitles)}")
        content_lines.append("")

        # 트랜스크립트 내용
        content_lines.append("### 트랜스크립트")
        content_lines.append("")

        if lecture.subtitles:
            for i, subtitle in enumerate(lecture.subtitles, 1):
                # 타임스탬프와 함께 내용 추가
                timestamp = subtitle.timestamp if subtitle.timestamp else "00:00:00"
                content_lines.append(f"**[{timestamp}]** {subtitle.text}")
                content_lines.append("")
        else:
            content_lines.append("*트랜스크립트가 없습니다.*")
            content_lines.append("")

        return "\n".join(content_lines)

    def _create_section_markdown_content(self, section: Section, lectures: List[Lecture]) -> str:
        """섹션별 통합 마크다운 내용 생성"""
        content_lines = []

        # 헤더
        content_lines.append(f"# {section.title} - 통합 트랜스크립트")
        content_lines.append("")

        # 메타데이터
        content_lines.append("## 섹션 정보")
        content_lines.append(f"- **섹션명**: {section.title}")
        content_lines.append(f"- **총 강의 수**: {len(lectures)}")

        # 트랜스크립트가 있는 강의 수 계산
        lectures_with_transcripts = [lec for lec in lectures if lec.subtitles]
        content_lines.append(f"- **트랜스크립트 있는 강의**: {len(lectures_with_transcripts)}")
        content_lines.append("")

        # 강의 목록
        content_lines.append("## 강의 목록")
        for i, lecture in enumerate(lectures, 1):
            status = "✅" if lecture.subtitles else "❌"
            content_lines.append(f"{i}. {status} {lecture.title}")
        content_lines.append("")

        # 각 강의별 트랜스크립트
        for i, lecture in enumerate(lectures, 1):
            content_lines.append(f"## {i}. {lecture.title}")
            content_lines.append("")

            if lecture.subtitles:
                for subtitle in lecture.subtitles:
                    timestamp = subtitle.timestamp if subtitle.timestamp else "00:00:00"
                    content_lines.append(f"**[{timestamp}]** {subtitle.text}")
                    content_lines.append("")
            else:
                content_lines.append("*이 강의는 트랜스크립트가 없습니다.*")
                content_lines.append("")

            content_lines.append("---")  # 구분선
            content_lines.append("")

        return "\n".join(content_lines)

    def _cleanup_individual_lecture_files(self, section: Section, lectures: List[Lecture]):
        """개별 강의 파일들 삭제"""
        try:
            for lecture in lectures:
                filename = self._create_lecture_filename(section, lecture)
                filepath = self.output_dir / filename

                if filepath.exists():
                    filepath.unlink()
                    print(f"🗑️ 개별 파일 삭제: {filename}")

        except Exception as e:
            print(f"⚠️ 개별 파일 삭제 중 오류: {str(e)}")

    def get_output_directory(self) -> Path:
        """출력 디렉토리 경로 반환"""
        return self.output_dir

    def list_saved_files(self) -> List[str]:
        """저장된 파일 목록 반환"""
        try:
            if not self.output_dir.exists():
                return []

            return [f.name for f in self.output_dir.glob("*.md")]

        except Exception:
            return []