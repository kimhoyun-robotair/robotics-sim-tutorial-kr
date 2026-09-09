#!/usr/bin/env python3
"""Check tutorial structure, local links and Python syntax without loading Isaac Sim.

This is a static check. It does not validate PhysX, RTX output or ROS 2 transport.
"""

from __future__ import annotations

import ast
import re
import sys
import textwrap
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE_HEADING = re.compile(r"^## 출처\s*$", re.MULTILINE)
LOCAL_LINK = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")


def main() -> int:
    errors: list[str] = []
    pages = sorted(DOCS.rglob("*.md"))
    if not pages:
        errors.append("docs 아래에 Markdown 페이지가 없다.")

    python_blocks = 0
    for page in [ROOT / "README.md", *pages]:
        text = page.read_text(encoding="utf-8")
        if not SOURCE_HEADING.search(text):
            errors.append(f"출처 단락 누락: {page.relative_to(ROOT)}")
        for raw_target in LOCAL_LINK.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or target.startswith("/"):
                continue
            if not (page.parent / target).resolve().exists():
                errors.append(
                    f"깨진 로컬 링크: {page.relative_to(ROOT)} -> {raw_target}"
                )
        # A partial example may omit imports, but must still be valid syntax.
        # Parse only; never execute documentation snippets in the audit process.
        for match in re.finditer(r"^(?P<indent>[ \t]*)```python[^\n]*\n(?P<code>.*?)^(?P=indent)```[ \t]*$", text, re.M | re.S):
            python_blocks += 1
            line = text.count("\n", 0, match.start()) + 1
            try:
                ast.parse(textwrap.dedent(match["code"]), feature_version=(3, 11))
            except SyntaxError as exc:
                errors.append(f"Python 코드 문법: {page.relative_to(ROOT)}:{line}: {exc}")

    course = (DOCS / "course-guide.md").read_text(encoding="utf-8")
    steps = [int(n) for n in re.findall(r"^## (\d+)단계", course, re.M)]
    if len(steps) < 20 or steps != list(range(1, len(steps) + 1)):
        errors.append("학습 과정은 1부터 연속한 20개 이상의 단계가 필요하다.")
    for section in re.split(r"^## \d+단계[^\n]*\n", course, flags=re.M)[1:]:
        if "**완료 기준:**" not in section:
            errors.append("완료 기준이 없는 학습 단계가 있다.")

    code_files = sorted((ROOT / "examples").rglob("*.py")) + sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "tests").glob("*.py"))
    for path in code_files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 11))
        except SyntaxError as exc:
            errors.append(f"Python 파일 문법: {path.relative_to(ROOT)}: {exc}")
    for path in (ROOT / "examples").rglob("*.toml"):
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"TOML 문법: {path.relative_to(ROOT)}: {exc}")

    projects = list((DOCS / "07-projects").glob("*.md"))
    numbered = [p for p in projects if re.match(r"0?[1-5][-_]", p.name)]
    if len(numbered) != 5:
        errors.append(
            "07-projects에는 01~05로 시작하는 미니 프로젝트가 정확히 5개 있어야 한다 "
            f"(현재 {len(numbered)}개)."
        )

    coverage = DOCS / "appendices" / "official-docs-coverage.md"
    if not coverage.exists():
        errors.append("공식 문서 전체 커버리지 표가 없다.")

    if errors:
        print("튜토리얼 감사 실패:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"정적 검사 통과: {len(pages)}개 문서, {len(steps)}단계, 5개 프로젝트, "
          f"Python 코드 블록 {python_blocks}개, Python 파일 {len(code_files)}개")
    print("물리·렌더링·ROS 2 실행 결과는 이 검사에 포함되지 않는다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
