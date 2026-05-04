"""
Extract plain text from .docx (stdlib zipfile + XML). Run from repo root:

  python docs/paper/tools/extract_docx.py

Writes docs/paper/_source/draft.md and format_outline.md by file size heuristic
(two .docx in repo root: smaller = format template, larger = draft).
"""

from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_to_text(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    blocks: list[str] = []
    for para in root.iter(W_NS + "p"):
        parts: list[str] = []
        for node in para.iter():
            if node.tag == W_NS + "t" and node.text:
                parts.append(node.text)
            if node.tail:
                parts.append(node.tail)
        line = "".join(parts).strip()
        if line:
            blocks.append(line)
    return "\n\n".join(blocks)


def main() -> None:
    repo = Path(__file__).resolve().parents[3]
    docxs = sorted(repo.glob("*.docx"), key=lambda p: p.stat().st_size)
    if len(docxs) < 2:
        raise SystemExit(f"Need two .docx in repo root, found {len(docxs)}: {docxs}")
    fmt, draft = docxs[0], docxs[-1]
    out = repo / "docs" / "paper" / "_source"
    out.mkdir(parents=True, exist_ok=True)
    (out / "format_outline.md").write_text(
        f"<!-- source: {fmt.name} -->\n\n" + docx_to_text(fmt), encoding="utf-8"
    )
    (out / "draft.md").write_text(
        f"<!-- source: {draft.name} -->\n\n" + docx_to_text(draft), encoding="utf-8"
    )
    print(f"Wrote {out / 'format_outline.md'} from {fmt.name}")
    print(f"Wrote {out / 'draft.md'} from {draft.name}")


if __name__ == "__main__":
    main()
