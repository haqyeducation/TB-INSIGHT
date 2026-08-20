"""Prepare BNPB event records as a province-month disaster covariate panel.

The operational BNPB search table provides dated event rows. The annual BNPB
workbooks are retained as independent official benchmarks because their totals
are compiled under a stated disaster threshold and can differ from the mutable
operational event table.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "bnpb"
CURATED_DIR = ROOT / "data" / "processed"
RAW_HTML = RAW_DIR / "bnpb_event_search_2024_2025_raw.html"
SOURCE_URL = "https://gis.bnpb.go.id/databencana/tabel/pencarian.php"
ANNUAL_URLS = {
    2024: "https://data.bnpb.go.id/dataset/f61d78e5-04c6-4ce8-9acf-e425dadc1f4d/resource/faeb2406-b800-4b8e-9e09-37d4b2aa5879/download/jumlah-kejadian-bencana-menurut-provinsi-2024.xlsx",
    2025: "https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/df39e8c3-117e-40fa-b518-ff1037743955/download/jumlah-kejadian-bencana-menurut-provinsi-2025.xlsx",
}


def normalize_province(value: object) -> str:
    name = " ".join(str(value).upper().split())
    mapping = {
        "DAERAH ISTIMEWA YOGYAKARTA": "DI YOGYAKARTA",
        "KEPULAUAN BANGKA BELITUNG": "KEP. BANGKA BELITUNG",
        "P A P U A": "PAPUA",
    }
    return mapping.get(name, name)


def load_events() -> tuple[pd.DataFrame, int]:
    raw = pd.read_html(RAW_HTML)[0]
    raw.columns = [
        "row_number", "disaster_identity_code", "district_code", "event_date", "event_type",
        "location", "district", "province_raw", "documentation", "cause", "deaths", "missing",
        "injured", "houses_damaged", "houses_flooded", "public_facilities_damaged",
    ]
    raw["event_date"] = pd.to_datetime(raw["event_date"], errors="coerce")
    raw["province"] = raw["province_raw"].map(normalize_province)
    numeric = ["deaths", "missing", "injured", "houses_damaged", "houses_flooded", "public_facilities_damaged"]
    for column in numeric:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
    substantive = [c for c in raw.columns if c != "row_number"]
    exact_duplicates = int(raw.duplicated(substantive).sum())
    events = raw.drop_duplicates(substantive, keep="first").copy()
    events["year"] = events.event_date.dt.year.astype("Int64")
    events["month"] = events.event_date.dt.month.astype("Int64")
    events["event_type"] = events.event_type.astype(str).str.upper().str.strip()
    events["event_record_count"] = 1
    events["has_any_impact_field"] = events[numeric].notna().any(axis=1).astype(int)
    events["source_url"] = SOURCE_URL
    return events, exact_duplicates


def aggregate(events: pd.DataFrame, province_lookup: pd.DataFrame) -> pd.DataFrame:
    groups = {
        "flood_events": ["BANJIR"],
        "landslide_events": ["TANAH LONGSOR"],
        "extreme_weather_events": ["CUACA EKSTREM"],
        "drought_events": ["KEKERINGAN"],
        "wildfire_events": ["KEBAKARAN HUTAN DAN LAHAN"],
        "coastal_wave_events": ["GELOMBANG PASANG DAN ABRASI"],
        "earthquake_events": ["GEMPABUMI"],
        "volcanic_eruption_events": ["ERUPSI GUNUNG API"],
        "tsunami_events": ["TSUNAMI", "GEMPA BUMI DAN TSUNAMI"],
    }
    for column, types in groups.items():
        events[column] = events.event_type.isin(types).astype(int)
    events["hydrometeorological_events"] = events[[
        "flood_events", "landslide_events", "extreme_weather_events", "drought_events",
        "wildfire_events", "coastal_wave_events",
    ]].sum(axis=1)

    sum_columns = ["event_record_count", "has_any_impact_field", *groups.keys(), "hydrometeorological_events"]
    impact_columns = ["deaths", "missing", "injured", "houses_damaged", "houses_flooded", "public_facilities_damaged"]
    # Impact fields are reporting fields. Blank values are not interpreted as
    # confirmed zero; sums are paired with completeness counts.
    aggregated = events.groupby(["province", "year", "month"], as_index=False)[sum_columns].sum()
    for column in impact_columns:
        sums = events.groupby(["province", "year", "month"])[column].sum(min_count=1).rename(f"{column}_reported_sum")
        counts = events.groupby(["province", "year", "month"])[column].count().rename(f"{column}_reported_records")
        aggregated = aggregated.merge(pd.concat([sums, counts], axis=1).reset_index(), on=["province", "year", "month"], how="left")

    skeleton = province_lookup.assign(key=1).merge(
        pd.DataFrame({"year": np.repeat([2024, 2025], 12), "month": list(range(1, 13)) * 2, "key": 1}),
        on="key",
    ).drop(columns="key")
    panel = skeleton.merge(aggregated, on=["province", "year", "month"], how="left", validate="one_to_one")
    count_columns = sum_columns + [f"{c}_reported_records" for c in impact_columns]
    panel[count_columns] = panel[count_columns].fillna(0).astype(int)
    panel["period"] = pd.to_datetime(dict(year=panel.year, month=panel.month, day=1)).dt.strftime("%Y-%m")
    panel["disaster_source"] = "BNPB operational disaster search table"
    panel["source_url"] = SOURCE_URL
    panel["quality_flag"] = "operational_snapshot_annual_totals_may_differ"
    return panel.sort_values(["province_code", "year", "month"])


def annual_benchmarks() -> pd.DataFrame:
    frames = []
    for year in [2024, 2025]:
        path = RAW_DIR / f"jumlah_kejadian_bencana_menurut_provinsi_{year}.xlsx"
        df = pd.read_excel(path, sheet_name=f"Jumlah Bencana {year}", header=1)
        df = df[df["Kode Wilayah Provinsi"].notna()].copy()
        df["year"] = year
        df["province_code_bnpb_workbook"] = pd.to_numeric(df["Kode Wilayah Provinsi"], errors="coerce").astype("Int64")
        df["province"] = df["Provinsi"].map(normalize_province)
        disaster_cols = list(df.columns[5:14])
        for column in disaster_cols:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)
        df["annual_official_total_events"] = df[disaster_cols].sum(axis=1)
        frames.append(df[["province_code_bnpb_workbook", "province", "year", "annual_official_total_events", *disaster_cols]])
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    base = pd.read_csv(CURATED_DIR / "analysis_panel_province_month_2024_2025.csv")
    lookup = base[["province_code", "province"]].drop_duplicates().sort_values("province_code")
    events, exact_duplicates = load_events()
    unknown = sorted(set(events.province) - set(lookup.province))
    if unknown:
        raise AssertionError(f"Unmatched BNPB provinces: {unknown}")

    events = events.merge(lookup, on="province", how="left", validate="many_to_one")
    panel = aggregate(events, lookup)
    benchmarks = annual_benchmarks().merge(lookup, on="province", how="left", validate="many_to_one")
    if benchmarks.province_code.isna().any():
        raise AssertionError("Unmatched province names in BNPB annual workbooks")
    operational_annual = panel.groupby(["province_code", "province", "year"], as_index=False).event_record_count.sum()
    comparison = benchmarks.merge(operational_annual, on=["province_code", "province", "year"], how="outer", validate="one_to_one")
    comparison["difference_operational_minus_annual"] = comparison.event_record_count - comparison.annual_official_total_events
    comparison["agreement_flag"] = np.where(comparison.difference_operational_minus_annual == 0, "match", "different_definition_or_snapshot")

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    event_columns = [
        "province_code", "province", "province_raw", "year", "month", "event_date", "event_type",
        "district_code", "district", "location", "deaths", "missing", "injured", "houses_damaged",
        "houses_flooded", "public_facilities_damaged", "has_any_impact_field", "source_url",
    ]
    events[event_columns].sort_values(["event_date", "province", "district"]).to_csv(CURATED_DIR / "bnpb_disaster_events_2024_2025_official.csv", index=False)
    panel.to_csv(CURATED_DIR / "bnpb_disaster_province_month_official.csv", index=False)
    comparison.to_csv(CURATED_DIR / "bnpb_disaster_annual_reconciliation.csv", index=False)

    validation = {
        "raw_rows": int(len(pd.read_html(RAW_HTML)[0])),
        "exact_duplicate_substantive_rows_removed": exact_duplicates,
        "curated_event_rows": int(len(events)),
        "panel_rows": int(len(panel)),
        "provinces": int(panel.province_code.nunique()),
        "periods": int(panel[["year", "month"]].drop_duplicates().shape[0]),
        "duplicate_panel_keys": int(panel.duplicated(["province_code", "year", "month"]).sum()),
        "unmatched_provinces": unknown,
        "operational_event_totals": {str(k): int(v) for k, v in events.groupby("year").size().items()},
        "official_annual_workbook_totals": {str(k): int(v) for k, v in benchmarks.groupby("year").annual_official_total_events.sum().items()},
        "annual_province_totals_matching": int((comparison.agreement_flag == "match").sum()),
        "annual_province_totals_compared": int(len(comparison)),
        "notes": [
            "Operational rows were retrieved with event dates 2024-01-01 through 2025-12-31.",
            "Exact duplicates across all substantive HTML fields were removed; row_number was excluded from duplicate detection.",
            "Annual workbooks use BNPB's formal event-threshold compilation and are retained as benchmarks, not used to overwrite monthly operational counts.",
            "Impact blanks remain missing in reported sums; reported-record counts quantify completeness.",
            "Use disaster variables as secondary/sensitivity covariates because monthly operational totals do not fully reconcile with annual workbooks.",
        ],
        "source_url": SOURCE_URL,
        "annual_source_urls": ANNUAL_URLS,
    }
    (CURATED_DIR / "bnpb_disaster_province_month_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
