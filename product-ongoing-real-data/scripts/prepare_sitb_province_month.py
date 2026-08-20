"""Curate official SITB province-month treatment cohorts from the public TB dashboard."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "sitb_dashboard"
CURATED_DIR = ROOT / "data" / "processed"

RAW_FILES = {
    2024: "tb_treatment_outcomes_province_month_2024_raw.csv",
    2025: "tb_treatment_outcomes_province_month_2025_raw.csv",
}

INDICATORS = {
    "jumlah_pasien": "treatment_started",
    "sembuh": "cured",
    "pengobatan_lengkap": "treatment_completed",
    "lost_to_follow_up": "lost_to_follow_up",
    "meninggal": "died",
    "gagal": "failed",
    "tidak_dievaluasi_pindah": "not_evaluated_or_transferred",
    "belum_ada_hasil": "outcome_pending",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    province_reference = pd.read_csv(
        CURATED_DIR / "tb_province_annual_official.csv",
        dtype={"province_code": str},
    )[["province_code", "province"]].drop_duplicates()
    code_by_name = dict(zip(province_reference["province"].str.upper(), province_reference["province_code"].str.zfill(2)))

    frames = []
    raw_manifest = []
    for year, filename in RAW_FILES.items():
        path = RAW_DIR / filename
        raw = pd.read_csv(path)
        raw["year"] = year
        raw["source_file"] = filename
        raw["source_url"] = (
            f"https://tbdashboard.sitb.id/"
            f"ss_data_tbc03so_{year}_provinsi_bulanan_list.php"
        )
        frames.append(raw)
        raw_manifest.append({
            "year": year,
            "file": filename,
            "rows": int(len(raw)),
            "sha256": sha256(path),
            "source_url": raw["source_url"].iat[0],
        })

    wide = pd.concat(frames, ignore_index=True)
    numeric_columns = ["bulan", "fasyankes_provinsi_id", *INDICATORS]
    wide[numeric_columns] = wide[numeric_columns].apply(pd.to_numeric, errors="raise")
    wide["source_province_name_raw"] = wide["fasyankes_provinsi_nama"].str.strip()
    canonical_name_by_id = (
        wide.groupby("fasyankes_provinsi_id")["source_province_name_raw"]
        .agg(lambda values: values.mode().iat[0])
        .to_dict()
    )
    wide["province"] = wide["fasyankes_provinsi_id"].map(canonical_name_by_id).str.upper().replace({
        "KEPULAUAN BANGKA BELITUNG": "KEP. BANGKA BELITUNG",
    })
    wide["province_name_corrected"] = (
        wide["source_province_name_raw"].str.upper().replace({
            "KEPULAUAN BANGKA BELITUNG": "KEP. BANGKA BELITUNG",
        }) != wide["province"]
    )
    wide["province_code"] = wide["province"].map(code_by_name)
    if wide["province_code"].isna().any():
        missing = sorted(wide.loc[wide["province_code"].isna(), "province"].unique())
        raise ValueError(f"Province names not mapped to BPS codes: {missing}")

    if wide.duplicated(["year", "bulan", "province_code"]).any():
        raise ValueError("Duplicate province-month rows detected")
    if set(wide["bulan"]) != set(range(1, 13)):
        raise ValueError("Month coverage is not 1-12")
    if (wide[list(INDICATORS)] < 0).any().any():
        raise ValueError("Negative count detected")

    coverage = wide.groupby(["year", "bulan"])["province_code"].nunique()
    if not coverage.eq(38).all():
        raise ValueError(f"Incomplete province coverage: {coverage[coverage.ne(38)].to_dict()}")

    outcome_columns = [
        "sembuh", "pengobatan_lengkap", "lost_to_follow_up", "meninggal",
        "gagal", "tidak_dievaluasi_pindah", "belum_ada_hasil",
    ]
    wide["outcome_sum"] = wide[outcome_columns].sum(axis=1)
    wide["outcome_balance"] = wide["jumlah_pasien"] - wide["outcome_sum"]
    wide["treatment_success"] = wide["sembuh"] + wide["pengobatan_lengkap"]
    wide["treatment_success_rate_pct"] = (
        wide["treatment_success"] / wide["jumlah_pasien"].where(wide["jumlah_pasien"].ne(0)) * 100
    ).round(4)
    wide["month"] = wide["bulan"]
    wide["period"] = pd.to_datetime(
        dict(year=wide["year"], month=wide["month"], day=1)
    ).dt.to_period("M").astype(str)
    wide["unit"] = "persons"
    wide["source_system"] = "SITB public TB dashboard"
    wide["source_publisher"] = "Kementerian Kesehatan RI"
    wide["cohort_definition"] = "Patients starting drug-susceptible TB treatment in the stated month"
    wide["snapshot_retrieved_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    wide["quality_flag"] = "official_live_dashboard_snapshot_subject_to_revision"

    wide_columns = [
        "province_code", "fasyankes_provinsi_id", "province", "source_province_name_raw",
        "province_name_corrected", "year", "month", "period",
        *INDICATORS.keys(), "outcome_sum", "outcome_balance", "treatment_success",
        "treatment_success_rate_pct", "unit", "cohort_definition", "source_system",
        "source_publisher", "source_file", "source_url", "snapshot_retrieved_at", "quality_flag",
    ]
    wide = wide[wide_columns].rename(columns={"fasyankes_provinsi_id": "source_province_id"})

    id_columns = [
        "province_code", "source_province_id", "province", "source_province_name_raw",
        "province_name_corrected", "year", "month", "period",
        "unit", "cohort_definition", "source_system", "source_publisher", "source_file",
        "source_url", "snapshot_retrieved_at", "quality_flag",
    ]
    long = wide.melt(
        id_vars=id_columns,
        value_vars=list(INDICATORS),
        var_name="source_indicator",
        value_name="value",
    )
    long["indicator"] = long["source_indicator"].map(INDICATORS)
    long = long[[
        "province_code", "source_province_id", "province", "source_province_name_raw",
        "province_name_corrected", "year", "month", "period",
        "indicator", "source_indicator", "value", "unit", "cohort_definition",
        "source_system", "source_publisher", "source_file", "source_url",
        "snapshot_retrieved_at", "quality_flag",
    ]].sort_values(["year", "month", "province_code", "indicator"])

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    wide.to_csv(
        CURATED_DIR / "tb_treatment_outcomes_province_month_official.csv",
        index=False,
        quoting=csv.QUOTE_MINIMAL,
    )
    long.to_csv(
        CURATED_DIR / "tb_province_month_sitb_official.csv",
        index=False,
        quoting=csv.QUOTE_MINIMAL,
    )

    bps = pd.read_csv(
        CURATED_DIR / "bps_province_annual_official.csv",
        dtype={"province_code": str},
    )
    bps["province_code"] = bps["province_code"].str.zfill(2)
    bps_columns = [
        "province_code", "year", "population", "population_density_per_km2",
        "population_reference_date", "sanitation_access_pct", "sanitation_reference_period",
        "poverty_pct", "poverty_reference_period",
    ]
    analysis_panel = wide.merge(
        bps[bps["year"].isin(RAW_FILES)][bps_columns],
        on=["province_code", "year"],
        how="left",
        validate="many_to_one",
    )
    analysis_panel["treatment_started_per_100k_population"] = (
        analysis_panel["jumlah_pasien"] / analysis_panel["population"] * 100_000
    ).round(4)
    analysis_panel.to_csv(
        CURATED_DIR / "analysis_panel_province_month_2024_2025.csv",
        index=False,
        quoting=csv.QUOTE_MINIMAL,
    )

    validation = {
        "source": "Kementerian Kesehatan RI SITB public TB dashboard",
        "raw_files": raw_manifest,
        "years": sorted(wide["year"].unique().tolist()),
        "months_per_year": wide.groupby("year")["month"].nunique().astype(int).to_dict(),
        "provinces_per_year": wide.groupby("year")["province_code"].nunique().astype(int).to_dict(),
        "wide_rows": int(len(wide)),
        "long_rows": int(len(long)),
        "analysis_panel_rows": int(len(analysis_panel)),
        "analysis_panel_population_matched_rows": int(analysis_panel["population"].notna().sum()),
        "indicators": sorted(long["indicator"].unique().tolist()),
        "duplicate_province_month_rows": int(wide.duplicated(["year", "month", "province_code"]).sum()),
        "negative_values": int((long["value"] < 0).sum()),
        "outcome_balance_nonzero_rows": int(wide["outcome_balance"].ne(0).sum()),
        "outcome_balance_min": int(wide["outcome_balance"].min()),
        "outcome_balance_max": int(wide["outcome_balance"].max()),
        "province_name_corrected_rows": int(wide["province_name_corrected"].sum()),
        "province_name_correction_note": "One 2024 source row for province ID 37 was labelled Papua; canonical ID mapping resolves it to Papua Pegunungan without changing counts.",
        "no_imputation": True,
        "revision_warning": "Live dashboard snapshot; treatment outcomes can be revised after extraction.",
    }
    (CURATED_DIR / "tb_province_month_validation.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(validation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
