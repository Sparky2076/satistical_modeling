"""
Build a base occupation_code_mapping.csv from local SOC_Structure.csv.

This produces a clean SOC hierarchy mapping table and leaves placeholders for
Chinese national/CFPS occupation codes to be filled later.

Input:
- SOC_Structure.csv

Output:
- data/processed/occupation_code_mapping.csv
"""

from __future__ import annotations

import argparse
import os

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build base occupation code mapping table.")
    parser.add_argument("--soc-structure", default="SOC_Structure.csv")
    parser.add_argument("--out", default="data/processed/occupation_code_mapping.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.soc_structure)

    needed = {
        "Major Group",
        "Minor Group",
        "Broad Occupation",
        "Detailed Occupation",
        "Detailed O*NET-SOC",
        "SOC or O*NET-SOC 2019 Title",
    }
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"{args.soc_structure} missing required columns: {missing}")

    out = df[
        [
            "Major Group",
            "Minor Group",
            "Broad Occupation",
            "Detailed Occupation",
            "Detailed O*NET-SOC",
            "SOC or O*NET-SOC 2019 Title",
        ]
    ].copy()

    out = out.rename(
        columns={
            "Major Group": "soc_major_group",
            "Minor Group": "soc_minor_group",
            "Broad Occupation": "soc_broad_occupation",
            "Detailed Occupation": "soc_detailed_occupation",
            "Detailed O*NET-SOC": "soc_code",
            "SOC or O*NET-SOC 2019 Title": "soc_title",
        }
    )

    out["soc_code"] = out["soc_code"].astype(str).str.strip()
    out["soc_title"] = out["soc_title"].astype(str).str.strip()

    # Placeholders for downstream manual/semi-auto crosswalk.
    out["isco08_code"] = ""
    out["gbt_occ_code"] = ""
    out["cfps_occ_code"] = ""
    out["mapping_method"] = "soc_structure_base"
    out["confidence"] = "unmapped"

    out = out.drop_duplicates(subset=["soc_code", "soc_title"]).sort_values("soc_code")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8-sig")

    print(f"[OK] {args.out}")
    print(f"[INFO] Rows: {len(out)}")


if __name__ == "__main__":
    main()

