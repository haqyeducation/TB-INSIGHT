# S3 canonical rebuild

**Status:** implemented and verified on 17 October 2026. The submitted files in
`Attachment/S3/` remain an immutable review archive; the files under this
product directory are the canonical corrected outputs.

## What changed

- BPS poverty extraction now stops at province-row boundaries and handles
  missing urban/rural placeholders. All 76 province-year values for 2024–2025
  are present and within 3.72–32.97 percent.
- NASA POWER climate features were regenerated with lag 0–3. The frozen feature
  matrix has 912 unique rows, no missing cells, and discloses one retained
  extreme climatological z-score (Aceh precipitation, November 2025, z=5.29).
- BIG boundaries were dissolved and repaired to 38 valid province geometries.
  Primary weights contain 38 queen edges and 11 explicitly labelled shortest-
  component bridges; the resulting graph is connected. A KNN-3 alternative is
  included for sensitivity analysis.
- Twelve lag PPML models and nine climate × social interaction PPML models were
  rerun from relative project paths. Poverty interactions now use corrected BPS
  values. Results remain exploratory because lag and interaction p-values are
  not multiplicity-adjusted.
- Monthly LISA was rerun for 912 province-months with 999 permutations and
  within-month FDR. It produces 87 raw significant classifications and one FDR
  significant classification; both versions remain in the output.
- The frontend now implements Erin's six-page information architecture:
  Ringkasan, Tren, Peta, Provinsi, Metode, and Sumber. Shared filters are encoded
  in the URL, and the map uses the canonical BIG GeoJSON and current LISA output.

## Canonical outputs

| Area | Location |
| --- | --- |
| Analysis panel | `data/processed/analysis_panel_tb_climate_disaster_2024_2025.csv` |
| Climate feature matrix | `data/processed/features/climate_lags_v2.csv` |
| BPS annual covariates | `data/processed/bps_province_annual_official.csv` |
| Boundary and weights | `data/processed/spatial/` |
| Lag models | `results/models/climate_lags/` |
| Interaction models | `results/models/social_interactions/` |
| LISA and maps | `results/spatial/` |
| Frontend | `frontend/src/` |

## Reproduction order

```powershell
python scripts/prepare_bps_province_covariates.py
python scripts/prepare_climate_province_month.py
python scripts/build_climate_feature_matrix.py
python scripts/build_tb_climate_project_panel.py
python scripts/build_spatial_assets.py
python scripts/run_s3_models.py
python scripts/run_s3_spatial.py
python -m pytest tests -q
cd frontend
pnpm install --frozen-lockfile=false
pnpm run build
pnpm run lint
```

## Interpretation guardrails

The outcome is TB treatment initiation, not incidence. The observation window
is only two years; findings should be described as ecological associations and
short-window spatiotemporal patterns, not long-term climate causation. The 2025
treatment outcomes are provisional. BNPB event counts are a sensitivity layer.

