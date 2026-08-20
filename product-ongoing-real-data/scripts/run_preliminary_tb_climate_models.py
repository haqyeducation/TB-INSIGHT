"""Run clearly labelled exploratory PPML fixed-effect models for project planning."""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "analysis_panel_tb_climate_disaster_2024_2025.csv"
OUTPUT = ROOT / "results" / "preliminary_tb_climate_ppml_results.csv"

SPECS = {
    "temperature_current": ["temperature_c_z"],
    "precipitation_current": ["precipitation_mm_z"],
    "humidity_current": ["relative_humidity_pct_z"],
    "joint_current": ["temperature_c_z", "precipitation_mm_z", "relative_humidity_pct_z"],
    "joint_3month_mean": ["temperature_c_z_mean_lag0_2", "precipitation_mm_z_mean_lag0_2", "relative_humidity_pct_z_mean_lag0_2"],
    "joint_3month_plus_disaster_sensitivity": [
        "temperature_c_z_mean_lag0_2", "precipitation_mm_z_mean_lag0_2",
        "relative_humidity_pct_z_mean_lag0_2", "hydrometeorological_events",
    ],
}


def main() -> None:
    data = pd.read_csv(PANEL)
    rows = []
    for model_name, predictors in SPECS.items():
        formula = "jumlah_pasien ~ " + " + ".join(predictors) + " + C(province_code) + C(period)"
        fit = smf.glm(
            formula=formula,
            data=data,
            family=sm.families.Poisson(),
            offset=data.log_population_offset,
        ).fit(cov_type="cluster", cov_kwds={"groups": data.province_code})
        for variable in predictors:
            beta = fit.params[variable]
            se = fit.bse[variable]
            rows.append({
                "model": model_name,
                "variable": variable,
                "coefficient_log_rate": beta,
                "cluster_robust_se": se,
                "incidence_rate_ratio": np.exp(beta),
                "irr_ci95_low": np.exp(beta - 1.96 * se),
                "irr_ci95_high": np.exp(beta + 1.96 * se),
                "p_value": fit.pvalues[variable],
                "n_observations": int(fit.nobs),
                "province_fixed_effects": True,
                "period_fixed_effects": True,
                "population_offset": True,
                "interpretation_warning": "Exploratory ecological association; not causal; multiplicity not adjusted",
            })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
