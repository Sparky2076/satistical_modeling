"""
Download and normalize Anthropic Economic Index data from Hugging Face.

Usage:
    # Online mode: pull directly from Hugging Face
    py -3.13 "src/download_anthropic_economic_index.py"

    # Offline/manual mode: process a locally downloaded CSV
    py -3.13 "src/download_anthropic_economic_index.py" --input-csv "data/raw/anthropic/economic_index_manual.csv"

Outputs:
    data/raw/anthropic/economic_index_raw_<split>.csv
    data/raw/anthropic/economic_index_columns_<split>.txt
    data/raw/anthropic/occupation_exposure_anthropic.csv

Notes:
- The dataset has multiple releases/structures and the HF viewer can fail.
- This script auto-detects key columns and can run in two modes:
  1) online (download from HF)
  2) offline (process local CSV)
- If auto-detection fails, use --occ-col / --ai-col / --llm-col to override.
"""

from __future__ import annotations

import argparse
import os
import re
from typing import Optional, Sequence

import pandas as pd


def _find_first_match(columns: Sequence[str], patterns: Sequence[str]) -> Optional[str]:
    for pattern in patterns:
        rgx = re.compile(pattern, re.IGNORECASE)
        for col in columns:
            if rgx.search(col):
                return col
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Anthropic Economic Index and export occupation exposure CSV.")
    parser.add_argument("--dataset", default="Anthropic/EconomicIndex", help="Hugging Face dataset id.")
    parser.add_argument("--split", default=None, help="Split name. Default: first available split.")
    parser.add_argument("--out-dir", default="data/raw/anthropic", help="Output directory.")
    parser.add_argument("--input-csv", default=None, help="Local CSV path (offline mode). If set, skip HF download.")
    parser.add_argument("--occ-col", default=None, help="Manual occupation column name override.")
    parser.add_argument("--ai-col", default=None, help="Manual AI exposure column name override.")
    parser.add_argument("--llm-col", default=None, help="Manual LLM exposure column name override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    splits = []
    if args.input_csv:
        split = "local"
        df = pd.read_csv(args.input_csv)
    else:
        from datasets import load_dataset

        ds = load_dataset(args.dataset)
        splits = list(ds.keys())
        if not splits:
            raise RuntimeError(f"No splits found in dataset {args.dataset}")

        split = args.split or splits[0]
        if split not in ds:
            raise ValueError(f"Split '{split}' not found. Available splits: {splits}")
        df = ds[split].to_pandas()

    df.columns = [str(c).strip() for c in df.columns]

    raw_out = os.path.join(args.out_dir, f"economic_index_raw_{split}.csv")
    cols_out = os.path.join(args.out_dir, f"economic_index_columns_{split}.txt")
    exposure_out = os.path.join(args.out_dir, "occupation_exposure_anthropic.csv")

    df.to_csv(raw_out, index=False, encoding="utf-8-sig")
    with open(cols_out, "w", encoding="utf-8") as f:
        for c in df.columns:
            f.write(c + "\n")

    # Manual override > auto detect
    occ_col = args.occ_col or _find_first_match(
        df.columns,
        [
            r"\bsoc(\s|_|-)?code\b",
            r"\boccupation(\s|_|-)?code\b",
            r"\boccupation\b",
            r"\bjob(\s|_|-)?title\b",
        ],
    )
    ai_col = args.ai_col or _find_first_match(
        df.columns,
        [
            r"\bai(\s|_|-)?exposure\b",
            r"\bexposure(\s|_|-)?ai\b",
            r"\bautomation\b",
            r"\bimpact\b",
            r"\bpenetration\b",
        ],
    )
    llm_col = args.llm_col or _find_first_match(
        df.columns,
        [
            r"\bllm(\s|_|-)?exposure\b",
            r"\bobserved(\s|_|-)?exposure\b",
            r"\bmodel(\s|_|-)?exposure\b",
            r"\bllm\b",
        ],
    )

    if occ_col is None or ai_col is None:
        raise RuntimeError(
            "Auto-detection failed.\n"
            f"Detected occ_col={occ_col}, ai_col={ai_col}, llm_col={llm_col}\n"
            f"Please inspect {cols_out} and rerun with --occ-col / --ai-col / --llm-col."
        )

    if llm_col is None:
        llm_col = ai_col

    out = df[[occ_col, ai_col, llm_col]].copy()
    out.columns = ["occupation_code", "ai_exposure_score", "llm_exposure_score"]
    out["occupation_code"] = out["occupation_code"].astype(str).str.strip()
    out["ai_exposure_score"] = pd.to_numeric(out["ai_exposure_score"], errors="coerce")
    out["llm_exposure_score"] = pd.to_numeric(out["llm_exposure_score"], errors="coerce")
    out["source"] = "Anthropic Economic Index"
    out = out.dropna(subset=["occupation_code"]).drop_duplicates()

    out.to_csv(exposure_out, index=False, encoding="utf-8-sig")

    if args.input_csv:
        print("[OK] Processed local input:", args.input_csv)
    else:
        print("[OK] Downloaded split:", split)
    print("[OK] Raw data:", raw_out)
    print("[OK] Column list:", cols_out)
    print("[OK] Occupation exposure:", exposure_out)
    print("[INFO] Detected columns -> occ:", occ_col, "| ai:", ai_col, "| llm:", llm_col)
    if splits:
        print("[INFO] Available splits:", splits)


if __name__ == "__main__":
    main()

