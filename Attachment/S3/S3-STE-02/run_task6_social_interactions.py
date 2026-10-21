"""
TB-INSIGHT — Task 6: Social Vulnerability Interactions
======================================================

Tests climate x social-vulnerability interactions one at a time.
No kitchen-sink model. Each interaction tested separately.

Design:
  - One primary climate exposure (lag 0-2 mean) x one vulnerability variable
  - 9 models: 3 climate families x 3 vulnerability variables
  - Each model includes: climate main effect + vulnerability main effect
    + climate:vulnerability interaction + province FE + period FE + offset
  - Vulnerability variables are standardized (mean=0, sd=1) within the script
    to make interaction coefficients interpretable on a common scale
  - Marginal contrasts computed at low / median / high vulnerability (p10/p50/p90)

Vulnerability variables (from BPS via codebook):
  - poverty_pct            (% poor population)
  - population_density_per_km2
  - sanitation_access_pct  (% with adequate sanitation)

Climate exposures (lag 0-2 mean, standardized z-scores):
  - temperature_c_z_mean_lag0_2
  - precipitation_mm_z_mean_lag0_2
  - relative_humidity_pct_z_mean_lag0_2

Output: results/models/social_interactions/
  ├── temperature_x_poverty/
  ├── temperature_x_density/
  ├── temperature_x_sanitation/
  ├── precipitation_x_poverty/
  ├── ...  (9 subfolders total)
  ├── coefficients_all_interactions.csv
  ├── marginal_contrasts.csv
  ├── multiplicity_note.md
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
    Path(r"D:\Airlangga Boy\BSO\IRIS\long-term project\task\[6]")
    / "results" / "models" / "social_interactions"
)

# ---------------------------------------------------------------------------
# Shared spec
# ---------------------------------------------------------------------------
OUTCOME     = "jumlah_pasien"
PROVINCE_FE = "province_code"
PERIOD_FE   = "period"
OFFSET      = "log_population_offset"
CLUSTER     = "province_code"

CLIMATE_EXPOSURES = [
    ("temperature",   "temperature_c_z_mean_lag0_2"),
    ("precipitation", "precipitation_mm_z_mean_lag0_2"),
    ("humidity",      "relative_humidity_pct_z_mean_lag0_2"),
]

VULNERABILITY_VARS = [
    ("poverty",     "poverty_pct"),
    ("density",     "population_density_per_km2"),
    ("sanitation",  "sanitation_access_pct"),
]

# Marginal contrast points (percentiles of vulnerability distribution)
CONTRAST_PERCENTILES = [10, 50, 90]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def standardize(series: pd.Series) -> tuple[pd.Series, float, float]:
    """Standardize series; return (z, mean, sd)."""
    mu = series.mean()
    sd = series.std(ddof=1)
    return (series - mu) / sd, mu, sd


def build_formula(climate_col: str, vuln_col_z: str) -> str:
    """
    Main effects + interaction.
    Both climate_col and vuln_col_z are already standardized.
    """
    return (
        f"{OUTCOME} ~ {climate_col} + {vuln_col_z}"
        f" + {climate_col}:{vuln_col_z}"
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


def extract_interaction_coefs(
    fit,
    climate_col: str,
    vuln_col_z: str,
) -> list[dict]:
    """Extract main effects + interaction coefficient."""
    rows = []
    # Climate main effect
    for term in [climate_col, vuln_col_z, f"{climate_col}:{vuln_col_z}"]:
        # statsmodels may reorder; try both orderings for interaction
        candidates = [term, f"{vuln_col_z}:{climate_col}"]
        matched = None
        for c in candidates:
            if c in fit.params.index:
                matched = c
                break
        if matched is None:
            # try partial match
            for idx in fit.params.index:
                if climate_col in idx and vuln_col_z in idx and ":" in idx:
                    matched = idx
                    break
        if matched is None:
            continue
        beta = fit.params[matched]
        se   = fit.bse[matched]
        rows.append({
            "term":                 term,
            "matched_param":        matched,
            "coefficient_log_rate": beta,
            "cluster_robust_se":    se,
            "incidence_rate_ratio": np.exp(beta),
            "irr_ci95_low":         np.exp(beta - 1.96 * se),
            "irr_ci95_high":        np.exp(beta + 1.96 * se),
            "p_value":              fit.pvalues[matched],
        })
    return rows


def compute_marginal_contrasts(
    fit,
    climate_col: str,
    vuln_col_z: str,
    vuln_series_z: pd.Series,
) -> list[dict]:
    """
    Compute the marginal association of a +1 SD climate change at
    low / median / high vulnerability (p10 / p50 / p90 of standardized vuln).

    For a Poisson log-linear model:
      log mu = ... + beta_c * C + beta_v * V + beta_cv * C*V
    The marginal effect of C at a given V=v is:
      beta_c + beta_cv * v
    The IRR at V=v for a +1 unit change in C is:
      exp(beta_c + beta_cv * v)
    """
    # Get coefficients
    beta_c = fit.params.get(climate_col, np.nan)

    # Interaction term (either ordering)
    beta_cv = np.nan
    for idx in fit.params.index:
        if climate_col in idx and vuln_col_z in idx and ":" in idx:
            beta_cv = fit.params[idx]
            break

    se_c  = fit.bse.get(climate_col, np.nan)
    se_cv = np.nan
    cov_c_cv = np.nan
    for idx in fit.bse.index:
        if climate_col in idx and vuln_col_z in idx and ":" in idx:
            se_cv = fit.bse[idx]
            break

    # Try to get cov(beta_c, beta_cv) for delta-method SE
    try:
        cov_matrix = fit.cov_params()
        int_idx = None
        for idx in cov_matrix.index:
            if climate_col in idx and vuln_col_z in idx and ":" in idx:
                int_idx = idx
                break
        if int_idx and climate_col in cov_matrix.index:
            cov_c_cv = cov_matrix.loc[climate_col, int_idx]
        else:
            cov_c_cv = 0.0
    except Exception:
        cov_c_cv = 0.0

    rows = []
    for pct in CONTRAST_PERCENTILES:
        v = float(np.percentile(vuln_series_z.dropna(), pct))
        marginal_beta = beta_c + beta_cv * v
        # Delta-method variance: var(beta_c) + v^2 * var(beta_cv) + 2v * cov(beta_c, beta_cv)
        var_marginal = (
            se_c**2
            + v**2 * se_cv**2
            + 2 * v * cov_c_cv
        )
        se_marginal = np.sqrt(max(var_marginal, 0))
        rows.append({
            "vulnerability_percentile":   pct,
            "vulnerability_value_z":      v,
            "marginal_beta":              marginal_beta,
            "marginal_se":                se_marginal,
            "marginal_irr":               np.exp(marginal_beta),
            "marginal_irr_ci95_low":      np.exp(marginal_beta - 1.96 * se_marginal),
            "marginal_irr_ci95_high":     np.exp(marginal_beta + 1.96 * se_marginal),
        })
    return rows


def extract_diagnostics(fit, data: pd.DataFrame) -> dict:
    return {
        "n_observations":         int(fit.nobs),
        "n_provinces":            int(data[PROVINCE_FE].nunique()),
        "n_periods":              int(data[PERIOD_FE].nunique()),
        "outcome":                OUTCOME,
        "model_family":           "Poisson",
        "link_function":          "log",
        "offset":                 OFFSET,
        "province_fixed_effects": True,
        "period_fixed_effects":   True,
        "cluster_variable":       CLUSTER,
        "converged":              bool(getattr(fit, "converged", None)),
        "iterations":             getattr(fit, "fit_history", {}).get("iteration", None),
        "log_likelihood":         fit.llf,
        "deviance":               fit.deviance,
        "pearson_chi2":           fit.pearson_chi2,
        "aic":                    fit.aic,
    }


def write_multiplicity_note(out: Path) -> None:
    lines = [
        "# TB-INSIGHT — Task 6: Multiplicity and Uncertainty Note",
        "",
        "## Number of models",
        "",
        "Nine interaction models are estimated (3 climate exposures x 3",
        "vulnerability variables), each separately.",
        "",
        "## No kitchen-sink model",
        "",
        "No model includes more than one vulnerability variable or more than one",
        "climate x vulnerability interaction term at a time. This avoids over-",
        "specification and preserves interpretability of individual contrasts.",
        "",
        "## Multiplicity",
        "",
        "Nine interaction p-values are tested. These are NOT adjusted for multiple",
        "comparisons. A statistically significant interaction in one of nine models",
        "should not be interpreted as confirmatory evidence of effect modification.",
        "Any nominally significant interaction should be treated as exploratory",
        "and requires replication or pre-specified sensitivity analysis.",
        "",
        "## Interpretation of interaction coefficient",
        "",
        "The interaction coefficient (beta_cv) represents the change in the",
        "log rate-ratio for a +1 SD increase in the climate exposure, associated",
        "with a +1 SD increase in the vulnerability variable (both standardized).",
        "This is a multiplicative interaction on the rate scale.",
        "",
        "## Marginal contrasts",
        "",
        "Marginal contrasts are computed at the 10th, 50th, and 90th percentiles",
        "of the standardized vulnerability distribution. These represent the",
        "estimated climate-TB association at low, median, and high vulnerability",
        "settings within the observed range. Delta-method standard errors are used.",
        "",
        "## Causal interpretation",
        "",
        "No causal interpretation is warranted. All results are ecological",
        "associations in the province-month panel. Vulnerability variables are",
        "time-invariant reference-period BPS values; they do not vary within",
        "provinces over the analysis period.",
    ]
    with open(out / "multiplicity_note.md", "w", encoding="utf-8") as f:
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

    # Standardize vulnerability variables, add _z columns
    vuln_std_info: dict[str, dict] = {}
    for vuln_label, vuln_col in VULNERABILITY_VARS:
        if vuln_col not in data.columns:
            raise ValueError(f"Missing vulnerability column: {vuln_col}")
        z_col = f"{vuln_col}_z"
        data[z_col], mu, sd = standardize(data[vuln_col])
        vuln_std_info[vuln_col] = {"mean": mu, "sd": sd, "z_col": z_col}
        print(f"  Standardized {vuln_col}: mean={mu:.4f}, sd={sd:.4f}")

    all_coef_rows:     list[dict] = []
    all_contrast_rows: list[dict] = []

    for climate_label, climate_col in CLIMATE_EXPOSURES:
        for vuln_label, vuln_col in VULNERABILITY_VARS:
            model_id = f"{climate_label}_x_{vuln_label}"
            z_col    = vuln_std_info[vuln_col]["z_col"]
            out_dir  = OUTPUT_ROOT / model_id
            out_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n  Running: {model_id}")

            formula = build_formula(climate_col, z_col)
            fit     = fit_ppml(data, formula)
            diag    = extract_diagnostics(fit, data)
            coefs   = extract_interaction_coefs(fit, climate_col, z_col)
            contrasts = compute_marginal_contrasts(
                fit, climate_col, z_col, data[z_col]
            )

            converged = diag["converged"]
            print(f"    converged={converged}, AIC={diag['aic']:.2f}, "
                  f"n_coefs_extracted={len(coefs)}")

            # Write per-model files
            pd.DataFrame(coefs).to_csv(out_dir / "coefficients.csv", index=False)
            pd.DataFrame(diag, index=[0]).to_csv(out_dir / "diagnostics.csv", index=False)
            pd.DataFrame(contrasts).to_csv(out_dir / "marginal_contrasts.csv", index=False)

            meta = {
                "model_id":              model_id,
                "task":                  "task6_social_interactions",
                "analysis_plan_version": "1.0",
                "climate_family":        climate_label,
                "climate_variable":      climate_col,
                "vulnerability_label":   vuln_label,
                "vulnerability_variable": vuln_col,
                "vulnerability_z_col":   z_col,
                "vulnerability_mean":    vuln_std_info[vuln_col]["mean"],
                "vulnerability_sd":      vuln_std_info[vuln_col]["sd"],
                "formula":               formula,
                "offset":                OFFSET,
                "fixed_effects":         [PROVINCE_FE, PERIOD_FE],
                "standard_errors":       "cluster-robust by province",
                "marginal_contrast_percentiles": CONTRAST_PERCENTILES,
                "n_observations":        diag["n_observations"],
                "converged":             converged,
                "run_timestamp_utc":     run_ts,
            }
            with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            with open(out_dir / "model_summary.txt", "w", encoding="utf-8") as f:
                f.write(f"TB-INSIGHT -- Social Vulnerability Interaction\n")
                f.write(f"Model ID     : {model_id}\n")
                f.write(f"Climate      : {climate_col}\n")
                f.write(f"Vulnerability: {vuln_col} (standardized as {z_col})\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Formula: {formula}\n")
                f.write(f"Offset : {OFFSET}\n")
                f.write("SE     : cluster-robust by province_code\n\n")
                f.write("Diagnostics:\n")
                f.write(pd.DataFrame([diag]).to_string(index=False))
                f.write("\n\nCoefficients:\n")
                f.write(pd.DataFrame(coefs).to_string(index=False))
                f.write("\n\nMarginal contrasts (climate IRR at low/med/high vulnerability):\n")
                f.write(pd.DataFrame(contrasts).to_string(index=False))
                f.write("\n")

            # Accumulate for cross-model summary
            for row in coefs:
                all_coef_rows.append({
                    "model_id":       model_id,
                    "climate_family": climate_label,
                    "vuln_label":     vuln_label,
                    **row,
                })
            for row in contrasts:
                all_contrast_rows.append({
                    "model_id":       model_id,
                    "climate_family": climate_label,
                    "climate_var":    climate_col,
                    "vuln_label":     vuln_label,
                    "vuln_var":       vuln_col,
                    **row,
                })

    # Cross-model summaries
    pd.DataFrame(all_coef_rows).to_csv(
        OUTPUT_ROOT / "coefficients_all_interactions.csv", index=False
    )
    pd.DataFrame(all_contrast_rows).to_csv(
        OUTPUT_ROOT / "marginal_contrasts.csv", index=False
    )

    # Multiplicity note
    write_multiplicity_note(OUTPUT_ROOT)

    # Top-level metadata
    top_meta = {
        "task":                  "task6_social_interactions",
        "analysis_plan_version": "1.0",
        "run_timestamp_utc":     run_ts,
        "models_run":            [
            f"{cl}_{vl}" for cl, _ in CLIMATE_EXPOSURES
            for vl, _ in VULNERABILITY_VARS
        ],
        "design":                "One interaction per model; no kitchen-sink",
        "marginal_contrast_percentiles": CONTRAST_PERCENTILES,
        "multiplicity_note":     "9 interaction tests; p-values not adjusted",
        "outcome":               OUTCOME,
        "offset":                OFFSET,
        "fixed_effects":         [PROVINCE_FE, PERIOD_FE],
        "standard_errors":       "cluster-robust by province",
        "vulnerability_standardization": {
            v: {"mean": vuln_std_info[v]["mean"], "sd": vuln_std_info[v]["sd"]}
            for _, v in VULNERABILITY_VARS
        },
    }
    with open(OUTPUT_ROOT / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(top_meta, f, indent=2)

    print("\n" + "=" * 60)
    print("Task 6 Complete")
    print("=" * 60)
    print(f"  Models run: {len(CLIMATE_EXPOSURES) * len(VULNERABILITY_VARS)}")
    print(f"  Output    : {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
