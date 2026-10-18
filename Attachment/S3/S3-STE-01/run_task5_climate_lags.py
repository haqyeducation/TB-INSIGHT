"""
TB-INSIGHT — Task 5: PPML Climate Lag Models
=============================================

Runs all pre-specified single-family lag models from the analysis plan.

Lag structure available in the panel:
  Lag 0   : temperature_c_z, precipitation_mm_z, relative_humidity_pct_z
  Lag 1   : temperature_c_z_lag1, precipitation_mm_z_lag1, relative_humidity_pct_z_lag1
  Lag 2   : temperature_c_z_lag2, precipitation_mm_z_lag2, relative_humidity_pct_z_lag2
  Lag 0-2 : temperature_c_z_mean_lag0_2 etc. (already primary in Task 3)

NOT available (documented as skipped):
  Lag 3 and Lag 0-3 mean — not in analysis panel (S5/S6 from plan)

Model structure for each:
  - One climate family at a time (temperature / precipitation / humidity)
  - PPML (Poisson GLM, log link)
  - Offset: log_population_offset
  - FE: C(province_code) + C(period)
  - SE: cluster-robust by province_code

Output: results/models/climate_lags/
  ├── temperature/
  │   ├── lag0/
  │   ├── lag1/
  │   └── lag2/
  ├── precipitation/
  │   ├── lag0/
  │   ├── lag1/
  │   └── lag2/
  ├── humidity/
  │   ├── lag0/
  │   ├── lag1/
  │   └── lag2/
  ├── coefficients_all_lags.csv   <- cross-model summary
  ├── selection_rule.md           <- documented selection rule
  ├── skipped_models.csv          <- lag3 / lag0-3 not available
  └── metadata.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PANEL = (
    Path(r"D:\Airlangga Boy\BSO\IRIS\long-term project\task\data_processed")
    / "analysis_panel_tb_climate_disaster_2024_2025.csv"
)
OUTPUT_ROOT = (
    Path(r"D:\Airlangga Boy\BSO\IRIS\long-term project\task\[5]")
    / "results" / "models" / "climate_lags"
)

# ---------------------------------------------------------------------------
# Shared spec
# ---------------------------------------------------------------------------
OUTCOME      = "jumlah_pasien"
PROVINCE_FE  = "province_code"
PERIOD_FE    = "period"
OFFSET       = "log_population_offset"
CLUSTER      = "province_code"

# Climate families and their lag columns
# format: (family_name, lag_label, column_name)
LAG_SPECS = [
    # Temperature
    ("temperature", "lag0",   "temperature_c_z"),
    ("temperature", "lag1",   "temperature_c_z_lag1"),
    ("temperature", "lag2",   "temperature_c_z_lag2"),
    # Precipitation
    ("precipitation", "lag0", "precipitation_mm_z"),
    ("precipitation", "lag1", "precipitation_mm_z_lag1"),
    ("precipitation", "lag2", "precipitation_mm_z_lag2"),
    # Humidity
    ("humidity", "lag0",      "relative_humidity_pct_z"),
    ("humidity", "lag1",      "relative_humidity_pct_z_lag1"),
    ("humidity", "lag2",      "relative_humidity_pct_z_lag2"),
]

# Models that cannot be run because the variables don't exist in the panel
SKIPPED_SPECS = [
    {
        "family": "temperature",
        "lag": "lag3",
        "variable": "temperature_c_z_lag3",
        "reason": "Variable not present in analysis panel",
        "plan_reference": "S5 (individual lag 3)",
    },
    {
        "family": "precipitation",
        "lag": "lag3",
        "variable": "precipitation_mm_z_lag3",
        "reason": "Variable not present in analysis panel",
        "plan_reference": "S5 (individual lag 3)",
    },
    {
        "family": "humidity",
        "lag": "lag3",
        "variable": "relative_humidity_pct_z_lag3",
        "reason": "Variable not present in analysis panel",
        "plan_reference": "S5 (individual lag 3)",
    },
    {
        "family": "all",
        "lag": "lag0_3_mean",
        "variable": "temperature/precipitation/humidity_c_z_mean_lag0_3",
        "reason": "Lag-3 variables not present; mean requires all four months",
        "plan_reference": "S6 (alternative 0-3 month window)",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_formula(exposure_col: str) -> str:
    return (
        f"{OUTCOME} ~ {exposure_col}"
        f" + C({PROVINCE_FE}) + C({PERIOD_FE})"
    )


def fit_ppml(data: pd.DataFrame, formula: str):
    return smf.glm(
        formula=formula,
        data=data,
        family=sm.families.Poisson(),
        offset=data[OFFSET],
    ).fit(
        cov_type="cluster",
        cov_kwds={"groups": data[CLUSTER]},
    )


def extract_coef(fit, var: str) -> dict:
    beta = fit.params[var]
    se   = fit.bse[var]
    return {
        "variable":             var,
        "coefficient_log_rate": beta,
        "cluster_robust_se":    se,
        "incidence_rate_ratio": np.exp(beta),
        "irr_ci95_low":         np.exp(beta - 1.96 * se),
        "irr_ci95_high":        np.exp(beta + 1.96 * se),
        "p_value":              fit.pvalues[var],
    }


def extract_diagnostics(fit, data: pd.DataFrame) -> dict:
    return {
        "n_observations":       int(fit.nobs),
        "n_provinces":          int(data[PROVINCE_FE].nunique()),
        "n_periods":            int(data[PERIOD_FE].nunique()),
        "outcome":              OUTCOME,
        "model_family":         "Poisson",
        "link_function":        "log",
        "offset":               OFFSET,
        "province_fixed_effects": True,
        "period_fixed_effects": True,
        "cluster_variable":     CLUSTER,
        "converged":            bool(getattr(fit, "converged", None)),
        "iterations":           getattr(fit, "fit_history", {}).get("iteration", None),
        "log_likelihood":       fit.llf,
        "deviance":             fit.deviance,
        "pearson_chi2":         fit.pearson_chi2,
        "aic":                  fit.aic,
    }


def write_model_files(
    out: Path,
    model_id: str,
    family: str,
    lag: str,
    formula: str,
    coef: dict,
    diag: dict,
    run_ts: str,
) -> None:
    out.mkdir(parents=True, exist_ok=True)

    # coefficients.csv
    pd.DataFrame([coef]).to_csv(out / "coefficients.csv", index=False)

    # diagnostics.csv
    pd.DataFrame([diag]).to_csv(out / "diagnostics.csv", index=False)

    # metadata.json
    meta = {
        "model_id":              model_id,
        "task":                  "task5_climate_lags",
        "analysis_plan_version": "1.0",
        "climate_family":        family,
        "lag":                   lag,
        "role":                  "pre-specified lag sensitivity",
        "outcome":               OUTCOME,
        "exposure":              coef["variable"],
        "formula":               formula,
        "offset":                OFFSET,
        "fixed_effects":         [PROVINCE_FE, PERIOD_FE],
        "standard_errors":       "cluster-robust by province",
        "n_observations":        diag["n_observations"],
        "converged":             diag["converged"],
        "run_timestamp_utc":     run_ts,
    }
    with open(out / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # model_summary.txt
    with open(out / "model_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"TB-INSIGHT -- Climate Lag Model\n")
        f.write(f"Model ID : {model_id}\n")
        f.write(f"Family   : {family}\n")
        f.write(f"Lag      : {lag}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Formula  : {formula}\n")
        f.write(f"Offset   : {OFFSET}\n")
        f.write("SE       : cluster-robust by province_code\n\n")
        f.write("Diagnostics:\n")
        f.write(pd.DataFrame([diag]).to_string(index=False))
        f.write("\n\nExposure estimate:\n")
        f.write(pd.DataFrame([coef]).to_string(index=False))
        f.write("\n")


def write_selection_rule(out: Path) -> None:
    lines = [
        "# TB-INSIGHT — Task 5: Lag Model Selection Rule",
        "",
        "## Purpose",
        "",
        "This document records the pre-specified selection rule for lag model",
        "interpretation. No lag specification may be promoted as the primary result",
        "based on statistical significance.",
        "",
        "## Selection rule",
        "",
        "1. All pre-specified lag models (Lag 0, Lag 1, Lag 2 for each family) are",
        "   estimated and reported without omission.",
        "2. Results are presented in full for all lags; no lag is suppressed because",
        "   its p-value is unfavorable.",
        "3. The primary exposure window remains Lag 0-2 mean (Task 3).",
        "   Individual lag models are sensitivity analyses.",
        "4. A lag specification may not be selected as 'the' result because it yields",
        "   a smaller p-value or larger IRR than other lags.",
        "5. Pattern commentary (e.g. 'IRR is slightly larger at Lag 1') is descriptive",
        "   only and does not constitute a change to the primary specification.",
        "",
        "## Lag 3 and Lag 0-3 mean: not run",
        "",
        "Variables for Lag 3 (`*_lag3`) and the Lag 0-3 mean are not present in the",
        "frozen analysis panel. These correspond to analysis-plan sections S5 and S6.",
        "They are documented in `skipped_models.csv` and cannot be estimated from the",
        "current panel version. If a revised panel is produced with Lag 3 variables,",
        "these models should be added as an amendment.",
        "",
        "## Multiple testing",
        "",
        "Nine lag models are estimated (3 families x 3 lags). P-values are not adjusted",
        "for multiplicity. These are sensitivity analyses; none is confirmatory.",
        "Cross-lag comparison should not be used to identify a 'best' lag window.",
    ]
    with open(out / "selection_rule.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    run_ts = datetime.now(timezone.utc).isoformat()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(PANEL, dtype={PROVINCE_FE: str})
    print(f"Panel: {len(data)} rows, {data[PROVINCE_FE].nunique()} provinces, "
          f"{data[PERIOD_FE].nunique()} periods")

    # Validate all needed columns exist
    all_needed = [OUTCOME, OFFSET, PROVINCE_FE, PERIOD_FE] + [s[2] for s in LAG_SPECS]
    missing = [c for c in all_needed if c not in data.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    all_rows: list[dict] = []

    for family, lag, var_col in LAG_SPECS:
        model_id = f"{family}_{lag}"
        out_dir  = OUTPUT_ROOT / family / lag
        formula  = build_formula(var_col)

        print(f"\n  Running: {model_id}  ({var_col})")
        fit  = fit_ppml(data, formula)
        coef = extract_coef(fit, var_col)
        diag = extract_diagnostics(fit, data)

        write_model_files(out_dir, model_id, family, lag, formula, coef, diag, run_ts)

        converged = diag["converged"]
        print(f"    converged={converged}, IRR={coef['incidence_rate_ratio']:.4f}, "
              f"p={coef['p_value']:.4f}, AIC={diag['aic']:.2f}")

        all_rows.append({
            "model_id":              model_id,
            "climate_family":        family,
            "lag":                   lag,
            "role":                  "sensitivity",
            "variable":              var_col,
            "coefficient_log_rate":  coef["coefficient_log_rate"],
            "cluster_robust_se":     coef["cluster_robust_se"],
            "incidence_rate_ratio":  coef["incidence_rate_ratio"],
            "irr_ci95_low":          coef["irr_ci95_low"],
            "irr_ci95_high":         coef["irr_ci95_high"],
            "p_value":               coef["p_value"],
            "significant_0.05":      coef["p_value"] < 0.05,
            "n_observations":        diag["n_observations"],
            "converged":             converged,
            "aic":                   diag["aic"],
        })

    # Cross-model summary
    summary_df = pd.DataFrame(all_rows)
    summary_df.to_csv(OUTPUT_ROOT / "coefficients_all_lags.csv", index=False)

    # Skipped models
    pd.DataFrame(SKIPPED_SPECS).to_csv(OUTPUT_ROOT / "skipped_models.csv", index=False)

    # Selection rule
    write_selection_rule(OUTPUT_ROOT)

    # Top-level metadata
    meta = {
        "task":                  "task5_climate_lags",
        "analysis_plan_version": "1.0",
        "run_timestamp_utc":     run_ts,
        "models_run":            [f"{f}_{l}" for f, l, _ in LAG_SPECS],
        "models_skipped":        [s["family"] + "_" + s["lag"] for s in SKIPPED_SPECS],
        "skip_reason":           "Lag-3 variables absent from frozen analysis panel",
        "outcome":               OUTCOME,
        "offset":                OFFSET,
        "fixed_effects":         [PROVINCE_FE, PERIOD_FE],
        "standard_errors":       "cluster-robust by province",
        "multiplicity_note":     (
            "9 models estimated (3 families x 3 lags). "
            "P-values are not adjusted for multiplicity. "
            "These are pre-specified sensitivity analyses."
        ),
    }
    with open(OUTPUT_ROOT / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\n" + "=" * 60)
    print("Task 5 Complete")
    print("=" * 60)
    print(f"  Models run    : {len(LAG_SPECS)}")
    print(f"  Models skipped: {len(SKIPPED_SPECS)} (documented in skipped_models.csv)")
    print(f"  Output        : {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
