"""
TESSA-PSA v2: merge price schedule, compute USD cost, optional value_score.

Uses stdlib only. Run from repo root:
  python src/tepsa_main.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "tessa_psa"


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


def fnum(x: str | None, default: float = 0.0) -> float:
    if x is None or x == "":
        return default
    try:
        return float(x)
    except ValueError:
        return default


def price_rows_by_model(tier: str = "standard") -> dict[str, dict[str, str]]:
    _, rows = read_csv(DATA_DIR / "api_price_schedule.csv")
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("pricing_tier", "standard") == tier:
            out[row["model_id"]] = row
    return out


def compute_cost_usd_row(obs: dict[str, str], pr: dict[str, str] | None) -> str:
    if not pr:
        return ""
    pin = fnum(pr.get("input_price_per_1m_usd"))
    pout = fnum(pr.get("output_price_per_1m_usd"))
    pc = fnum(pr.get("cached_input_price_per_1m_usd"))
    tin = fnum(obs.get("input_tokens"))
    tout = fnum(obs.get("output_tokens"))
    tc = fnum(obs.get("cache_tokens"))
    cost = tin / 1e6 * pin + tout / 1e6 * pout + tc / 1e6 * pc
    return f"{cost:.8f}".rstrip("0").rstrip(".")


def compute_value_score_row(
    obs: dict[str, str],
    wage_per_min: float = 1.0,
    gamma: float = 1.0,
    lambda_risk: float = 0.5,
    kappa: float = 0.3,
    quality_baseline: float = 5.0,
) -> str:
    try:
        hb = fnum(obs.get("human_time_base_min"))
        ha = fnum(obs.get("human_time_ai_min"))
        q = fnum(obs.get("quality_score"))
        rs = fnum(obs.get("risk_score"))
        rev = fnum(obs.get("review_effort_min"))
    except Exception:
        return ""
    if not obs.get("quality_score"):
        return ""
    tsave = max(0.0, hb - ha)
    qgain = q - quality_baseline
    val = wage_per_min * tsave + gamma * qgain - lambda_risk * rs - kappa * rev
    return f"{val:.6f}".rstrip("0").rstrip(".")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--obs",
        type=Path,
        default=DATA_DIR / "task_policy_observations.csv",
        help="Observations CSV (may be header-only).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DATA_DIR / "task_policy_observations_enriched.csv",
    )
    args = parser.parse_args()

    fields, obs_rows = read_csv(args.obs)
    obs_rows = [r for r in obs_rows if any((v or "").strip() for v in r.values())]
    if not obs_rows:
        print("Observations empty or only header; wrote no enriched file.")
        return

    prices = price_rows_by_model()
    out_fields = list(fields)
    for c in (
        "input_price_per_1m_usd",
        "cached_input_price_per_1m_usd",
        "output_price_per_1m_usd",
        "provider",
        "pricing_tier",
        "price_collected_date",
        "source_url",
    ):
        if c not in out_fields:
            out_fields.append(c)
    if "cost_usd" not in out_fields:
        out_fields.append("cost_usd")
    if "value_score" not in out_fields:
        out_fields.append("value_score")

    enriched: list[dict[str, object]] = []
    for row in obs_rows:
        mid = row.get("model_id") or row.get("model") or ""
        pr = prices.get(mid)
        er = dict(row)
        if pr:
            er.update(
                {
                    "provider": pr.get("provider", ""),
                    "pricing_tier": pr.get("pricing_tier", ""),
                    "input_price_per_1m_usd": pr.get("input_price_per_1m_usd", ""),
                    "cached_input_price_per_1m_usd": pr.get("cached_input_price_per_1m_usd", ""),
                    "output_price_per_1m_usd": pr.get("output_price_per_1m_usd", ""),
                    "price_collected_date": pr.get("price_collected_date", ""),
                    "source_url": pr.get("source_url", ""),
                }
            )
        er["cost_usd"] = compute_cost_usd_row(er, pr)
        vs = compute_value_score_row(er)
        er["value_score"] = vs if vs != "" else row.get("value_score", "")
        enriched.append(er)

    write_csv(args.out, out_fields, enriched)
    print(f"Wrote {args.out} ({len(enriched)} rows).")


if __name__ == "__main__":
    main()
