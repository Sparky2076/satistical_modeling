"""
Rebuild data/tessa_psa/human_labels.csv from team exports under human_label _res/.

Concatenates ds_results_final.csv + glm_results_final.csv + spark_results_final.csv
(when present under human_label _res/), aligns GLM run_id tokens
(glm_batch_v3 / glm_batch_v4 / glm_batch_final -> glm_batch) so keys match
task_policy_observations.csv, then drop_duplicates on (task_id, policy_id, run_id).

  python src/tepsa_build_human_labels.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "tessa_psa"
EXPORT_DIR = REPO_ROOT / "human_label _res"

GLM_RUN_ALIASES = frozenset({"glm_batch_v3", "glm_batch_v4", "glm_batch_final"})


def normalize_run_id(run_id: str) -> str:
    r = (run_id or "").strip()
    if r in GLM_RUN_ALIASES:
        return "glm_batch"
    return r


def main() -> None:
    ap = argparse.ArgumentParser(description="Build human_labels.csv from *_results_final.csv exports.")
    ap.add_argument(
        "--ds",
        type=Path,
        default=EXPORT_DIR / "ds_results_final.csv",
        help="DeepSeek-side export (default: human_label _res/ds_results_final.csv).",
    )
    ap.add_argument(
        "--glm",
        type=Path,
        default=EXPORT_DIR / "glm_results_final.csv",
        help="GLM export (default: human_label _res/glm_results_final.csv).",
    )
    ap.add_argument(
        "--spark",
        type=Path,
        default=None,
        help="Optional Spark export CSV (same schema). If omitted and file missing, skipped.",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DATA_DIR / "human_labels.csv",
        help="Output path (default: data/tessa_psa/human_labels.csv).",
    )
    args = ap.parse_args()

    parts: list[pd.DataFrame] = []
    for p, name in [(args.ds, "ds"), (args.glm, "glm")]:
        if not p.is_file():
            raise SystemExit(f"Missing {name} export: {p}")
        parts.append(pd.read_csv(p))
    spark_path = args.spark or (EXPORT_DIR / "spark_results_final.csv")
    if args.spark is not None and not spark_path.is_file():
        raise SystemExit(f"Missing --spark file: {spark_path}")
    if args.spark is None and spark_path.is_file():
        parts.append(pd.read_csv(spark_path))
    elif args.spark is not None:
        parts.append(pd.read_csv(spark_path))

    df = pd.concat(parts, ignore_index=True)
    df["run_id"] = df["run_id"].astype(str).map(normalize_run_id)
    k = ["task_id", "policy_id", "run_id"]
    df = df.drop_duplicates(subset=k, keep="last")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"Wrote {args.out} rows={len(df)} (from {len(parts)} source file(s))")


if __name__ == "__main__":
    main()
