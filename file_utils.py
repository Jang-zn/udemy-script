"""
Markdown 파일 생성 및 파일 처리 유틸리티
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from models import Course, Section, Lecture, Subtitle

class MarkdownGenerator:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or print
    
    def create_section_file(self, section: Section, output_dir: Path, section_number: int) -> bool:
        """섹션별 Markdown 파일 생성"""
        try:
            # 출력 디렉토리 생성
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성
            safe_title = self._sanitize_filename(section.title)
            filename = f"섹션_{section_number:02d}_{safe_title}_total.md"
            file_path = output_dir / filename
            
            self.log_callback(f"     📄 생성 중: {filename}")
            
            # Markdown 내용 생성
            content = self._generate_section_markdown(section, section_number)
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_callback(f"     ✅ 파일 저장 완료: {file_path}")
            return True
            
        except Exception as e:
            self.log_callback(f"     ❌ 섹션 파일 생성 실패: {str(e)}")
            return False
    
    def _generate_section_markdown(self, section: Section, section_number: int) -> str:
        """섹션 Markdown 내용 생성"""
        try:
            lines = []
            
            # 섹션 제목
            lines.append(f"# 섹션 {section_number}: {section.title}")
            lines.append("")
            
            # 섹션 정보
            lines.append(f"**생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}")
            lines.append(f"**총 강의 수**: {section.lecture_count}개")
            lines.append("")
            
            # 각 강의별 내용
            for lecture_idx, lecture in enumerate(section.lectures, 1):
                lines.extend(self._generate_lecture_markdown(lecture, lecture_idx))
                lines.append("")  # 강의 간 구분
            
            return "\n".join(lines)
            
        except Exception as e:
            self.log_callback(f"     ❌ 섹션 Markdown 생성 실패: {str(e)}")
            return ""
    
    def _generate_lecture_markdown(self, lecture: Lecture, lecture_number: int) -> List[str]:
        """강의별 Markdown 내용 생성"""
        try:
            lines = []
            
            # 강의 제목
            lines.append(f"## 강의 {lecture_number} - {lecture.title}")
            lines.append("")
            
            # 강의 정보
            if lecture.duration:
                lines.append(f"**재생시간**: {lecture.duration}")
                lines.append("")
            
            # 자막이 있는 경우
            if lecture.has_subtitles and lecture.subtitles:
                lines.extend(self._generate_subtitles_markdown(lecture.subtitles))
            else:
                lines.append("*이 강의에는 자막이 없습니다.*")
            
            return lines
            
        except Exception as e:
            self.log_callback(f"     ❌ 강의 Markdown 생성 실패: {str(e)}")
            return [f"## 강의 {lecture_number} - {lecture.title}", "", "*자막 생성 중 오류가 발생했습니다.*"]
    
    def _generate_subtitles_markdown(self, subtitles: List[Subtitle]) -> List[str]:
        """자막 Markdown 내용 생성"""
        try:
            lines = []
            
            if not subtitles:
                lines.append("*자막 데이터가 없습니다.*")
                return lines
            
            # 자막 정렬 (시간순)
            sorted_subtitles = sorted(subtitles, key=lambda s: s.start_seconds)
            
            for subtitle in sorted_subtitles:
                # 타임스탬프와 텍스트
                lines.append(f"**{subtitle.timestamp}**  ")
                lines.append(subtitle.text)
                lines.append("")  # 자막 항목 간 구분
            
            return lines
            
        except Exception as e:
            self.log_callback(f"     ❌ 자막 Markdown 생성 실패: {str(e)}")
            return ["*자막 처리 중 오류가 발생했습니다.*"]
    
    def create_course_summary(self, course: Course, output_dir: Path) -> bool:
        """강의 전체 요약 파일 생성"""
        try:
            summary_file = output_dir / "00_강의_요약.md"
            
            lines = []
            
            # 강의 전체 정보
            lines.append(f"# {course.title}")
            lines.append("")
            lines.append(f"**생성일**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}")
            lines.append(f"**총 섹션 수**: {course.total_sections}개")
            lines.append(f"**총 강의 수**: {course.total_lectures}개")
            
            if course.instructor:
                lines.append(f"**강사**: {course.instructor}")
            
            if course.description:
                lines.append(f"**설명**: {course.description}")
            
            lines.append("")
            lines.append("---")
            lines.append("")
            
            # 목차
            lines.append("## 📚 목차")
            lines.append("")
            
            for section_idx, section in enumerate(course.sections, 1):
                lines.append(f"### 섹션 {section_idx}: {section.title}")
                lines.append(f"- 강의 수: {section.lecture_count}개")
                
                # 강의 목록
                for lecture_idx, lecture in enumerate(section.lectures, 1):
                    duration_info = f" ({lecture.duration})" if lecture.duration else ""
                    subtitle_info = " 📝" if lecture.has_subtitles else " ❌"
                    lines.append(f"  {lecture_idx}. {lecture.title}{duration_info}{subtitle_info}")
                
                lines.append("")
            
            # 통계 정보
            lines.append("---")
            lines.append("")
            lines.append("## 📊 통계")
            lines.append("")
            
            # 자막 있는 강의 수 계산
            total_with_subtitles = sum(
                1 for section in course.sections 
                for lecture in section.lectures 
                if lecture.has_subtitles
            )
            
            lines.append(f"- **자막 있는 강의**: {total_with_subtitles}/{course.total_lectures}개")
            lines.append(f"- **자막 커버리지**: {(total_with_subtitles/course.total_lectures*100):.1f}%")
            
            # 파일 저장
            content = "\n".join(lines)
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_callback(f"✅ 강의 요약 파일 생성: {summary_file}")
            return True
            
        except Exception as e:
            self.log_callback(f"❌ 강의 요약 파일 생성 실패: {str(e)}")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일명에 사용할 수 없는 문자 제거"""
        try:
            # 파일명에 사용할 수 없는 문자들 제거
            invalid_chars = r'[<>:"/\\|?*]'
            sanitized = re.sub(invalid_chars, '', filename)
            
            # 연속된 공백을 하나로 줄임
            sanitized = re.sub(r'\s+', ' ', sanitized)
            
            # 앞뒤 공백 제거
            sanitized = sanitized.strip()
            
            # 길이 제한 (50자)
            if len(sanitized) > 50:
                sanitized = sanitized[:47] + "..."
            
            # 빈 문자열인 경우 기본값
            if not sanitized:
                sanitized = "제목없음"
            
            return sanitized
            
        except Exception:
            return "제목없음"
    
    def create_readme_file(self, output_dir: Path, course_name: str) -> bool:
        """README 파일 생성"""
        try:
            readme_file = output_dir / "README.md"
            
            lines = []
            lines.append(f"# {course_name} - 강의 대본")
            lines.append("")
            lines.append(f"Udemy 강의 대본 자동 추출 결과")
            lines.append("")
            lines.append(f"**추출일**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}")
            lines.append("")
            
            # 사용법
            lines.append("## 📖 사용법")
            lines.append("")
            lines.append("각 섹션별로 Markdown 파일이 생성되었습니다:")
            lines.append("")
            lines.append("- `섹션_01_제목_total.md` - 섹션 1의 모든 강의 대본")
            lines.append("- `섹션_02_제목_total.md` - 섹션 2의 모든 강의 대본")
            lines.append("- `00_강의_요약.md` - 전체 강의 구조 및 통계")
            lines.append("")
            
            # 형식 설명
            lines.append("## 📝 파일 형식")
            lines.append("")
            lines.append("```markdown")
            lines.append("# 섹션 1: 섹션 제목")
            lines.append("")
            lines.append("## 강의 1 - 강의 제목")
            lines.append("")
            lines.append("**00:00:15**  ")
            lines.append("강의 내용 자막...")
            lines.append("")
            lines.append("**00:00:32**  ")
            lines.append("다음 자막 내용...")
            lines.append("```")
            lines.append("")
            
            # 주의사항
            lines.append("## ⚠️ 주의사항")
            lines.append("")
            lines.append("- 이 자료는 개인 학습 목적으로만 사용해주세요.")
            lines.append("- 저작권 보호 콘텐츠의 재배포는 금지됩니다.")
            lines.append("- Udemy 이용약관을 준수해주세요.")
            lines.append("")
            
            # 생성 도구 정보
            lines.append("---")
            lines.append("")
            lines.append("*Generated by Udemy Script Scraper*")
            
            content = "\n".join(lines)
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_callback(f"✅ README 파일 생성: {readme_file}")
            return True
            
        except Exception as e:
            self.log_callback(f"❌ README 파일 생성 실패: {str(e)}")
            return False
    
    def backup_session_info(self, output_dir: Path, course: Course, progress_info: dict) -> bool:
        """세션 정보 백업 (디버깅/복구용)"""
        try:
            backup_dir = output_dir / ".backup"
            backup_dir.mkdir(exist_ok=True)
            
            session_file = backup_dir / "session_info.json"
            
            import json
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "course_title": course.title,
                "total_sections": course.total_sections,
                "total_lectures": course.total_lectures,
                "progress": progress_info,
                "sections": [
                    {
                        "title": section.title,
                        "lecture_count": section.lecture_count,
                        "lectures": [
                            {
                                "title": lecture.title,
                                "duration": lecture.duration,
                                "has_subtitles": lecture.has_subtitles,
                                "subtitle_count": len(lecture.subtitles) if lecture.subtitles else 0
                            }
                            for lecture in section.lectures
                        ]
                    }
                    for section in course.sections
                ]
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.log_callback(f"✅ 세션 정보 백업: {session_file}")
            return True
            
        except Exception as e:
            self.log_callback(f"❌ 세션 정보 백업 실패: {str(e)}")
            return False
    
    def get_output_file_list(self, output_dir: Path) -> List[str]:
        """생성된 파일 목록 반환"""
        try:
            if not output_dir.exists():
                return []
            
            files = []
            for file_path in sorted(output_dir.glob("*.md")):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    size_kb = file_size / 1024
                    files.append(f"{file_path.name} ({size_kb:.1f}KB)")
            
            return files
            
        except Exception:
            return []
    
    def cleanup_empty_files(self, output_dir: Path) -> int:
        """빈 파일들 정리"""
        try:
            if not output_dir.exists():
                return 0
            
            cleaned_count = 0
            
            for file_path in output_dir.glob("*.md"):
                if file_path.is_file():
                    try:
                        if file_path.stat().st_size < 100:  # 100바이트 미만
                            file_path.unlink()
                            cleaned_count += 1
                            self.log_callback(f"🗑️ 빈 파일 삭제: {file_path.name}")
                    except:
                        continue
            
            return cleaned_count
            
        except Exception:
            return 0


