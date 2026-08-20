# Official data source ledger

Analysis-ready project panel: `processed/analysis_panel_tb_climate_disaster_2024_2025.csv`  
Machine-readable source ledger: `processed/project_source_ledger.csv`  
Codebook: `processed/analysis_panel_tb_climate_codebook.csv`

Downloaded on: 2026-08-12 (Asia/Jakarta)

## WHO Global Tuberculosis Programme

The files in `raw/who/` were downloaded without modification from the WHO Global TB Programme download endpoints:

| Local file | Official endpoint | Geographic level | Notes |
|---|---|---|---|
| `who_estimates.csv` | https://extranet.who.int/tme/generateCSV.asp?ds=estimates | country-year | Modelled burden estimates; not the same as notified cases |
| `who_notifications.csv` | https://extranet.who.int/tme/generateCSV.asp?ds=notifications | country-year | Case notifications and disaggregations |
| `who_outcomes.csv` | https://extranet.who.int/tme/generateCSV.asp?ds=outcomes | country-year/cohort | Treatment outcomes |
| `who_provisional.csv` | https://extranet.who.int/tme/generateCSV.asp?ds=provisional_notifications | country-month/quarter | Provisional and subject to revision |
| `who_dictionary.csv` | https://extranet.who.int/tme/generateCSV.asp?ds=dictionary | metadata | Variable definitions |

Landing page: https://www.who.int/teams/global-tuberculosis-programme/data

These global extracts are retained as immutable raw inputs. Filter `country == "Indonesia"` in staging code rather than editing the raw files.

## Kementerian Kesehatan / SITB

| Local output | Source | Geographic/time level | QA status |
|---|---|---|---|
| `processed/tb_national_month_official.csv` | SATUSEHAT Data Dashboard “Pemantauan Kasus Tuberkulosis” (SITB) | national-month, Jan 2023–Jun 2026 | 16 official crosstabs; 4 indicators; no failed files |
| `processed/tb_province_annual_official.csv` | `raw/kemenkes/Profil_Kesehatan_Indonesia_2024.pdf`, Lampiran 56.a | 38 provinces, 2024 | 38/38 rows; sex sums checked; total = 856,420 |
| `processed/tb_treatment_outcomes_province_month_official.csv` | public SITB TB Dashboard exports | 38 provinces x 12 months, treatment cohorts starting in 2024 and 2025 | 912 rows; all seven outcome categories reconcile exactly to patient totals |
| `processed/tb_province_month_sitb_official.csv` | long form of the same public SITB exports | province-month-indicator, 2024-2025 | 7,296 rows; 8 indicators; no imputation |
| `processed/analysis_panel_province_month_2024_2025.csv` | SITB province-month joined to same-year BPS covariates | province-month, 2024-2025 | 912/912 rows matched to population; BPS variables remain annual |

Dashboard: https://satusehat.kemkes.go.id/data/dashboard/5acb4fb6-af4a-48ac-abf5-3c255cfb5a26

The SATUSEHAT Tableau workbook still exposes only valid national monthly series because its geographic fields are blank. A second official public source, `https://tbdashboard.sitb.id/`, exposes province-month treatment cohorts for 2024 and 2025. Those exports contain patients starting drug-susceptible TB treatment and their outcomes; they are **not** interchangeable with notification or incidence series. The dashboard is live, so snapshots may be revised.

One September 2024 row carried province ID 37 but the label `Papua`; every other occurrence of ID 37, including all 2025 rows, is `Papua Pegunungan`. The processed data resolves the label by the stable source ID, retains the raw label, and marks the corrected row. Counts are unchanged.

## Badan Pusat Statistik

`processed/bps_province_annual_official.csv` contains 38-province annual/reference-period covariates extracted from the official PDFs in `raw/bps/`:

- projected mid-year population and population density, 2023–2026;
- access to adequate sanitation, Susenas 2023–2025;
- poverty rate, Susenas March 2024 and March 2025.

Population may be joined to all TB months within its reference year as an annual denominator, but it is not a monthly observation. Poverty and sanitation are not interpolated. See `processed/bps_province_validation.json` for row counts and national-total checks.

## Reproducible preparation

1. `node scripts/extract_satusehat_tb.cjs`
2. `python scripts/prepare_national_province_data.py`
3. `python scripts/prepare_kemenkes_province_annual.py`
4. `python scripts/prepare_bps_province_covariates.py`
5. `python scripts/prepare_sitb_province_month.py`

Raw PDF and CSV files are retained unchanged; processed outputs include publisher, source file/table, reference period, and extraction method fields.

## NASA POWER and Badan Informasi Geospasial

`processed/climate_province_month_official.csv` contains complete monthly temperature,
relative humidity, and precipitation for 38 provinces in 2024-2025. It also contains
month-specific 1991-2020 normals, anomalies, z-scores, one- and two-month lags, and
three-month means. The raw NASA POWER NetCDF tiles cover 1981-2025 and are retained
under `raw/nasa_power/`.

NASA POWER monthly API: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/

Climate grid cells were assigned to province polygons from BIG layer 12:
https://geoservices.big.go.id/rbi/rest/services/BATASWILAYAH/BATAS_WILAYAH/MapServer/12

The BIG export was generalized for climate-grid aggregation and topology-repaired.
It must not be used as a legal boundary product. Current province codes were harmonized
by province name because the service snapshot carries older Papua codes.

## BNPB

The dated operational event table was extracted for 2024-01-01 through 2025-12-31.
Of 7,164 raw rows, 21 exact substantive duplicates were removed, leaving 7,143 event
records. `processed/bnpb_disaster_province_month_official.csv` is a complete 38-province
x 24-month panel, including explicit zeros when no event was found.

The operational monthly counts do not fully reconcile with the formal annual BNPB
workbooks. See `processed/bnpb_disaster_annual_reconciliation.csv`. Therefore disaster
counts are secondary/sensitivity covariates, not the primary exposure.

Operational table: https://gis.bnpb.go.id/databencana/tabel/pencarian.php

## Rebuild order for the final project panel

1. `python scripts/prepare_bps_province_covariates.py`
2. `python scripts/prepare_sitb_province_month.py`
3. `python scripts/prepare_climate_province_month.py`
4. `python scripts/prepare_bnpb_province_month.py`
5. `python scripts/build_tb_climate_project_panel.py`
6. `python scripts/run_preliminary_tb_climate_models.py`

