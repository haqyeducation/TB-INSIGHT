"""Run reproducible S3 PPML lag and climate-social interaction models."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "analysis_panel_tb_climate_disaster_2024_2025.csv"
OUT = ROOT / "results" / "models"
CLIMATE = {
    "temperature": "temperature_c_z",
    "precipitation": "precipitation_mm_z",
    "humidity": "relative_humidity_pct_z",
}
VULNERABILITY = {
    "poverty": "poverty_pct",
    "density": "population_density_per_km2",
    "sanitation": "sanitation_access_pct",
}


def fit_ppml(data: pd.DataFrame, formula: str):
    return smf.glm(
        formula, data=data, family=sm.families.Poisson(),
        offset=data["log_population_offset"],
    ).fit(cov_type="cluster", cov_kwds={"groups": data["province_code"]})


def estimate(fit, term: str) -> dict:
    beta, se = float(fit.params[term]), float(fit.bse[term])
    return {
        "term": term, "coefficient_log_rate": beta, "cluster_robust_se": se,
        "incidence_rate_ratio": float(np.exp(beta)),
        "irr_ci95_low": float(np.exp(beta - 1.96 * se)),
        "irr_ci95_high": float(np.exp(beta + 1.96 * se)),
        "p_value": float(fit.pvalues[term]),
    }


def diagnostics(fit, data: pd.DataFrame) -> dict:
    return {
        "n_observations": int(fit.nobs), "n_provinces": int(data.province_code.nunique()),
        "n_periods": int(data.period.nunique()), "converged": bool(fit.converged),
        "aic": float(fit.aic), "deviance": float(fit.deviance),
        "outcome": "jumlah_pasien", "offset": "log_population_offset",
        "fixed_effects": "province_code + period", "cluster": "province_code",
    }


def run_lags(data: pd.DataFrame, timestamp: str) -> None:
    out = OUT / "climate_lags"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for family, base in CLIMATE.items():
        for lag in range(4):
            variable = base if lag == 0 else f"{base}_lag{lag}"
            formula = f"jumlah_pasien ~ {variable} + C(province_code) + C(period)"
            complete = data.dropna(subset=[variable, "log_population_offset"]).copy()
            fit = fit_ppml(complete, formula)
            coef, diag = estimate(fit, variable), diagnostics(fit, complete)
            model_id = f"{family}_lag{lag}"
            model_out = out / family / f"lag{lag}"
            model_out.mkdir(parents=True, exist_ok=True)
            pd.DataFrame([coef]).to_csv(model_out / "coefficients.csv", index=False)
            pd.DataFrame([diag]).to_csv(model_out / "diagnostics.csv", index=False)
            (model_out / "metadata.json").write_text(json.dumps({
                "model_id": model_id, "formula": formula, "role": "lag sensitivity",
                "run_timestamp_utc": timestamp, **diag,
            }, indent=2), encoding="utf-8")
            rows.append({"model_id": model_id, "climate_family": family, "lag": lag, **coef, **diag})
    pd.DataFrame(rows).to_csv(out / "coefficients_all_lags.csv", index=False)
    (out / "selection_rule.md").write_text(
        "# Climate lag selection rule\n\n"
        "All twelve pre-specified models (three climate families × lag 0–3) are reported. "
        "The lag-0–2 mean remains the primary exposure window inherited from S2; individual lags "
        "are sensitivity analyses and are not selected by the smallest p-value. P-values are not "
        "multiplicity-adjusted, so these comparisons are exploratory.\n",
        encoding="utf-8",
    )


def run_interactions(data: pd.DataFrame, timestamp: str) -> None:
    out = OUT / "social_interactions"
    out.mkdir(parents=True, exist_ok=True)
    coef_rows, contrast_rows = [], []
    for vuln_label, variable in VULNERABILITY.items():
        z_col = f"{variable}_z"
        data[z_col] = (data[variable] - data[variable].mean()) / data[variable].std(ddof=1)
    for climate_label, base in CLIMATE.items():
        climate = f"{base}_mean_lag0_2"
        for vuln_label, variable in VULNERABILITY.items():
            z_col = f"{variable}_z"
            interaction = f"{climate}:{z_col}"
            formula = (
                f"jumlah_pasien ~ {climate} + {z_col} + {interaction} "
                "+ C(province_code) + C(period)"
            )
            complete = data.dropna(subset=[climate, z_col, "log_population_offset"]).copy()
            fit = fit_ppml(complete, formula)
            model_id = f"{climate_label}_x_{vuln_label}"
            model_out = out / model_id
            model_out.mkdir(parents=True, exist_ok=True)
            coefs = [estimate(fit, term) for term in [climate, z_col, interaction]]
            diag = diagnostics(fit, complete)
            pd.DataFrame(coefs).to_csv(model_out / "coefficients.csv", index=False)
            pd.DataFrame([diag]).to_csv(model_out / "diagnostics.csv", index=False)
            for row in coefs:
                coef_rows.append({"model_id": model_id, "climate_family": climate_label,
                                  "vulnerability": vuln_label, **row})
            cov = fit.cov_params()
            for percentile in [10, 50, 90]:
                v = float(np.percentile(complete[z_col], percentile))
                beta = float(fit.params[climate] + v * fit.params[interaction])
                variance = float(
                    cov.loc[climate, climate] + v * v * cov.loc[interaction, interaction]
                    + 2 * v * cov.loc[climate, interaction]
                )
                se = np.sqrt(max(variance, 0))
                contrast_rows.append({
                    "model_id": model_id, "vulnerability_percentile": percentile,
                    "vulnerability_value_z": v, "marginal_beta": beta,
                    "marginal_se": se, "marginal_irr": float(np.exp(beta)),
                    "marginal_irr_ci95_low": float(np.exp(beta - 1.96 * se)),
                    "marginal_irr_ci95_high": float(np.exp(beta + 1.96 * se)),
                })
            pd.DataFrame([r for r in contrast_rows if r["model_id"] == model_id]).to_csv(
                model_out / "marginal_contrasts.csv", index=False
            )
            (model_out / "metadata.json").write_text(json.dumps({
                "model_id": model_id, "formula": formula, "run_timestamp_utc": timestamp,
                "vulnerability_mean": float(data[variable].mean()),
                "vulnerability_sd": float(data[variable].std(ddof=1)), **diag,
            }, indent=2), encoding="utf-8")
    pd.DataFrame(coef_rows).to_csv(out / "coefficients_all_interactions.csv", index=False)
    pd.DataFrame(contrast_rows).to_csv(out / "marginal_contrasts.csv", index=False)
    (out / "multiplicity_note.md").write_text(
        "# Multiplicity and interpretation\n\nNine separate climate × vulnerability models are "
        "reported; no kitchen-sink model is used. P-values are unadjusted and exploratory. "
        "The province-month ecological estimates are associations, not causal effects.\n",
        encoding="utf-8",
    )


def main() -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    data = pd.read_csv(PANEL, dtype={"province_code": str})
    if len(data) != 912 or data[["province_code", "year", "month"]].duplicated().any():
        raise ValueError("Expected a unique 38-province × 24-month panel")
    if not data.poverty_pct.between(0, 100).all():
        raise ValueError("Invalid BPS poverty values")
    run_lags(data.copy(), timestamp)
    run_interactions(data.copy(), timestamp)
    print(json.dumps({"lag_models": 12, "interaction_models": 9, "timestamp": timestamp}, indent=2))


if __name__ == "__main__":
    main()
