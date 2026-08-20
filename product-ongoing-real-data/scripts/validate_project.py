"""Fail-fast validation for the analysis-ready TB-INSIGHT handoff."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
PANEL_PATH = DATA / "analysis_panel_tb_climate_disaster_2024_2025.csv"
VALIDATION_PATH = DATA / "analysis_panel_tb_climate_validation.json"
REQUIRED_COLUMNS = {
    "province_code",
    "province",
    "year",
    "month",
    "period",
    "jumlah_pasien",
    "population",
    "population_density_per_km2",
    "poverty_pct",
    "sanitation_access_pct",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "event_record_count",
}


def main() -> None:
    panel = pd.read_csv(PANEL_PATH, dtype={"province_code": str})
    missing_columns = sorted(REQUIRED_COLUMNS - set(panel.columns))
    assert not missing_columns, f"Kolom wajib hilang: {missing_columns}"
    assert len(panel) == 912, f"Jumlah baris bukan 912: {len(panel)}"
    assert panel["province_code"].nunique() == 38, "Cakupan bukan 38 provinsi"
    assert panel["period"].nunique() == 24, "Cakupan bukan 24 bulan"
    assert not panel.duplicated(["province_code", "period"]).any(), "Kunci provinsi-bulan duplikat"
    assert not panel[list(REQUIRED_COLUMNS)].isna().any().any(), "Ada missing pada variabel wajib"
    assert (panel["jumlah_pasien"] >= 0).all(), "Ada outcome negatif"

    validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    assert validation["all_required_complete"] is True
    assert validation["outcome_balance_failures"] == 0
    print({
        "status": "PASS",
        "rows": len(panel),
        "provinces": panel["province_code"].nunique(),
        "periods": panel["period"].nunique(),
        "period_min": panel["period"].min(),
        "period_max": panel["period"].max(),
    })


if __name__ == "__main__":
    main()

