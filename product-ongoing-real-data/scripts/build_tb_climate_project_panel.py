"""Build the analysis-ready TB-climate province-month panel and metadata."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "processed"


def source_ledger() -> pd.DataFrame:
    rows = [
        {
            "dataset_id": "SITB_TREATMENT_OUTCOMES_PROVINCE_MONTH",
            "publisher": "Kementerian Kesehatan RI - SITB",
            "source_url": "https://tbdashboard.sitb.id/ss_data_tbc03so_2024_provinsi_bulanan_list.php ; https://tbdashboard.sitb.id/ss_data_tbc03so_2025_provinsi_bulanan_list.php",
            "coverage": "38 provinces; monthly; 2024-2025",
            "role": "Primary outcome",
            "status": "Complete for public 2024-2025 endpoints",
            "local_files": "data/raw/sitb_dashboard/*.csv; data/processed/tb_treatment_outcomes_province_month_official.csv",
            "limitation": "Treatment-start cohorts, not TB incidence. 2025 outcomes are highly provisional due to pending outcomes.",
        },
        {
            "dataset_id": "BPS_PROVINCE_ANNUAL_COVARIATES",
            "publisher": "Badan Pusat Statistik",
            "source_url": "https://www.bps.go.id/",
            "coverage": "38 provinces; annual; 2023-2026 depending on indicator",
            "role": "Population offset and structural covariates",
            "status": "Complete for population, density, sanitation, poverty in 2024-2025",
            "local_files": "data/raw/bps/*.pdf; data/processed/bps_province_annual_official.csv",
            "limitation": "Annual/survey-period measures repeated across months; not monthly observations.",
        },
        {
            "dataset_id": "NASA_POWER_MERRA2_MONTHLY",
            "publisher": "NASA POWER",
            "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/monthly/",
            "coverage": "38 provinces; monthly 1981-2025; panel output 2024-2025",
            "role": "Primary exposures: temperature, humidity, precipitation anomalies",
            "status": "Complete, 912/912 panel rows",
            "local_files": "data/raw/nasa_power/*.nc; data/processed/climate_province_month_official.csv",
            "limitation": "Reanalysis grid, not station observations; small/island provinces may use nearest grid cell and are flagged.",
        },
        {
            "dataset_id": "BIG_PROVINCE_BOUNDARIES",
            "publisher": "Badan Informasi Geospasial",
            "source_url": "https://geoservices.big.go.id/rbi/rest/services/BATASWILAYAH/BATAS_WILAYAH/MapServer/12",
            "coverage": "38 provinces; official polygon service snapshot",
            "role": "Spatial aggregation support",
            "status": "Complete; generalized export processed",
            "local_files": "data/raw/big/big_province_boundaries_generalized.geojson",
            "limitation": "Generalized to 0.05 degrees and topology-repaired for grid aggregation; not suitable for legal boundary use.",
        },
        {
            "dataset_id": "BNPB_OPERATIONAL_EVENTS",
            "publisher": "Badan Nasional Penanggulangan Bencana",
            "source_url": "https://gis.bnpb.go.id/databencana/tabel/pencarian.php",
            "coverage": "Dated event records; 2024-2025; 38 provinces after aggregation",
            "role": "Secondary/sensitivity covariate",
            "status": "Extracted; 7,143 deduplicated records and 912 panel rows",
            "local_files": "data/raw/bnpb/bnpb_event_search_2024_2025_raw.html; data/processed/bnpb_disaster_province_month_official.csv",
            "limitation": "Operational snapshot does not fully reconcile with formal annual BNPB workbooks; not a primary exposure.",
        },
        {
            "dataset_id": "BNPB_ANNUAL_BENCHMARKS",
            "publisher": "Badan Nasional Penanggulangan Bencana",
            "source_url": "https://data.bnpb.go.id/dataset/data-bencana-indonesia ; https://data.bnpb.go.id/dataset/kompilasi-data-kejadian-dan-dampak-bencana-2025",
            "coverage": "38 provinces; annual 2024-2025",
            "role": "Quality benchmark for operational event panel",
            "status": "Complete and reconciled by province name",
            "local_files": "data/raw/bnpb/jumlah_kejadian_bencana_menurut_provinsi_*.xlsx; data/processed/bnpb_disaster_annual_reconciliation.csv",
            "limitation": "Annual only; formal threshold/compilation differs from operational event table.",
        },
    ]
    return pd.DataFrame(rows)


def build_codebook(columns: list[str]) -> pd.DataFrame:
    definitions = {
        "province_code": ("BPS/Kemendagri-style province code used in the project", "identifier", "SITB/BPS harmonisation"),
        "province": ("Harmonised uppercase province name", "identifier", "SITB/BPS harmonisation"),
        "year": ("Calendar year of TB treatment-start cohort month", "time", "SITB"),
        "month": ("Calendar month 1-12", "time", "SITB"),
        "period": ("Year-month key YYYY-MM", "time", "Derived"),
        "jumlah_pasien": ("Patients starting drug-susceptible TB treatment in the month", "count", "SITB"),
        "known_outcome_count": ("Patients with a recorded outcome other than pending", "count", "Derived: jumlah_pasien - belum_ada_hasil"),
        "pending_share": ("Share of cohort whose outcome is not yet available", "proportion", "Derived"),
        "treatment_success": ("Cured plus treatment completed", "count", "Derived from SITB"),
        "treatment_success_all_share": ("Treatment success divided by full cohort", "proportion", "Derived"),
        "treatment_success_known_share": ("Treatment success divided by patients with known outcomes", "proportion", "Derived"),
        "adverse_known_count": ("Lost to follow-up plus death plus failure", "count", "Derived"),
        "adverse_known_share": ("Adverse known outcomes divided by known outcomes", "proportion", "Derived"),
        "cohort_maturity_flag": ("Mature when pending outcome share is at most 5%", "quality flag", "Derived"),
        "treatment_started_per_100k": ("Monthly treatment starts per 100,000 mid-year population", "rate", "Derived"),
        "log_population_offset": ("Natural log of population for count models", "model offset", "Derived"),
        "population": ("Official projected mid-year population", "persons", "BPS"),
        "population_density_per_km2": ("Population density", "persons/km2", "BPS"),
        "sanitation_access_pct": ("Households/population with access to adequate sanitation as reported by BPS table", "percent", "BPS"),
        "poverty_pct": ("Percentage of poor population, March Susenas", "percent", "BPS"),
        "temperature_c": ("Monthly mean 2-metre air temperature", "degrees C", "NASA POWER/MERRA-2"),
        "relative_humidity_pct": ("Monthly mean 2-metre relative humidity", "percent", "NASA POWER/MERRA-2"),
        "precipitation_mm": ("Monthly precipitation total derived from monthly mean mm/day times calendar days", "mm/month", "NASA POWER/MERRA-2"),
        "temperature_c_z": ("Temperature anomaly z-score relative to province calendar-month 1991-2020 normal", "z-score", "Derived"),
        "relative_humidity_pct_z": ("Humidity anomaly z-score relative to province calendar-month 1991-2020 normal", "z-score", "Derived"),
        "precipitation_mm_z": ("Precipitation anomaly z-score relative to province calendar-month 1991-2020 normal", "z-score", "Derived"),
        "heavy_rain_anomaly": ("1 when precipitation anomaly is at least +1 SD", "binary", "Derived"),
        "hot_anomaly": ("1 when temperature anomaly is at least +1 SD", "binary", "Derived"),
        "event_record_count": ("Deduplicated BNPB operational disaster event records", "count", "BNPB operational table"),
        "hydrometeorological_events": ("Flood, landslide, extreme weather, drought, wildfire, and coastal-wave events", "count", "Derived from BNPB"),
        "disaster_quality_flag": ("Warning on disagreement with formal annual BNPB compilation", "quality flag", "Derived QA"),
    }
    rows = []
    for column in columns:
        if column in definitions:
            definition, unit, source = definitions[column]
        elif column.endswith("_lag1"):
            definition, unit, source = (f"One-month lag of {column[:-5]}", "same as base variable", "Derived")
        elif column.endswith("_lag2"):
            definition, unit, source = (f"Two-month lag of {column[:-5]}", "same as base variable", "Derived")
        elif column.endswith("_mean_lag0_2"):
            definition, unit, source = (f"Mean of current and prior two months for {column[:-12]}", "same as base variable", "Derived")
        else:
            definition, unit, source = (column.replace("_", " ").capitalize(), "see source", "Source/derived")
        rows.append({"variable": column, "definition": definition, "unit_or_type": unit, "source": source})
    return pd.DataFrame(rows)


def main() -> None:
    tb = pd.read_csv(CURATED / "tb_treatment_outcomes_province_month_official.csv")
    bps = pd.read_csv(CURATED / "bps_province_annual_official.csv").query("year in [2024, 2025]").copy()
    climate = pd.read_csv(CURATED / "climate_province_month_official.csv")
    disasters = pd.read_csv(CURATED / "bnpb_disaster_province_month_official.csv")

    bps_keep = [
        "province_code", "year", "population", "population_density_per_km2", "population_reference_date",
        "sanitation_access_pct", "sanitation_reference_period", "poverty_pct", "poverty_reference_period",
    ]
    climate_drop = ["province", "period", "source_url", "boundary_source_url"]
    disaster_drop = ["province", "period", "source_url"]

    panel = tb.merge(bps[bps_keep], on=["province_code", "year"], how="left", validate="many_to_one")
    panel = panel.merge(climate.drop(columns=climate_drop), on=["province_code", "year", "month"], how="left", validate="one_to_one")
    disasters = disasters.drop(columns=disaster_drop).rename(columns={"quality_flag": "disaster_quality_flag"})
    panel = panel.merge(disasters, on=["province_code", "year", "month"], how="left", validate="one_to_one")

    panel["known_outcome_count"] = panel.jumlah_pasien - panel.belum_ada_hasil
    panel["pending_share"] = panel.belum_ada_hasil / panel.jumlah_pasien.replace(0, np.nan)
    panel["treatment_success_all_share"] = panel.treatment_success / panel.jumlah_pasien.replace(0, np.nan)
    panel["treatment_success_known_share"] = panel.treatment_success / panel.known_outcome_count.replace(0, np.nan)
    panel["adverse_known_count"] = panel.lost_to_follow_up + panel.meninggal + panel.gagal
    panel["adverse_known_share"] = panel.adverse_known_count / panel.known_outcome_count.replace(0, np.nan)
    panel["cohort_maturity_flag"] = np.where(panel.pending_share <= 0.05, "mature_le_5pct_pending", "provisional_gt_5pct_pending")
    panel["treatment_started_per_100k"] = panel.jumlah_pasien / panel.population * 100_000
    panel["log_population_offset"] = np.log(panel.population)

    preferred = [
        "province_code", "province", "year", "month", "period", "jumlah_pasien", "sembuh",
        "pengobatan_lengkap", "lost_to_follow_up", "meninggal", "gagal", "tidak_dievaluasi_pindah",
        "belum_ada_hasil", "outcome_sum", "outcome_balance", "known_outcome_count", "pending_share", "treatment_success",
        "treatment_success_all_share", "treatment_success_known_share", "adverse_known_count",
        "adverse_known_share", "cohort_maturity_flag", "treatment_started_per_100k", "log_population_offset",
        "population", "population_density_per_km2", "population_reference_date", "sanitation_access_pct",
        "sanitation_reference_period", "poverty_pct", "poverty_reference_period", "temperature_c",
        "relative_humidity_pct", "precipitation_mm", "temperature_c_anomaly", "temperature_c_z",
        "temperature_c_z_lag1", "temperature_c_z_lag2", "temperature_c_z_mean_lag0_2",
        "relative_humidity_pct_anomaly", "relative_humidity_pct_z", "relative_humidity_pct_z_lag1",
        "relative_humidity_pct_z_lag2", "relative_humidity_pct_z_mean_lag0_2", "precipitation_mm_anomaly",
        "precipitation_mm_z", "precipitation_mm_z_lag1", "precipitation_mm_z_lag2",
        "precipitation_mm_z_mean_lag0_2", "heavy_rain_anomaly", "hot_anomaly", "climate_spatial_method",
        "climate_grid_cells", "event_record_count", "hydrometeorological_events", "flood_events",
        "landslide_events", "extreme_weather_events", "drought_events", "wildfire_events",
        "coastal_wave_events", "earthquake_events", "volcanic_eruption_events", "tsunami_events",
        "has_any_impact_field", "deaths_reported_sum", "deaths_reported_records", "injured_reported_sum",
        "injured_reported_records", "houses_damaged_reported_sum", "houses_damaged_reported_records",
        "houses_flooded_reported_sum", "houses_flooded_reported_records", "disaster_quality_flag",
        "quality_flag", "source_url", "snapshot_retrieved_at",
    ]
    panel = panel[preferred].sort_values(["province_code", "year", "month"])

    output = CURATED / "analysis_panel_tb_climate_disaster_2024_2025.csv"
    panel.to_csv(output, index=False)
    ledger = source_ledger()
    ledger.to_csv(CURATED / "project_source_ledger.csv", index=False)
    codebook = build_codebook(panel.columns.tolist())
    codebook.to_csv(CURATED / "analysis_panel_tb_climate_codebook.csv", index=False)

    required = [
        "jumlah_pasien", "population", "population_density_per_km2", "sanitation_access_pct", "poverty_pct",
        "temperature_c", "relative_humidity_pct", "precipitation_mm", "temperature_c_z",
        "relative_humidity_pct_z", "precipitation_mm_z", "event_record_count",
    ]
    validation = {
        "rows": int(len(panel)),
        "provinces": int(panel.province_code.nunique()),
        "periods": int(panel[["year", "month"]].drop_duplicates().shape[0]),
        "duplicate_keys": int(panel.duplicated(["province_code", "year", "month"]).sum()),
        "required_missing": {c: int(panel[c].isna().sum()) for c in required},
        "all_required_complete": bool(panel[required].notna().all().all()),
        "outcome_balance_failures": int((panel.outcome_balance != 0).sum()),
        "pending_share_by_year": panel.groupby("year").pending_share.mean().round(4).to_dict(),
        "mature_cohorts_by_year": panel.groupby("year").cohort_maturity_flag.apply(lambda s: int((s == "mature_le_5pct_pending").sum())).to_dict(),
        "climate_spatial_methods": panel.groupby("climate_spatial_method").size().to_dict(),
        "disaster_warning": "BNPB monthly operational counts are sensitivity covariates due to incomplete agreement with annual workbooks.",
    }
    (CURATED / "analysis_panel_tb_climate_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
