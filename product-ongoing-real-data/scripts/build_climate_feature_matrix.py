"""Freeze the S3 climate feature matrix and machine-readable QA report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "processed" / "climate_province_month_official.csv"
OUT = ROOT / "data" / "processed" / "features"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(SOURCE, dtype={"province_code": str})
    keep = [
        "province_code", "province", "year", "month", "period",
        "temperature_c", "relative_humidity_pct", "precipitation_mm",
        "temperature_c_anomaly", "temperature_c_z", "temperature_c_z_lag1",
        "temperature_c_z_lag2", "temperature_c_z_lag3", "temperature_c_z_mean_lag0_2",
        "relative_humidity_pct_anomaly", "relative_humidity_pct_z",
        "relative_humidity_pct_z_lag1", "relative_humidity_pct_z_lag2",
        "relative_humidity_pct_z_lag3", "relative_humidity_pct_z_mean_lag0_2",
        "precipitation_mm_anomaly", "precipitation_mm_z", "precipitation_mm_z_lag1",
        "precipitation_mm_z_lag2", "precipitation_mm_z_lag3",
        "precipitation_mm_z_mean_lag0_2", "heavy_rain_anomaly", "hot_anomaly",
        "climate_spatial_method", "climate_grid_cells", "climate_source",
        "boundary_source", "source_url", "boundary_source_url",
    ]
    matrix = frame[keep].sort_values(["province_code", "year", "month"])
    matrix.to_csv(OUT / "climate_lags_v2.csv", index=False)
    z_columns = ["temperature_c_z", "relative_humidity_pct_z", "precipitation_mm_z"]
    extreme_rows = []
    for column in z_columns:
        subset = matrix.loc[matrix[column].abs() > 5, ["province_code", "province", "period", column]]
        for row in subset.to_dict("records"):
            row["variable"] = column
            row["z_value"] = row.pop(column)
            extreme_rows.append(row)
    qa = {
        "rows": len(matrix), "provinces": int(matrix.province_code.nunique()),
        "periods": int(matrix.period.nunique()),
        "duplicate_keys": int(matrix.duplicated(["province_code", "year", "month"]).sum()),
        "missing_values": int(matrix.isna().sum().sum()),
        "extreme_abs_z_gt_5_count": len(extreme_rows), "extreme_rows": extreme_rows,
        "qa_interpretation": "Extreme z-scores are retained and disclosed; they are not automatically errors because the denominator is a province-calendar-month climatological SD.",
    }
    (OUT / "climate_lags_v2_qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    main()
