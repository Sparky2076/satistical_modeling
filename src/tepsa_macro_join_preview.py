"""
Left-join macro_calibration_totals (year=2024, five tepsa sectors) onto observations.

Run from repo root:
  python src/tepsa_macro_join_preview.py
  python src/tepsa_macro_join_preview.py --obs data/tessa_psa/task_policy_observations_enriched.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "tessa_psa"

FIVE_SECTORS = frozenset(
    {"public_service", "enterprise_support", "manufacturing", "education", "code"}
)
MACRO_PREFIX = "macro_"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        return list(r.fieldnames or []), rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> None:
    ap = argparse.ArgumentParser(description="Join macro_calibration_totals onto observations by tepsa_sector.")
    ap.add_argument(
        "--obs",
        type=Path,
        default=DATA_DIR / "task_policy_observations_with_labels.csv",
        help="Observations CSV (enriched or with_labels).",
    )
    ap.add_argument(
        "--macro",
        type=Path,
        default=DATA_DIR / "macro_calibration_totals.csv",
    )
    ap.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Macro table year filter (default 2024).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DATA_DIR / "obs_macro_preview.csv",
    )
    args = ap.parse_args()

    obs_fields, obs_rows = read_csv(args.obs)
    obs_rows = [r for r in obs_rows if any((v or "").strip() for v in r.values())]
    if not obs_fields:
        raise SystemExit(f"Missing header: {args.obs}")

    _, macro_rows = read_csv(args.macro)
    macro_by_sector: dict[str, dict[str, str]] = {}
    for r in macro_rows:
        sec = (r.get("tepsa_sector") or "").strip()
        if sec not in FIVE_SECTORS:
            continue
        try:
            y = int((r.get("year") or "0").strip())
        except ValueError:
            continue
        if y != args.year:
            continue
        macro_by_sector[sec] = r

    macro_cols_src = [
        "nbs_sector_label",
        "stat_scope",
        "year",
        "avg_annual_wage_cny",
        "employment_10000",
        "enterprise_count_10000",
        "source_url",
        "notes",
    ]
    macro_out_names = [f"{MACRO_PREFIX}{c}" for c in macro_cols_src]

    out_fields = list(obs_fields)
    for c in macro_out_names:
        if c not in out_fields:
            out_fields.append(c)

    merged: list[dict[str, object]] = []
    n_hit = 0
    for r in obs_rows:
        row = dict(r)
        sec = (r.get("tepsa_sector") or "").strip()
        m = macro_by_sector.get(sec)
        if m:
            n_hit += 1
            for src, dst in zip(macro_cols_src, macro_out_names, strict=True):
                row[dst] = (m.get(src) or "").strip()
        else:
            for dst in macro_out_names:
                row[dst] = ""
        merged.append(row)

    write_csv(args.out, out_fields, merged)
    print(f"Wrote {args.out} rows={len(merged)} macro_sector_matches={n_hit} year={args.year}")


if __name__ == "__main__":
    main()
