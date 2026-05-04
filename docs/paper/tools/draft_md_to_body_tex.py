"""
Convert docs/paper/_source/draft.md (统模初稿 extract) to sections/body_autogen.tex.

Prose lines: keep Unicode for XeLaTeX; escape only % & # $.
Display-math lines: LaTeX-ify symbols; do not run prose escaping.

After section「六、结果展示与解释框架」, injects \\input{sections/empirical_figures_inline}.
Back matter starting at「参考文献」is written to sections/body_backmatter.tex so main.tex
can insert empirical figures before references.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DRAFT = REPO / "docs" / "paper" / "_source" / "draft.md"
OUT_MAIN = REPO / "docs" / "paper" / "sections" / "body_autogen.tex"
OUT_BACK = REPO / "docs" / "paper" / "sections" / "body_backmatter.tex"

SECTION_SIX = "六、结果展示与解释框架"


def unicode_to_latex_math(s: str) -> str:
    s = re.sub(r"([A-Za-z][A-Za-z0-9]*)̂", r"\\hat{\1}", s)
    return (
        s.replace("≤", r"\leq ")
        .replace("≥", r"\geq ")
        .replace("∈", r"\in ")
        .replace("Σ", r"\sum ")
        .replace("→", r"\rightarrow ")
        .replace("σ", r"\sigma ")
        .replace("Δ", r"\Delta ")
        .replace("∀", r"\forall ")
        .replace("×", r"\times ")
        .replace("γ", r"\gamma ")
        .replace("λ", r"\lambda ")
        .replace("κ", r"\kappa ")
        .replace("α", r"\alpha ")
    )


def escape_text_minimal(s: str) -> str:
    # 不转义 $：正文经 hat/bar 修正后会含行内公式；中文稿中裸 $ 极少
    return s.replace("%", r"\%").replace("&", r"\&").replace("#", r"\#")


def prose_hat_fix(s: str) -> str:
    """Word-style combining circumflex on Latin runs → inline math (nested-safe)."""

    for _ in range(10):
        prev = s
        s = re.sub(
            r"([A-Za-z]+)̂(_\{[^}]*\})",
            lambda m: (
                rf"$\widehat{{{m.group(1)}}}{m.group(2)}$"
                if len(m.group(1)) > 1
                else rf"$\hat{{{m.group(1)}}}{m.group(2)}$"
            ),
            s,
        )
        def repl_paren(m: re.Match[str]) -> str:
            w = m.group(1)
            inner = m.group(2)
            inside = inner[1:-1]
            unwrapped = re.sub(r"\$([^$]*)\$", r"\1", inside)
            cmd = r"\widehat" if len(w) > 1 else r"\hat"
            return f"${cmd}{{{w}}}({unwrapped})$"

        s = re.sub(r"([A-Za-z]+)̂(\([^)]*\))", repl_paren, s)
        s = re.sub(
            r"([A-Za-z]+)̂",
            lambda m: (
                rf"$\widehat{{{m.group(1)}}}$"
                if len(m.group(1)) > 1
                else rf"$\hat{{{m.group(1)}}}$"
            ),
            s,
        )
        if s == prev:
            break
    return s


def prose_bar_fix(s: str) -> str:
    return s.replace("R̄", r"$\bar{R}$").replace("D̄", r"$\bar{D}$")


def chinese_char_count(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def is_display_math(line: str) -> bool:
    if "=" not in line and "≤" not in line and "≥" not in line:
        if not re.search(r"^max_|^s\.t\.", line.strip()):
            return False
    if chinese_char_count(line) > 6:
        return False
    if re.search(r"[A-Za-z]_", line):
        return True
    if any(c in line for c in ("^", "∈", "Σ", "≤", "≥", "∀", "γ", "λ", "κ", "Δ")):
        return True
    if re.search(r"Pr\(|E\[|max_|min_", line):
        return True
    return False


def strip_equation_label(line: str) -> tuple[str, str | None]:
    m = re.search(r"（\s*(\d+)\s*）\s*$", line)
    if m:
        return line[: m.start()].rstrip(), m.group(1)
    m2 = re.search(r"\(\s*(\d+)\s*\)\s*$", line)
    if m2:
        return line[: m2.start()].rstrip(), m2.group(1)
    return line, None


def cleanup_display_math(core: str, eq_num: str | None) -> str:
    """Normalize fragile lines from the Word extract for pdfLaTeX/XeLaTeX."""
    c = core.strip()
    c = c.replace("Ĉ", r"\hat{C}").replace("R̄", r"\bar{R}").replace("D̄", r"\bar{D}")
    if c.startswith("max_x"):
        c = r"\operatorname*{max}_{x}\ " + c.replace("max_x", "", 1).strip()
    if c.startswith("s.t."):
        c = r"\text{s.t.}\ " + c.replace("s.t.", "", 1).strip()
    if eq_num == "6" or ("且" in c and r"\forall" in c and "Disp" in c):
        return (
            r"\begin{aligned}"
            r"\text{Disp}(x) &\leq \bar{D}, \\"
            r"\sum_a x_{s,a} &= 1, \quad \forall s."
            r"\end{aligned}"
        )
    return c


def clean_heading(s: str) -> str:
    return re.sub(r"\d+\s*$", "", s).strip()


def format_reference_item(line: str) -> str:
    body = re.sub(r"^\[\d+\]\s*", "", line.strip())
    return r"\bibitem{ref" + re.match(r"^\[(\d+)\]", line.strip()).group(1) + "}" + "\n" + escape_text_minimal(body)


def process_body_blocks(body: str) -> tuple[list[str], list[str]]:
    """Returns (main_parts, back_parts)."""
    section_pat = re.compile(r"^([一二三四五六七八九十]+、[^\n]+)$")
    subsection_pat = re.compile(r"^（[一二三四五六七八九十]+）[^\n]+$")

    main: list[str] = []
    back: list[str] = []
    target = main
    in_bib = False

    def flush_bib_footer():
        nonlocal in_bib
        if in_bib:
            target.append(r"\end{thebibliography}")
            in_bib = False

    main.append(
        "% Auto-generated from _source/draft.md — edit in Word then re-run extract + this script\n"
        r"\begingroup\small\setlength{\parskip}{0.35em}"
    )
    main.append("")
    back.append(
        "% Back matter from _source/draft.md (references, appendix, acknowledgements)\n"
        r"\begingroup\small\setlength{\parskip}{0.35em}"
    )
    back.append("")

    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            if line == "参考文献":
                flush_bib_footer()
                target = back
                target.append(r"\section{参考文献}")
                target.append(r"\begin{thebibliography}{99}")
                in_bib = True
                i += 1
                continue
            if line == "附录":
                flush_bib_footer()
                target = back
                target.append(r"\section{附录}")
                i += 1
                continue
            if line == "致谢":
                flush_bib_footer()
                target = back
                target.append(r"\section{致谢}")
                i += 1
                continue

            if section_pat.match(line):
                flush_bib_footer()
                h = clean_heading(line)
                target.append(r"\section{" + escape_text_minimal(h) + "}")
                if h == SECTION_SIX:
                    target.append(r"\input{sections/empirical_figures_inline}")
                i += 1
                continue
            if subsection_pat.match(line):
                target.append(r"\subsection*{" + escape_text_minimal(clean_heading(line)) + "}")
                i += 1
                continue
            break

        while i < len(lines):
            line = lines[i]
            i += 1
            if in_bib and re.match(r"^\[\d+\]", line.strip()):
                m = re.match(r"^\[(\d+)\]\s*(.*)$", line.strip(), re.DOTALL)
                if m:
                    num, rest = m.group(1), m.group(2).strip()
                    target.append(r"\bibitem{ref" + num + "}" + escape_text_minimal(rest))
                continue

            if line.startswith("图 ") or line.startswith("表 "):
                target.append(r"\textit{" + escape_text_minimal(line) + r"}\\")
                continue
            if line in ("目录", "摘要", "关键词：", "表格与插图清单"):
                continue
            if re.fullmatch(r"(参考文献|附录|致谢)\d+", line):
                continue
            if line.startswith("从 Token 消耗到公共智能服务配置") and len(line) < 80:
                continue

            if is_display_math(line):
                line_m = unicode_to_latex_math(line)
                core, num = strip_equation_label(line_m)
                core = cleanup_display_math(core, num)
                if num:
                    target.append(r"\begin{equation}\label{eq:" + num + "}")
                    target.append(core)
                    target.append(r"\end{equation}")
                else:
                    target.append(r"\[" + core + r"\]")
            else:
                pl = prose_bar_fix(prose_hat_fix(line))
                target.append(escape_text_minimal(pl) + r"\\")

        target.append("")

    flush_bib_footer()
    main.append(r"\endgroup")
    back.append(r"\endgroup")
    return main, back


def main() -> None:
    raw = DRAFT.read_text(encoding="utf-8")
    anchor = "一、问题背景与研究目标\n\n（一）国家战略背景"
    start = raw.find(anchor)
    if start < 0:
        raise SystemExit("Could not find main body anchor after TOC in draft.md")
    body = raw[start:].strip()

    main_parts, back_parts = process_body_blocks(body)

    OUT_MAIN.parent.mkdir(parents=True, exist_ok=True)
    OUT_MAIN.write_text("\n".join(main_parts), encoding="utf-8")
    OUT_BACK.write_text("\n".join(back_parts), encoding="utf-8")
    print(f"Wrote {OUT_MAIN}")
    print(f"Wrote {OUT_BACK}")


if __name__ == "__main__":
    main()
