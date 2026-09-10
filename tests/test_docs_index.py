import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
README = ROOT / "README.md"

LOCAL_MD_LINK = re.compile(r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)")


def test_local_markdown_links_resolve() -> None:
    broken: list[str] = []
    for path in [README, *sorted(DOCS_ROOT.rglob("*.md"))]:
        for match in LOCAL_MD_LINK.finditer(path.read_text(encoding="utf-8")):
            href = match.group(1).split("#", 1)[0]
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = (path.parent / href).resolve()
            if not target.is_file():
                broken.append(f"{path.relative_to(ROOT)} -> {href}")
    assert not broken, "깨진 로컬 Markdown 링크: " + ", ".join(broken)
