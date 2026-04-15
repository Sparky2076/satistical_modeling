"""
Build occupation_exposure.csv from local raw files only.

Inputs (default at repo root):
- job_exposure.csv
- onet_task_statements.csv

Output:
- data/processed/occupation_exposure.csv

Columns:
- occupation_code
- routine_task_score
- cognitive_task_score
- social_task_score
- ai_exposure_score
- llm_exposure_score
- source
"""

from __future__ import annotations

import argparse
import os
import re
from typing import Dict, Iterable, List

import pandas as pd


ROUTINE_KWS = [
    "record",
    "file",
    "sort",
    "inspect",
    "process",
    "operate",
    "monitor",
    "schedule",
    "document",
    "repeat",
]

COGNITIVE_KWS = [
    "analyze",
    "evaluate",
    "design",
    "develop",
    "research",
    "diagnose",
    "optimize",
    "model",
    "plan",
    "solve",
]

SOCIAL_KWS = [
    "communicate",
    "coordinate",
    "negotiate",
    "teach",
    "train",
    "advise",
    "consult",
    "assist",
    "lead",
    "present",
    "interview",
]


def _contains_any(text: str, kws: Iterable[str]) -> bool:
    return any(kw in text for kw in kws)


def _normalize_score(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    mn, mx = s.min(skipna=True), s.max(skipna=True)
    if pd.isna(mn) or pd.isna(mx) or mx <= mn:
        return s
    return (s - mn) / (mx - mn)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build occupation AI/task exposure table from local files.")
    parser.add_argument("--job-exposure", default="job_exposure.csv")
    parser.add_argument("--onet-tasks", default="onet_task_statements.csv")
    parser.add_argument("--out", default="data/processed/occupation_exposure.csv")
    return parser.parse_args()


def build_task_scores(onet_tasks_path: str) -> pd.DataFrame:
    task_df = pd.read_csv(onet_tasks_path)
    need_cols = {"O*NET-SOC Code", "Task"}
    if not need_cols.issubset(task_df.columns):
        raise ValueError(f"{onet_tasks_path} missing required columns: {need_cols - set(task_df.columns)}")

    task_df["occupation_code"] = task_df["O*NET-SOC Code"].astype(str).str.strip()
    task_df["task_text"] = task_df["Task"].fillna("").astype(str).str.lower()
    task_df["task_text"] = task_df["task_text"].str.replace(r"\s+", " ", regex=True)

    task_df["routine_hit"] = task_df["task_text"].apply(lambda x: 1 if _contains_any(x, ROUTINE_KWS) else 0)
    task_df["cognitive_hit"] = task_df["task_text"].apply(lambda x: 1 if _contains_any(x, COGNITIVE_KWS) else 0)
    task_df["social_hit"] = task_df["task_text"].apply(lambda x: 1 if _contains_any(x, SOCIAL_KWS) else 0)

    grp = task_df.groupby("occupation_code", as_index=False).agg(
        routine_task_score=("routine_hit", "mean"),
        cognitive_task_score=("cognitive_hit", "mean"),
        social_task_score=("social_hit", "mean"),
    )
    return grp


def build_ai_scores(job_exposure_path: str) -> pd.DataFrame:
    ai_df = pd.read_csv(job_exposure_path)
    need_cols = {"occ_code", "observed_exposure"}
    if not need_cols.issubset(ai_df.columns):
        raise ValueError(f"{job_exposure_path} missing required columns: {need_cols - set(ai_df.columns)}")

    ai_df["occupation_code"] = ai_df["occ_code"].astype(str).str.strip()
    ai_df["observed_exposure"] = pd.to_numeric(ai_df["observed_exposure"], errors="coerce")

    grp = ai_df.groupby("occupation_code", as_index=False).agg(
        ai_exposure_score=("observed_exposure", "mean"),
    )
    grp["ai_exposure_score"] = _normalize_score(grp["ai_exposure_score"])
    grp["llm_exposure_score"] = grp["ai_exposure_score"]
    return grp


def main() -> None:
    args = parse_args()

    task_scores = build_task_scores(args.onet_tasks)
    ai_scores = build_ai_scores(args.job_exposure)

    out = pd.merge(task_scores, ai_scores, on="occupation_code", how="outer")
    out["source"] = "local:onet_task_statements+job_exposure"

    # Keep required output columns order.
    out = out[
        [
            "occupation_code",
            "routine_task_score",
            "cognitive_task_score",
            "social_task_score",
            "ai_exposure_score",
            "llm_exposure_score",
            "source",
        ]
    ].sort_values("occupation_code")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"[OK] {args.out}")
    print(f"[INFO] Rows: {len(out)}")


if __name__ == "__main__":
    main()

