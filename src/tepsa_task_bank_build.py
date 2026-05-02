"""
Build data/tessa_psa/task_bank.csv (B4).

- Portal tasks: curated URLs in tepsa_task_bank_portal_data.py (stdlib).
- C-Eval val split: HuggingFace datasets-server JSON API (no huggingface_hub).
- CMMLU dev split: raw CSV from haonan-li/CMMLU on GitHub.

Run: py -3.13 src/tepsa_task_bank_build.py   (or python with network for HTTPS)

Output row count target: >=300 (default 300: 70+70 portal PS/ES + 30+20+20 + 45+45 benchmarks).
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
OUT = ROOT / "data" / "tessa_psa" / "task_bank.csv"

from tepsa_task_bank_portal_data import (  # noqa: E402
    CODE_STEMS,
    CODE_URLS,
    EDUCATION_STEMS,
    EDUCATION_URLS,
    ENTERPRISE_STEMS,
    ENTERPRISE_URLS,
    MANUFACTURING_STEMS,
    MANUFACTURING_URLS,
    PUBLIC_SERVICE_STEMS,
    PUBLIC_SERVICE_URLS,
)

CEVAL_SUBJECTS = [
    "computer_network",
    "operating_system",
    "college_programming",
    "tax_accountant",
    "law",
    "civil_servant",
    "college_economics",
    "basic_medicine",
    "education_science",
]
CEVAL_ROWS_PER_SUBJECT = 5
CEVAL_SEED = 42

CMMLU_DEV_SUBJECTS = [
    "agronomy",
    "anatomy",
    "arts",
    "astronomy",
    "business_ethics",
    "chinese_civil_service_exam",
    "chinese_driving_rule",
    "chinese_food_culture",
    "chinese_foreign_policy",
]
CMMLU_ROWS_PER_SUBJECT = 5
CMMLU_BASE = "https://raw.githubusercontent.com/haonan-li/CMMLU/master/data/dev/"


def _http_json(url: str, timeout: int = 60) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "tepsa-task-bank-build/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_text(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "tepsa-task-bank-build/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def load_snapshot_benchmarks() -> list[dict[str, str]] | None:
    p = ROOT / "data" / "tessa_psa" / "appendix" / "b4_benchmark_snapshot.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) and len(data) >= 80 else None


def sample_ceval() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rng = random.Random(CEVAL_SEED)
    idx_global = 0
    for subj in CEVAL_SUBJECTS:
        url = (
            "https://datasets-server.huggingface.co/rows?"
            f"dataset=ceval/ceval-exam&config={subj}&split=val&offset=0&length=100"
        )
        try:
            data = _http_json(url)
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            print(f"[warn] C-Eval fetch failed for {subj}: {e}", file=sys.stderr)
            continue
        n = int(data.get("num_rows_total", 0))
        if n <= 0:
            continue
        pick = sorted(rng.sample(range(n), min(CEVAL_ROWS_PER_SUBJECT, n)))
        for off in pick:
            u2 = (
                "https://datasets-server.huggingface.co/rows?"
                f"dataset=ceval/ceval-exam&config={subj}&split=val&offset={off}&length=1"
            )
            try:
                chunk = _http_json(u2)
            except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
                continue
            if not chunk.get("rows"):
                continue
            r0 = chunk["rows"][0]["row"]
            q = r0["question"]
            opts = f"A.{r0['A']} B.{r0['B']} C.{r0['C']} D.{r0['D']}"
            ans = r0.get("answer", "")
            text = f"（C-Eval·{subj}）{q} 选项：{opts}"
            sector = "code" if subj in ("computer_network", "operating_system", "college_programming") else "education"
            diff = "hard" if subj in ("law", "college_programming", "advanced_mathematics") else "medium"
            rows.append(
                {
                    "task_id": f"ceval-{idx_global + 1:03d}",
                    "task_text": text,
                    "task_source": f"HuggingFace ceval/ceval-exam config={subj} split=val row={off}",
                    "sector": sector,
                    "expected_answer_hint": f"官方标准答案选项：{ans}（仅用于锚点评测；引用见 C-Eval 论文与许可证）",
                    "risk_class": "low",
                    "difficulty_label": diff,
                }
            )
            idx_global += 1
    return rows


def sample_cmmlu() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    idx = 0
    for subj in CMMLU_DEV_SUBJECTS:
        url = CMMLU_BASE + subj + ".csv"
        try:
            raw = _http_text(url)
        except urllib.error.URLError as e:
            print(f"[warn] CMMLU fetch failed {subj}: {e}", file=sys.stderr)
            continue
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        reader = csv.reader(lines)
        header = next(reader, None)
        for i, parts in enumerate(reader):
            if i >= CMMLU_ROWS_PER_SUBJECT:
                break
            if len(parts) < 7:
                continue
            _, question, a, b, c, d, ans = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
            text = f"（CMMLU·{subj}）{question} 选项：A.{a} B.{b} C.{c} D.{d}"
            idx += 1
            rows.append(
                {
                    "task_id": f"cmmlu-{idx:03d}",
                    "task_text": text,
                    "task_source": f"GitHub haonan-li/CMMLU data/dev/{subj}.csv (CC BY-NC-SA 4.0)",
                    "sector": "education",
                    "expected_answer_hint": f"标准答案：{ans.strip()}（数据集锚点；请遵守 CMMLU 许可证用于研究）",
                    "risk_class": "low",
                    "difficulty_label": "medium",
                }
            )
    return rows


def _risk_diff_for_portal(sector: str, text: str) -> tuple[str, str]:
    t = text
    high_kw = ("事故", "危险", "爆炸", "动火", "有限空间", "压力容器", "税务", "反垄断", "内幕", "证券", "诉讼")
    if any(k in t for k in high_kw):
        return "high", "hard" if len(t) > 40 else "medium"
    if sector in ("public service", "enterprise support"):
        return "medium", "medium"
    if sector == "manufacturing":
        return "high", "medium"
    return "low", "easy"


def portal_tasks(n_ps: int, n_es: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for i in range(n_ps):
        url = PUBLIC_SERVICE_URLS[i % len(PUBLIC_SERVICE_URLS)]
        stem = PUBLIC_SERVICE_STEMS[i]
        risk, diff = _risk_diff_for_portal("public service", stem)
        out.append(
            {
                "task_id": f"ps-{i + 1:03d}",
                "task_text": stem + " 请结合权威公开信息作答，并提示用户以经办机构或主管部门最新规定为准。",
                "task_source": url,
                "sector": "public service",
                "expected_answer_hint": "以 task_source 栏目及地方政府/经办机构最新办事指南为准；不作个案法律或医疗结论。",
                "risk_class": risk,
                "difficulty_label": diff,
            }
        )
    for i in range(n_es):
        url = ENTERPRISE_URLS[i % len(ENTERPRISE_URLS)]
        stem = ENTERPRISE_STEMS[i]
        risk, diff = _risk_diff_for_portal("enterprise support", stem)
        out.append(
            {
                "task_id": f"es-{i + 1:03d}",
                "task_text": stem + " 请提示企业以税务机关、监管机关及合同文本为准，避免替代专业审计或法律意见。",
                "task_source": url,
                "sector": "enterprise support",
                "expected_answer_hint": "以 task_source 政策发布与当年有效文件为准；涉税涉证事项以主管税务机关解释为准。",
                "risk_class": risk,
                "difficulty_label": diff,
            }
        )
    for i in range(len(MANUFACTURING_STEMS)):
        url = MANUFACTURING_URLS[i % len(MANUFACTURING_URLS)]
        stem = MANUFACTURING_STEMS[i]
        risk, diff = _risk_diff_for_portal("manufacturing", stem)
        out.append(
            {
                "task_id": f"mfg-{i + 1:03d}",
                "task_text": stem,
                "task_source": url,
                "sector": "manufacturing",
                "expected_answer_hint": "以企业安全规程、特种设备法规及现场作业票证为准；本题为排查要点而非设备诊断结论。",
                "risk_class": risk,
                "difficulty_label": diff,
            }
        )
    for i in range(len(EDUCATION_STEMS)):
        url = EDUCATION_URLS[i % len(EDUCATION_URLS)]
        stem = EDUCATION_STEMS[i]
        risk, diff = _risk_diff_for_portal("education", stem)
        out.append(
            {
                "task_id": f"edu-{i + 1:03d}",
                "task_text": stem,
                "task_source": url,
                "sector": "education",
                "expected_answer_hint": "以教育部及省级教育行政部门最新文件、课程标准文本为准。",
                "risk_class": risk,
                "difficulty_label": diff,
            }
        )
    for i in range(len(CODE_STEMS)):
        url = CODE_URLS[i % len(CODE_URLS)]
        stem = CODE_STEMS[i]
        risk, diff = _risk_diff_for_portal("code", stem)
        out.append(
            {
                "task_id": f"code-{i + 1:03d}",
                "task_text": stem,
                "task_source": url,
                "sector": "code",
                "expected_answer_hint": "以 Python 官方文档对应章节为准；版本差异请标明 Python 3.x。",
                "risk_class": risk,
                "difficulty_label": diff,
            }
        )
    return out


def dedupe_task_text(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for r in rows:
        key = re.sub(r"\s+", " ", r["task_text"].strip())[:500]
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def validate(rows: list[dict[str, str]]) -> None:
    ids = [r["task_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate task_id")
    sectors = {}
    for r in rows:
        sectors[r["sector"]] = sectors.get(r["sector"], 0) + 1
    print("sector counts:", sectors)
    http_like = sum(
        1
        for r in rows
        if r["task_source"].startswith("http")
        or r["task_source"].startswith("HuggingFace")
        or r["task_source"].startswith("GitHub")
    )
    print("rows", len(rows), "http/hf/github source", http_like)


def main() -> None:
    n_ps, n_es = 70, 70
    portal = portal_tasks(n_ps, n_es)
    snap = load_snapshot_benchmarks()
    if snap:
        bench = snap
        print("benchmarks: using local b4_benchmark_snapshot.json", len(bench))
    else:
        bench = sample_ceval() + sample_cmmlu()
        print("benchmarks: live fetch", len(bench))
    rows = portal + bench
    rows = dedupe_task_text(rows)
    validate(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task_id",
        "task_text",
        "task_source",
        "sector",
        "expected_answer_hint",
        "risk_class",
        "difficulty_label",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT, "rows", len(rows))


if __name__ == "__main__":
    main()
