#!/usr/bin/env python3
"""Tutorial structure, source sections, links, and five-project contract audit."""

from __future__ import annotations

import re
import sys
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

    for page in pages:
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

    print(f"튜토리얼 감사 통과: {len(pages)}개 페이지, 5개 미니 프로젝트")
    return 0


if __name__ == "__main__":
    sys.exit(main())

