"""
Micro-level AI labor impact pipeline.

This script builds a merged micro dataset and runs baseline regressions aligned
with a macro Bartik design:
    Y_it = beta1 * bartik_pt + beta2 * exposure_o + beta3 * bartik_pt*exposure_o
           + controls + FE + error

Input CSV files (user-provided):
1) micro individual panel (required): data/raw/cfps_micro.csv
2) province-year bartik (required): data/raw/bartik_prov_year.csv
3) occupation exposure (required): data/raw/occupation_exposure.csv
4) province-year controls (optional): data/raw/province_controls.csv

Outputs:
- data/processed/micro_merged.csv
- data/processed/regression_results.txt
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


def _require_columns(df: pd.DataFrame, required: List[str], table_name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{table_name} missing required columns: {missing}")


def _safe_log(series: pd.Series) -> pd.Series:
    return np.log(series.where(series > 0))


@dataclass
class PipelineConfig:
    micro_path: str
    bartik_path: str
    exposure_path: str
    controls_path: str | None
    output_merged_path: str
    output_report_path: str
    winsor_lower: float
    winsor_upper: float
    run_regression: bool


def load_and_validate_inputs(cfg: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    micro = pd.read_csv(cfg.micro_path)
    bartik = pd.read_csv(cfg.bartik_path)
    exposure = pd.read_csv(cfg.exposure_path)
    controls = pd.read_csv(cfg.controls_path) if cfg.controls_path and os.path.exists(cfg.controls_path) else None

    _require_columns(
        micro,
        ["pid", "year", "provcd", "occ_code", "age", "gender", "edu_years", "married", "employment", "wage"],
        "micro",
    )
    _require_columns(bartik, ["provcd", "year"], "bartik")
    _require_columns(exposure, ["occ_code", "exposure_score"], "occupation_exposure")

    if "bartik_pt" not in bartik.columns:
        _require_columns(bartik, ["share_p2010", "robot_density_t"], "bartik")
        bartik["bartik_pt"] = bartik["share_p2010"] * bartik["robot_density_t"]

    if controls is not None:
        _require_columns(controls, ["provcd", "year"], "province_controls")

    return micro, bartik, exposure, controls


def build_features(
    micro: pd.DataFrame,
    bartik: pd.DataFrame,
    exposure: pd.DataFrame,
    controls: pd.DataFrame | None,
    winsor_lower: float,
    winsor_upper: float,
) -> pd.DataFrame:
    df = micro.copy()

    # Standardize key types for stable merges.
    df["pid"] = df["pid"].astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["provcd"] = pd.to_numeric(df["provcd"], errors="coerce").astype("Int64")
    df["occ_code"] = df["occ_code"].astype(str)

    bartik = bartik.copy()
    bartik["year"] = pd.to_numeric(bartik["year"], errors="coerce").astype("Int64")
    bartik["provcd"] = pd.to_numeric(bartik["provcd"], errors="coerce").astype("Int64")

    exposure = exposure.copy()
    exposure["occ_code"] = exposure["occ_code"].astype(str)

    # Core merges: province-year Bartik + occupation exposure.
    df = df.merge(
        bartik[["provcd", "year", "bartik_pt"]],
        on=["provcd", "year"],
        how="left",
        validate="m:1",
    )
    df = df.merge(
        exposure[["occ_code", "exposure_score"]],
        on="occ_code",
        how="left",
        validate="m:1",
    )

    if controls is not None:
        c = controls.copy()
        c["year"] = pd.to_numeric(c["year"], errors="coerce").astype("Int64")
        c["provcd"] = pd.to_numeric(c["provcd"], errors="coerce").astype("Int64")
        df = df.merge(c, on=["provcd", "year"], how="left", validate="m:1")

    # Baseline controls/features.
    df["age2"] = pd.to_numeric(df["age"], errors="coerce") ** 2
    df["female"] = pd.to_numeric(df["gender"], errors="coerce").map({0: 0, 1: 1, 2: 0})
    df["emp_it"] = pd.to_numeric(df["employment"], errors="coerce").fillna(0).astype(int)
    df["wage"] = pd.to_numeric(df["wage"], errors="coerce")

    # Winsorize wage and take logs.
    low = df["wage"].quantile(winsor_lower)
    high = df["wage"].quantile(winsor_upper)
    df["wage_winsor"] = df["wage"].clip(lower=low, upper=high)
    df["ln_wage_it"] = _safe_log(df["wage_winsor"])

    # Occupation switching: current occ_code vs lagged occ_code within person.
    df = df.sort_values(["pid", "year"])
    df["occ_code_lag"] = df.groupby("pid")["occ_code"].shift(1)
    df["switch_it"] = ((df["occ_code_lag"].notna()) & (df["occ_code"] != df["occ_code_lag"])).astype(int)

    # Main interaction.
    df["bartik_x_exposure"] = df["bartik_pt"] * df["exposure_score"]

    return df


def run_baseline_regressions(df: pd.DataFrame) -> str:
    try:
        import statsmodels.formula.api as smf
    except ImportError as exc:
        raise RuntimeError(
            "statsmodels not installed. Install with: py -3.13 -m pip install statsmodels"
        ) from exc

    report_parts: List[str] = []
    report_parts.append("=== Baseline Regressions ===")
    report_parts.append(
        "Spec: Y ~ bartik_pt + exposure_score + bartik_x_exposure + age + age2 + female + edu_years + married + C(year)"
    )

    # 1) Employment (LPM style)
    emp_df = df.dropna(
        subset=["emp_it", "bartik_pt", "exposure_score", "bartik_x_exposure", "age", "age2", "edu_years", "married"]
    ).copy()
    if len(emp_df) > 0:
        m_emp = smf.ols(
            "emp_it ~ bartik_pt + exposure_score + bartik_x_exposure + age + age2 + female + edu_years + married + C(year)",
            data=emp_df,
        ).fit(cov_type="cluster", cov_kwds={"groups": emp_df["provcd"]})
        report_parts.append("\n--- Model 1: Employment ---")
        report_parts.append(m_emp.summary().as_text())

    # 2) Log wage
    wage_df = df.dropna(
        subset=["ln_wage_it", "bartik_pt", "exposure_score", "bartik_x_exposure", "age", "age2", "edu_years", "married"]
    ).copy()
    if len(wage_df) > 0:
        m_wage = smf.ols(
            "ln_wage_it ~ bartik_pt + exposure_score + bartik_x_exposure + age + age2 + female + edu_years + married + C(year)",
            data=wage_df,
        ).fit(cov_type="cluster", cov_kwds={"groups": wage_df["provcd"]})
        report_parts.append("\n--- Model 2: Log Wage ---")
        report_parts.append(m_wage.summary().as_text())

    # 3) Occupational switching
    sw_df = df.dropna(
        subset=["switch_it", "bartik_pt", "exposure_score", "bartik_x_exposure", "age", "age2", "edu_years", "married"]
    ).copy()
    if len(sw_df) > 0:
        m_switch = smf.ols(
            "switch_it ~ bartik_pt + exposure_score + bartik_x_exposure + age + age2 + female + edu_years + married + C(year)",
            data=sw_df,
        ).fit(cov_type="cluster", cov_kwds={"groups": sw_df["provcd"]})
        report_parts.append("\n--- Model 3: Occupation Switching ---")
        report_parts.append(m_switch.summary().as_text())

    return "\n".join(report_parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build micro AI impact dataset and run baseline regressions.")
    parser.add_argument("--micro-path", default="data/raw/cfps_micro.csv")
    parser.add_argument("--bartik-path", default="data/raw/bartik_prov_year.csv")
    parser.add_argument("--exposure-path", default="data/raw/occupation_exposure.csv")
    parser.add_argument("--controls-path", default="data/raw/province_controls.csv")
    parser.add_argument("--output-merged-path", default="data/processed/micro_merged.csv")
    parser.add_argument("--output-report-path", default="data/processed/regression_results.txt")
    parser.add_argument("--winsor-lower", type=float, default=0.01)
    parser.add_argument("--winsor-upper", type=float, default=0.99)
    parser.add_argument("--skip-regression", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = PipelineConfig(
        micro_path=args.micro_path,
        bartik_path=args.bartik_path,
        exposure_path=args.exposure_path,
        controls_path=args.controls_path,
        output_merged_path=args.output_merged_path,
        output_report_path=args.output_report_path,
        winsor_lower=args.winsor_lower,
        winsor_upper=args.winsor_upper,
        run_regression=not args.skip_regression,
    )

    micro, bartik, exposure, controls = load_and_validate_inputs(cfg)
    merged = build_features(
        micro=micro,
        bartik=bartik,
        exposure=exposure,
        controls=controls,
        winsor_lower=cfg.winsor_lower,
        winsor_upper=cfg.winsor_upper,
    )

    os.makedirs(os.path.dirname(cfg.output_merged_path), exist_ok=True)
    merged.to_csv(cfg.output_merged_path, index=False, encoding="utf-8-sig")

    if cfg.run_regression:
        report = run_baseline_regressions(merged)
        os.makedirs(os.path.dirname(cfg.output_report_path), exist_ok=True)
        with open(cfg.output_report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] Merged data: {cfg.output_merged_path}")
        print(f"[OK] Regression report: {cfg.output_report_path}")
    else:
        print(f"[OK] Merged data only: {cfg.output_merged_path}")


if __name__ == "__main__":
    main()
