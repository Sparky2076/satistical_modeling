"""
Inter-rater reliability check for human_labels.csv.

Current schema: one row per (task_id, policy_id, run_id). ICC needs either
two columns (rater1, rater2) or multiple rows per key with different annotator_id.

  py -3 src/tepsa_annotation_icc.py
  py -3 src/tepsa_annotation_icc.py --labels data/tessa_psa/human_labels.csv

Writes output/annotation/icc_report.md (status + guidance).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = REPO / "data" / "tessa_psa" / "human_labels.csv"
OUT_DIR = REPO / "output" / "annotation"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    args = ap.parse_args()

    df = pd.read_csv(args.labels, encoding="utf-8")
    keys = ["task_id", "policy_id", "run_id"]
    for k in keys:
        if k not in df.columns:
            raise SystemExit(f"Missing column {k}")

    g = (
        df.groupby(keys, observed=True)
        .agg(n_rows=("annotator_id", "size"), n_annot=("annotator_id", "nunique"))
        .reset_index()
    )
    multi = g[(g["n_rows"] >= 2) | (g["n_annot"] >= 2)]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = OUT_DIR / "icc_report.md"

    lines = [
        "# Annotation inter-rater report",
        "",
        f"- **Input**: `{args.labels.resolve().relative_to(REPO.resolve()) if args.labels.resolve().is_relative_to(REPO.resolve()) else args.labels}`",
        f"- **Rows**: {len(df)}",
        f"- **Unique keys** `(task_id, policy_id, run_id)`: {len(g)}",
        f"- **Keys with ≥2 rows or ≥2 distinct annotator_id**: {len(multi)}",
        "",
    ]

    if len(multi) == 0:
        lines += [
            "## Result",
            "",
            "**ICC not computed**: no duplicate keys with multiple raters. To report ICC in the paper,",
            "pilot a subset with **two human annotators** per `(task_id, policy_id, run_id)` (wide table",
            "or two rows per key), then use `pingouin.intraclass_corr` or Stata/R. Optional deps:",
            "`requirements-annotation.txt`.",
            "",
        ]
    else:
        # Long-format subset for future pingouin hook
        sub = df.merge(multi[keys], on=keys, how="inner")
        lines += [
            "## Result",
            "",
            f"Found **{len(multi)}** keys with multiple observations; automated ICC not run in MVP.",
            "Export a balanced rater×target matrix and use `pingouin` or textbook ICC(2,1).",
            "",
            "### Sample keys",
            "",
            "```",
            multi.head(20).to_string(index=False),
            "```",
            "",
            f"_Sub-table rows_: {len(sub)}",
            "",
        ]

    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
