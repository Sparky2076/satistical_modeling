"""
Process newly pulled clean data files into model-ready tables.

Inputs (repo root):
- share_p2010_clean.csv
- robot_density_china_public_clean.csv
- province_controls_2010_clean.csv

Outputs:
- data/processed/bartik_prov_year.csv
- data/processed/province_controls.csv

Notes:
- `share_p2010` uses manufacturing_share_total_employment when available,
  otherwise falls back to manufacturing_share_urban_unit_employment.
- Province controls currently come from the available clean 2010 table.
"""

from __future__ import annotations

import os
import pandas as pd


IN_SHARE = "share_p2010_clean.csv"
IN_ROBOT = "robot_density_china_public_clean.csv"
IN_CTRL = "province_controls_2010_clean.csv"

OUT_BARTIK = "data/processed/bartik_prov_year.csv"
OUT_CTRL = "data/processed/province_controls.csv"


def _build_province_code_map(provinces: pd.Series) -> pd.DataFrame:
    uniq = sorted(provinces.dropna().astype(str).unique().tolist())
    return pd.DataFrame({"province": uniq, "provcd": list(range(1, len(uniq) + 1))})


def main() -> None:
    share = pd.read_csv(IN_SHARE)
    robot = pd.read_csv(IN_ROBOT)
    ctrl = pd.read_csv(IN_CTRL)

    # Build deterministic province code map from available clean file values.
    prov_map = _build_province_code_map(share["province"])

    # share_p2010
    share = share.copy()
    share["share_p2010"] = pd.to_numeric(share.get("manufacturing_share_total_employment"), errors="coerce")
    fallback = pd.to_numeric(share.get("manufacturing_share_urban_unit_employment"), errors="coerce")
    share["share_p2010"] = share["share_p2010"].fillna(fallback)
    share = share[["province", "share_p2010"]].merge(prov_map, on="province", how="left")

    # robot density
    robot = robot.copy()
    robot["year"] = pd.to_numeric(robot["year"], errors="coerce").astype("Int64")
    robot["robot_density_t"] = pd.to_numeric(
        robot["robot_density_per_10000_manufacturing_workers"], errors="coerce"
    )
    robot = robot[["year", "robot_density_t"]].dropna()

    # Cartesian join: province x year
    share["key"] = 1
    robot["key"] = 1
    bartik = share.merge(robot, on="key", how="inner").drop(columns=["key"])
    bartik["bartik_pt"] = bartik["share_p2010"] * bartik["robot_density_t"]
    bartik = bartik[["provcd", "province", "year", "share_p2010", "robot_density_t", "bartik_pt"]]
    bartik = bartik.sort_values(["provcd", "year"])

    # Province controls (currently 2010 clean table)
    ctrl = ctrl.copy()
    ctrl = ctrl.merge(prov_map, on="province", how="left")
    ctrl["year"] = pd.to_numeric(ctrl["year"], errors="coerce").astype("Int64")
    ctrl["gdp"] = pd.to_numeric(ctrl["gdp_100m_rmb"], errors="coerce")
    ctrl["population"] = pd.to_numeric(ctrl["population_year_end_10k_persons"], errors="coerce")
    ctrl["gdp_pc"] = pd.to_numeric(ctrl["per_capita_gdp_rmb"], errors="coerce")
    ctrl["ln_gdp_pc"] = pd.to_numeric(ctrl["gdp_pc"], errors="coerce")
    ctrl["ln_gdp_pc"] = ctrl["ln_gdp_pc"].where(ctrl["ln_gdp_pc"] > 0).map(lambda x: pd.NA if pd.isna(x) else x)
    ctrl["ln_gdp_pc"] = pd.to_numeric(ctrl["ln_gdp_pc"], errors="coerce")
    ctrl["ln_gdp_pc"] = ctrl["ln_gdp_pc"].apply(lambda x: pd.NA if pd.isna(x) else __import__("math").log(x))
    ctrl["urban_rate"] = pd.to_numeric(ctrl["urbanization_rate_pct_2010"], errors="coerce")
    ctrl["unemployment_rate"] = pd.to_numeric(ctrl["registered_unemployment_rate_pct"], errors="coerce")
    ctrl["mfg_share"] = pd.to_numeric(ctrl["manufacturing_share_total_employment"], errors="coerce")

    ctrl_out = ctrl[
        [
            "provcd",
            "province",
            "year",
            "gdp",
            "population",
            "gdp_pc",
            "ln_gdp_pc",
            "urban_rate",
            "unemployment_rate",
            "mfg_share",
        ]
    ].sort_values(["provcd", "year"])

    os.makedirs(os.path.dirname(OUT_BARTIK), exist_ok=True)
    bartik.to_csv(OUT_BARTIK, index=False, encoding="utf-8-sig")
    ctrl_out.to_csv(OUT_CTRL, index=False, encoding="utf-8-sig")

    print(f"[OK] {OUT_BARTIK} rows={len(bartik)}")
    print(f"[OK] {OUT_CTRL} rows={len(ctrl_out)}")
    print(f"[INFO] robot years covered: {sorted(bartik['year'].dropna().unique().tolist())}")


if __name__ == "__main__":
    main()

