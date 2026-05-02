"""
Generate and validate a manual download checklist for NBS (data.stats.gov.cn).

Goal:
- Tell user exactly which province-year tables to manually download from NBS.
- Validate locally downloaded CSV files for coverage and schema.

Run:
    py -3.13 "src/nbs_download_checklist.py"
    py -3.13 "src/nbs_download_checklist.py" --validate-only
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class RequiredTable:
    purpose: str
    file_name: str
    expected_columns: List[str]
    min_year: int
    max_year: int
    search_keywords: List[str]
    note: str


REQUIRED_TABLES = [
    RequiredTable(
        purpose="Bartik base: province manufacturing employment share in 2010",
        file_name="data/raw/share_p2010.csv",
        expected_columns=["provcd", "share_p2010"],
        min_year=2010,
        max_year=2010,
        search_keywords=[
            "分地区",
            "按行业就业人员",
            "制造业",
            "城镇单位就业人员",
            "2010",
        ],
        note="需要31省统一口径。share_p2010 建议在 [0,1]。",
    ),
    RequiredTable(
        purpose="Province-year controls for regressions",
        file_name="data/raw/province_controls_raw.csv",
        expected_columns=[
            "provcd",
            "year",
            "gdp",
            "population",
            "urban_rate",
            "unemployment_rate",
            "mfg_share",
        ],
        min_year=2010,
        max_year=2020,
        search_keywords=[
            "地区生产总值",
            "常住人口",
            "城镇化率",
            "失业率",
            "制造业占比",
            "分地区",
            "2010-2020",
        ],
        note="控制变量建议年频并覆盖全部省份。",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NBS manual download checklist generator/validator.")
    parser.add_argument(
        "--out-checklist",
        default="data/README_nbs_download_checklist.md",
        help="Output markdown checklist path",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate local files; do not rewrite checklist markdown.",
    )
    return parser.parse_args()


def _write_checklist_md(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines: List[str] = []
    lines.append("# 国家统计局人工下载清单")
    lines.append("")
    lines.append("网站：`https://data.stats.gov.cn/`（无需登录可搜索/预览）")
    lines.append("")
    lines.append("## 操作流程（每张表都按此流程）")
    lines.append("")
    lines.append("1. 打开数据查询页，输入“检索关键词”。")
    lines.append("2. 选择“年度数据”，地区维度选“31省（不含港澳台）”。")
    lines.append("3. 年份范围按下表要求导出。")
    lines.append("4. 导出 CSV 后放入仓库指定路径。")
    lines.append("5. 运行本脚本校验：`py -3.13 src/nbs_download_checklist.py --validate-only`")
    lines.append("")
    lines.append("## 需要下载的表")
    lines.append("")

    for i, t in enumerate(REQUIRED_TABLES, start=1):
        lines.append(f"### {i}) {t.purpose}")
        lines.append(f"- 文件路径：`{t.file_name}`")
        lines.append(f"- 年份范围：`{t.min_year}-{t.max_year}`")
        lines.append(f"- 预期列：`{', '.join(t.expected_columns)}`")
        lines.append(f"- 检索关键词：`{' | '.join(t.search_keywords)}`")
        lines.append(f"- 备注：{t.note}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _validate_table(t: RequiredTable) -> List[str]:
    issues: List[str] = []
    if not os.path.exists(t.file_name):
        issues.append(f"[MISSING] {t.file_name} not found")
        return issues

    try:
        df = pd.read_csv(t.file_name)
    except Exception as exc:
        issues.append(f"[ERROR] {t.file_name} cannot be read as CSV: {exc}")
        return issues

    missing_cols = [c for c in t.expected_columns if c not in df.columns]
    if missing_cols:
        issues.append(f"[SCHEMA] {t.file_name} missing columns: {missing_cols}")

    # Year coverage checks if a year column exists.
    if "year" in t.expected_columns and "year" in df.columns:
        yy = pd.to_numeric(df["year"], errors="coerce")
        y_min = int(yy.min()) if yy.notna().any() else None
        y_max = int(yy.max()) if yy.notna().any() else None
        if y_min is None or y_max is None:
            issues.append(f"[YEAR] {t.file_name} year column empty/invalid")
        else:
            if y_min > t.min_year or y_max < t.max_year:
                issues.append(
                    f"[YEAR] {t.file_name} coverage {y_min}-{y_max}, expected {t.min_year}-{t.max_year}"
                )

    # Province coverage check if provcd exists.
    if "provcd" in t.expected_columns and "provcd" in df.columns:
        prov_count = df["provcd"].nunique(dropna=True)
        if prov_count < 31:
            issues.append(f"[PROV] {t.file_name} has {prov_count} unique provcd, expected >=31")

    # Basic sanity checks for share
    if "share_p2010" in df.columns:
        x = pd.to_numeric(df["share_p2010"], errors="coerce")
        bad = ((x < 0) | (x > 1)).sum()
        if bad > 0:
            issues.append(f"[RANGE] {t.file_name} has {int(bad)} rows outside [0,1] for share_p2010")

    return issues


def main() -> None:
    args = parse_args()

    if not args.validate_only:
        _write_checklist_md(args.out_checklist)
        print(f"[OK] checklist written: {args.out_checklist}")

    all_issues: List[str] = []
    for t in REQUIRED_TABLES:
        issues = _validate_table(t)
        if issues:
            all_issues.extend(issues)
        else:
            print(f"[OK] {t.file_name}")

    if all_issues:
        print("\n[VALIDATION] Issues found:")
        for x in all_issues:
            print("-", x)
    else:
        print("\n[VALIDATION] All required NBS tables look good.")


if __name__ == "__main__":
    main()

