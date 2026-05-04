"""
Binary treatment IPW (Hajek) + overlap diagnostics on obs_macro_preview.

Treatment default: policy_id == pl_deepseek_pro vs others.
Covariates Z: difficulty_label, risk_class, tepsa_sector (pre-treatment only).

  pip install -r requirements-regression.txt
  python src/tepsa_regression_ipw.py
  python src/tepsa_regression_ipw.py --run-id ds_batch --treat-policy pl_deepseek_pro

Output: output/regression_ipw/tepsa_ipw_summary.md (+ optional csv).

This is MVP adjustment—not a substitute for random assignment; see outline §5.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from tepsa_regression_baseline import DEFAULT_INPUT, REPO_ROOT, _prep_base, _value_score_from_row

EPS = 1e-6

PROPENSITY_FORMULA = "T ~ C(difficulty_label) + C(risk_class) + C(tepsa_sector)"


class IPWFrameBuildError(Exception):
    """Non-fatal for plotting; CLI converts to SystemExit."""


def _hajek_ate(T: np.ndarray, Y: np.ndarray, p: np.ndarray) -> tuple[float, float, float]:
    """Returns (mu1, mu0, ate). T in {0,1}, p = P(T=1|Z) clipped."""
    T = T.astype(float)
    w1 = T / p
    w0 = (1.0 - T) / (1.0 - p)
    mu1 = float(np.sum(w1 * Y) / np.sum(w1))
    mu0 = float(np.sum(w0 * Y) / np.sum(w0))
    return mu1, mu0, mu1 - mu0


def build_ipw_frame(
    input_path: Path,
    run_id: str,
    treat_policy: str,
    outcome: str,
    clip: float,
) -> tuple[pd.DataFrame, object, str, str]:
    """
    Single source for IPW analysis rows + clipped propensity.

    Returns
    -------
    dz : DataFrame
        Analysis sample with columns T, Y, pscore (clipped), plus covariates.
    logit : fitted discrete model results
    formula : str
        Propensity logit formula (same as PROPENSITY_FORMULA).
    ycol : str
        Outcome column name used (quality_score or value_score_reg).
    """
    df = pd.read_csv(input_path, encoding="utf-8")
    df = _prep_base(df)
    for col in ("difficulty_label", "risk_class"):
        if col not in df.columns:
            raise IPWFrameBuildError(f"Missing column {col} for propensity model.")
    if run_id.strip():
        df = df[df["run_id"] == run_id.strip()]
    if df.empty:
        raise IPWFrameBuildError("No rows after run_id filter.")

    df["difficulty_label"] = df["difficulty_label"].astype(str).str.strip()
    df["risk_class"] = df["risk_class"].astype(str).str.strip()

    df["value_score_calc"] = df.apply(_value_score_from_row, axis=1)
    _vs_file = pd.to_numeric(df["value_score"], errors="coerce")
    df["value_score_reg"] = _vs_file.where(_vs_file.notna(), df["value_score_calc"])

    df["T"] = (df["policy_id"] == treat_policy.strip()).astype(int)
    if df["T"].nunique() < 2:
        raise IPWFrameBuildError("Treatment is degenerate (need both T=0 and T=1).")

    ycol = "quality_score" if outcome == "quality" else "value_score_reg"
    dz = df[
        df[ycol].notna()
        & np.isfinite(pd.to_numeric(df[ycol], errors="coerce"))
        & df["difficulty_label"].notna()
        & df["risk_class"].notna()
        & df["tepsa_sector"].notna()
    ].copy()
    if outcome == "quality":
        dz = dz[pd.to_numeric(dz["quality_score"], errors="coerce") > 0]

    dz["Y"] = pd.to_numeric(dz[ycol], errors="coerce")

    for c in ("difficulty_label", "risk_class", "tepsa_sector"):
        vc = dz[c].value_counts()
        dz = dz[dz[c].isin(vc[vc >= 5].index)]

    if len(dz) < 40:
        raise IPWFrameBuildError("Too few rows after Z filters for IPW.")

    formula = PROPENSITY_FORMULA
    try:
        logit = smf.logit(formula, data=dz).fit(disp=False, maxiter=200, method="lbfgs")
    except Exception as e:
        raise IPWFrameBuildError(f"Logit failed: {e}") from e

    p = np.asarray(logit.predict(dz), dtype=float)
    p = np.clip(p, clip, 1.0 - clip)
    dz = dz.copy()
    dz["pscore"] = p
    return dz, logit, formula, ycol


def run_ipw(
    input_path: Path,
    out_dir: Path,
    run_id: str,
    treat_policy: str,
    clip: float,
    outcome: str,
) -> None:
    try:
        dz, logit, formula, ycol = build_ipw_frame(
            input_path, run_id, treat_policy, outcome, clip
        )
    except IPWFrameBuildError as e:
        raise SystemExit(str(e)) from e

    p = np.asarray(dz["pscore"], dtype=float)
    T = np.asarray(dz["T"], dtype=float)
    Y = np.asarray(dz["Y"], dtype=float)

    mu1, mu0, ate = _hajek_ate(T, Y, p)

    try:
        in_rel = input_path.relative_to(REPO_ROOT)
    except ValueError:
        in_rel = input_path

    out_dir.mkdir(parents=True, exist_ok=True)
    md = [
        "# TESSA-PSA binary IPW (Hajek) + overlap",
        "",
        f"- **Input**: `{in_rel}`",
        f"- **run_id**: `{run_id or '(none)'}`",
        f"- **Outcome**: `{ycol}`",
        f"- **Treatment**: `policy_id == '{treat_policy}'` (else 0)",
        f"- **Propensity**: logit `{formula}`",
        f"- **p clipping**: [{clip}, {1.0 - clip}]",
        f"- **N**: {len(dz)} (after Z completeness + min cell ≥5 per Z level)",
        "",
        "## Overlap (fitted p = P(T=1|Z))",
        "",
        f"- Treated n = {int((T == 1).sum())}, control n = {int((T == 0).sum())}",
        f"- p among treated — min/median/max: `{float(np.min(p[T == 1])):.4f}` / `{float(np.median(p[T == 1])):.4f}` / `{float(np.max(p[T == 1])):.4f}`"
        if (T == 1).any()
        else "",
        f"- p among control — min/median/max: `{float(np.min(p[T == 0])):.4f}` / `{float(np.median(p[T == 0])):.4f}` / `{float(np.max(p[T == 0])):.4f}`"
        if (T == 0).any()
        else "",
        "",
        "## Hajek ATE (population mean difference, IPW)",
        "",
        f"- E[Y|T=1] ≈ `{mu1:.6f}`",
        f"- E[Y|T=0] ≈ `{mu0:.6f}`",
        f"- **ATE** ≈ `{ate:.6f}`",
        "",
        "*解释*：在可交换性/无未测混杂等假设下对 ATE 的加权估计；本数据未必满足，故作**敏感性/对照**而非主因果结论。",
        "",
        "```",
        logit.summary().as_text(),
        "```",
        "",
    ]
    (out_dir / "tepsa_ipw_summary.md").write_text("\n".join(md), encoding="utf-8")

    pd.DataFrame(
        {
            "treat_policy": [treat_policy],
            "outcome": [ycol],
            "n": [len(dz)],
            "ate_hajek": [ate],
            "mu_treated": [mu1],
            "mu_control": [mu0],
            "p_treated_min": [float(np.min(p[T == 1]))] if (T == 1).any() else [np.nan],
            "p_control_max": [float(np.max(p[T == 0]))] if (T == 0).any() else [np.nan],
        }
    ).to_csv(out_dir / "tepsa_ipw_ate.csv", index=False, encoding="utf-8")

    print(f"Wrote {out_dir / 'tepsa_ipw_summary.md'}")
    print(f"Wrote {out_dir / 'tepsa_ipw_ate.csv'}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Binary IPW ATE with overlap diagnostics")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=_REPO / "output" / "regression_ipw")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--treat-policy", default="pl_deepseek_pro", help="policy_id defining T=1")
    ap.add_argument("--clip", type=float, default=0.05, help="Trim propensity to [clip, 1-clip]")
    ap.add_argument("--outcome", choices=("quality", "value"), default="quality")
    args = ap.parse_args()
    run_ipw(args.input, args.out_dir, args.run_id, args.treat_policy, args.clip, args.outcome)


if __name__ == "__main__":
    main()
