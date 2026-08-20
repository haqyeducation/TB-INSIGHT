"""Join 2024 official TB province indicators to same-year BPS covariates."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "processed"

tb = pd.read_csv(CURATED / "tb_province_annual_official.csv", dtype={"province_code": str})
bps = pd.read_csv(CURATED / "bps_province_annual_official.csv", dtype={"province_code": str})
bps = bps[bps["year"] == 2024][[
    "province_code", "province", "year", "population", "population_density_per_km2",
    "population_reference_date", "sanitation_access_pct", "sanitation_reference_period",
]].rename(columns={"province": "province_bps"})
panel = tb.merge(bps, on=["province_code", "year"], how="left", validate="one_to_one")
panel["province_name_match"] = panel["province"].str.replace("KEP.", "KEPULAUAN", regex=False).eq(panel["province_bps"])
panel["notification_rate_recalculated_per_100k"] = panel["tb_cases_total"] / panel["population"] * 100_000
panel["cnr_difference_vs_published"] = (
    panel["notification_rate_recalculated_per_100k"] - panel["case_notification_rate_per_100k"]
)
panel["join_quality_flag"] = panel["population"].notna().map({True: "matched", False: "unmatched"})
if len(panel) != 38 or panel["population"].isna().any():
    raise ValueError("Expected a complete one-to-one 38-province join")
panel.to_csv(CURATED / "analysis_panel_province_2024.csv", index=False)
print({"rows": len(panel), "matched": int(panel["population"].notna().sum())})
