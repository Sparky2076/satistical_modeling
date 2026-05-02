"""
Validate data/tessa_psa/task_bank.csv before batch API runs.

task_source: http(s) URL for web/gov tasks; for task_id prefixes ceval- / cmmlu-,
a non-URL dataset provenance string is allowed.

Run from repo root:
  python src/tepsa_validate_inputs.py
  python src/tepsa_validate_inputs.py --path data/tessa_psa/task_bank.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = REPO_ROOT / "data" / "tessa_psa" / "task_bank.csv"

ALLOWED_SECTORS = frozenset(
    {
        "public service",
        "enterprise support",
        "manufacturing",
        "education",
        "code",
    }
)
ALLOWED_RISK = frozenset({"low", "medium", "high"})
ALLOWED_DIFFICULTY = frozenset({"easy", "medium", "hard"})

# Plan A: join macro_calibration_totals.tepsa_sector (underscore) from task_bank.sector (space)
SECTOR_TO_TEPSA: dict[str, str] = {
    "public service": "public_service",
    "enterprise support": "enterprise_support",
    "manufacturing": "manufacturing",
    "education": "education",
    "code": "code",
}


def is_http_url(s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return False
    try:
        u = urlparse(s)
    except ValueError:
        return False
    return u.scheme in ("http", "https") and bool(u.netloc)


def is_benchmark_provenance_task(task_id: str, src: str) -> bool:
    """C-Eval / CMMLU anchors use non-URL provenance strings (dataset id + split)."""
    tid = (task_id or "").strip().lower()
    s = (src or "").strip()
    if not s or len(s) < 8:
        return False
    if tid.startswith("ceval-") or tid.startswith("cmmlu-"):
        return True
    return False


def acceptable_task_source(task_id: str, src: str) -> bool:
    if is_http_url(src):
        return True
    return is_benchmark_provenance_task(task_id, src)


def validate_rows(rows: list[dict[str, str]]) -> tuple[list[str], int]:
    """Return (messages, fatal_count)."""
    msgs: list[str] = []
    fatal = 0
    seen_ids: dict[str, int] = {}
    for i, row in enumerate(rows, start=2):
        tid = (row.get("task_id") or "").strip()
        if not tid:
            msgs.append(f"line {i}: empty task_id")
            fatal += 1
            continue
        if tid in seen_ids:
            msgs.append(f"line {i}: duplicate task_id {tid!r} (first line {seen_ids[tid]})")
            fatal += 1
        else:
            seen_ids[tid] = i

        text = (row.get("task_text") or "").strip()
        if not text:
            msgs.append(f"line {i} task_id={tid!r}: empty task_text")
            fatal += 1

        src = (row.get("task_source") or "").strip()
        if not acceptable_task_source(tid, src):
            msgs.append(
                f"line {i} task_id={tid!r}: task_source must be http(s) URL "
                f"or (for ceval-/cmmlu- ids) dataset provenance string; got {src!r}"
            )
            fatal += 1

        sec = (row.get("sector") or "").strip()
        if sec not in ALLOWED_SECTORS:
            msgs.append(f"line {i} task_id={tid!r}: invalid sector {sec!r}")
            fatal += 1
        else:
            tepsa = SECTOR_TO_TEPSA.get(sec)
            if not tepsa:
                msgs.append(f"line {i} task_id={tid!r}: missing tepsa_sector mapping for sector {sec!r}")
                fatal += 1

        rc = (row.get("risk_class") or "").strip().lower()
        if rc not in ALLOWED_RISK:
            msgs.append(f"line {i} task_id={tid!r}: invalid risk_class {rc!r}")
            fatal += 1

        dl = (row.get("difficulty_label") or "").strip().lower()
        if dl not in ALLOWED_DIFFICULTY:
            msgs.append(f"line {i} task_id={tid!r}: invalid difficulty_label {dl!r}")
            fatal += 1

    return msgs, fatal


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--path", type=Path, default=DEFAULT_BANK)
    args = p.parse_args()
    path: Path = args.path
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(2)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    print(f"Validated: {path}")
    print(f"  rows: {len(rows)}")
    print(f"  columns: {fieldnames}")

    required = {"task_id", "task_text", "task_source", "sector", "risk_class", "difficulty_label"}
    missing = required - set(fieldnames)
    if missing:
        print(f"ERROR: missing columns: {sorted(missing)}", file=sys.stderr)
        sys.exit(2)

    msgs, fatal = validate_rows(rows)
    for m in msgs[:50]:
        print(f"  {m}")
    if len(msgs) > 50:
        print(f"  ... ({len(msgs) - 50} more issues)")

    # summary counts
    from collections import Counter

    c_sec = Counter((r.get("sector") or "").strip() for r in rows)
    c_risk = Counter((r.get("risk_class") or "").strip().lower() for r in rows)
    c_diff = Counter((r.get("difficulty_label") or "").strip().lower() for r in rows)
    print("  sector counts:", dict(c_sec))
    print("  risk_class counts:", dict(c_risk))
    print("  difficulty_label counts:", dict(c_diff))
    print("  sector -> tepsa_sector (for macro join):", SECTOR_TO_TEPSA)

    if fatal:
        print(f"\nFAILED: {fatal} fatal issue(s).", file=sys.stderr)
        sys.exit(1)
    if msgs:
        print(f"\nWARN: {len(msgs)} non-fatal note(s) above (none if only structural).")
    print("OK: task_bank passed validation.")


if __name__ == "__main__":
    main()
