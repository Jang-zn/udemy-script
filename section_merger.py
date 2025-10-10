"""
섹션별 대본 파일들을 하나의 마크다운 파일로 합치는 모듈
"""

import os
from pathlib import Path
from typing import List, Dict
import re


class SectionMerger:
    """섹션별 대본 파일들을 합치는 클래스"""

    def __init__(self, course_dir: str):
        self.course_dir = Path(course_dir)
        self.course_name = self.course_dir.name

    def merge_all_sections(self) -> bool:
        """모든 섹션을 개별 마크다운 파일로 합치기"""
        try:
            print(f"🚀 섹션별 대본 합치기 시작: {self.course_name}")

            # 섹션 디렉토리들 찾기
            section_dirs = self._find_section_directories()
            if not section_dirs:
                print("❌ 섹션 디렉토리를 찾을 수 없습니다.")
                return False

            print(f"📁 발견된 섹션: {len(section_dirs)}개")

            success_count = 0
            for section_dir in section_dirs:
                if self._merge_section(section_dir):
                    success_count += 1

            # 전체 통합 파일은 생성하지 않음 (사용자 요청)

            print(f"✅ 섹션 합치기 완료: {success_count}/{len(section_dirs)}개 성공")
            return success_count > 0

        except Exception as e:
            print(f"❌ 섹션 합치기 실패: {str(e)}")
            return False

    def _find_section_directories(self) -> List[Path]:
        """섹션 디렉토리들 찾기"""
        section_dirs = []
        for item in self.course_dir.iterdir():
            if item.is_dir() and item.name.startswith("Section_"):
                section_dirs.append(item)

        # 섹션 번호 순으로 정렬
        section_dirs.sort(key=lambda x: int(x.name.split("_")[1]))
        return section_dirs

    def _merge_section(self, section_dir: Path) -> bool:
        """개별 섹션의 모든 강의를 하나의 마크다운 파일로 합치기"""
        try:
            section_name = section_dir.name
            section_num = section_name.split("_")[1]

            print(f"  📝 {section_name} 처리 중...")

            # 섹션 내 텍스트 파일들 찾기
            txt_files = list(section_dir.glob("*.txt"))
            if not txt_files:
                print(f"    ⚠️ {section_name}에 텍스트 파일이 없습니다.")
                return False

            # 파일명 기준으로 정렬 (강의 순서대로)
            txt_files.sort(key=lambda x: self._extract_lecture_number(x.name))

            # 마크다운 내용 생성
            markdown_content = self._create_section_markdown(section_num, txt_files)

            # 마크다운 파일 저장 (섹션폴더명_total.md 형식)
            section_folder_name = section_dir.name
            output_file = self.course_dir / f"{section_folder_name}_total.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"    ✅ {output_file.name} 생성 완료 ({len(txt_files)}개 강의)")

            return True

        except Exception as e:
            print(f"    ❌ {section_dir.name} 처리 실패: {str(e)}")
            return False

    def _extract_lecture_number(self, filename: str) -> int:
        """파일명에서 강의 번호 추출"""
        try:
            # "01_강의제목.txt" 형식에서 01 추출
            match = re.match(r'^(\d+)_', filename)
            if match:
                return int(match.group(1))
            return 999  # 번호가 없으면 맨 뒤로
        except:
            return 999

    def _create_section_markdown(self, section_num: str, txt_files: List[Path]) -> str:
        """섹션의 마크다운 내용 생성"""
        content = []

        # 섹션 헤더
        content.append(f"# Section {section_num} 통합 대본\n")
        content.append(f"**강의명**: {self.course_name}\n")
        content.append(f"**섹션**: Section {section_num}\n")
        content.append(f"**총 강의 수**: {len(txt_files)}개\n")
        content.append(f"**생성일**: {self._get_current_datetime()}\n\n")
        content.append("---\n\n")

        # 각 강의별 내용
        for i, txt_file in enumerate(txt_files, 1):
            try:
                # 강의 제목 추출
                lecture_title = self._extract_lecture_title(txt_file.name)

                content.append(f"## {i}. {lecture_title}\n\n")

                # 강의 내용 읽기
                with open(txt_file, 'r', encoding='utf-8') as f:
                    lecture_content = f.read().strip()

                # 내용에서 제목 라인 제거 (첫 두 줄)
                lines = lecture_content.split('\n')
                if len(lines) > 2 and lines[1].startswith('='):
                    lecture_content = '\n'.join(lines[2:]).strip()

                if lecture_content:
                    content.append(f"{lecture_content}\n\n")
                else:
                    content.append("*이 강의에는 대본이 없습니다.*\n\n")

                content.append("---\n\n")

            except Exception as e:
                content.append(f"*강의 {i} 내용 읽기 실패: {str(e)}*\n\n")
                content.append("---\n\n")

        return ''.join(content)

    def _extract_lecture_title(self, filename: str) -> str:
        """파일명에서 강의 제목 추출"""
        try:
            # "01_강의제목.txt"에서 "강의제목" 부분 추출
            title = filename.replace('.txt', '')
            if '_' in title:
                title = title.split('_', 1)[1]  # 첫 번째 _를 기준으로 나누고 뒷부분 사용

            # 파일명이 너무 길면 줄임
            if len(title) > 100:
                title = title[:97] + "..."

            return title
        except:
            return filename.replace('.txt', '')

    def _get_current_datetime(self) -> str:
        """현재 날짜시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _create_complete_course_file(self):
        """전체 강의 통합 파일 생성"""
        try:
            print("📚 전체 강의 통합 파일 생성 중...")

            # 섹션별 마크다운 파일들 찾기 (새로운 패턴: Section_XX_제목_total.md)
            md_files = list(self.course_dir.glob("Section_*_total.md"))
            if not md_files:
                print("⚠️ 섹션별 마크다운 파일이 없습니다.")
                return

            # 섹션 번호순으로 정렬
            md_files.sort(key=lambda x: int(x.name.split('_')[1]))

            content = []

            # 전체 파일 헤더
            content.append(f"# {self.course_name} - 전체 대본\n\n")
            content.append(f"**총 섹션 수**: {len(md_files)}개\n")
            content.append(f"**생성일**: {self._get_current_datetime()}\n\n")
            content.append("---\n\n")

            # 목차 생성
            content.append("## 📋 목차\n\n")
            for md_file in md_files:
                section_num = md_file.name.split('_')[1]
                content.append(f"- [Section {section_num}](#section-{section_num}-통합-대본)\n")
            content.append("\n---\n\n")

            # 각 섹션 내용 추가
            for md_file in md_files:
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        section_content = f.read()
                    content.append(section_content)
                    content.append("\n")
                except Exception as e:
                    content.append(f"*{md_file.name} 읽기 실패: {str(e)}*\n\n")

            # 전체 파일 저장
            output_file = self.course_dir / "00_전체강의_통합대본.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(''.join(content))

            print(f"✅ {output_file.name} 생성 완료")

        except Exception as e:
            print(f"❌ 전체 강의 통합 파일 생성 실패: {str(e)}")


def main():
    """메인 실행 함수"""
    course_dir = "output/【한글자막】 Spring Boot 3 & Spring Framework 6 마스터하기..."

    if not os.path.exists(course_dir):
        print(f"❌ 강의 디렉토리를 찾을 수 없습니다: {course_dir}")
        return

    merger = SectionMerger(course_dir)
    merger.merge_all_sections()


if __name__ == "__main__":
    main()