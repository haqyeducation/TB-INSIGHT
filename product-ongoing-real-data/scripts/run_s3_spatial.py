"""Recompute monthly LISA and comparable map candidates from canonical weights."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SPATIAL = PROCESSED / "spatial"
OUT = ROOT / "results" / "spatial"


def fdr_bh(p: np.ndarray) -> np.ndarray:
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.minimum(adjusted, 1.0)
    return result


def weight_matrix(codes: list[str], edges: pd.DataFrame) -> np.ndarray:
    index = {code: i for i, code in enumerate(codes)}
    w = np.zeros((len(codes), len(codes)))
    for row in edges.itertuples(index=False):
        i, j = index[str(row.province_code_i).zfill(2)], index[str(row.province_code_j).zfill(2)]
        w[i, j] = w[j, i] = 1
    row_sum = w.sum(axis=1)
    if (row_sum == 0).any():
        raise ValueError("Spatial weight graph contains an isolate")
    return w / row_sum[:, None]


def local_moran(values: np.ndarray, w: np.ndarray, rng: np.random.Generator, permutations: int = 999):
    z = (values - values.mean()) / values.std(ddof=0)
    lag = w @ z
    observed = z * lag
    permuted = np.empty((permutations, len(z)))
    for p in range(permutations):
        zp = rng.permutation(z)
        permuted[p] = zp * (w @ zp)
    pseudo_p = (1 + (np.abs(permuted) >= np.abs(observed)).sum(axis=0)) / (permutations + 1)
    return z, lag, observed, pseudo_p


def save_map(gdf: gpd.GeoDataFrame, column: str, title: str, path: Path, cmap: str = "viridis") -> None:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    gdf.plot(column=column, cmap=cmap, linewidth=0.35, edgecolor="#334155", legend=True, ax=ax,
             missing_kwds={"color": "#e2e8f0", "label": "No data"})
    ax.set_title(title, fontsize=14, loc="left")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    maps = OUT / "maps"
    maps.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PROCESSED / "analysis_panel_tb_climate_disaster_2024_2025.csv",
                        dtype={"province_code": str})
    panel.province_code = panel.province_code.str.zfill(2)
    boundary = gpd.read_file(SPATIAL / "province_boundaries_38.geojson")
    boundary.province_code = boundary.province_code.astype(str).str.zfill(2)
    boundary = boundary.sort_values("province_code").reset_index(drop=True)
    codes = boundary.province_code.tolist()
    edges = pd.read_csv(SPATIAL / "spatial_weights_queen_bridge.csv", dtype=str)
    w = weight_matrix(codes, edges)

    rng = np.random.default_rng(20261017)
    monthly_rows = []
    for period, frame in panel.groupby("period", sort=True):
        frame = boundary[["province_code", "province"]].merge(
            frame[["province_code", "treatment_started_per_100k"]], on="province_code", validate="one_to_one"
        )
        z, lag, local_i, p = local_moran(frame.treatment_started_per_100k.to_numpy(), w, rng)
        p_fdr = fdr_bh(p)
        for idx, row in frame.iterrows():
            if z[idx] >= 0 and lag[idx] >= 0:
                quadrant = "high-high"
            elif z[idx] < 0 and lag[idx] < 0:
                quadrant = "low-low"
            elif z[idx] >= 0:
                quadrant = "high-low"
            else:
                quadrant = "low-high"
            monthly_rows.append({
                "period": period, "province_code": row.province_code, "province": row.province,
                "treatment_started_per_100k": row.treatment_started_per_100k,
                "z_value": z[idx], "spatial_lag_z": lag[idx], "local_moran_i": local_i[idx],
                "pseudo_p_value": p[idx], "fdr_p_value": p_fdr[idx],
                "quadrant": quadrant, "cluster_raw_0_05": quadrant if p[idx] <= .05 else "not_significant",
                "cluster_fdr_0_05": quadrant if p_fdr[idx] <= .05 else "not_significant",
            })
    monthly = pd.DataFrame(monthly_rows)
    monthly.to_csv(OUT / "hotspot_monthly_lisa.csv", index=False)
    persistence = monthly.groupby(["province_code", "province"], as_index=False).agg(
        months_high_high_raw=("cluster_raw_0_05", lambda s: int((s == "high-high").sum())),
        months_low_low_raw=("cluster_raw_0_05", lambda s: int((s == "low-low").sum())),
        months_high_high_fdr=("cluster_fdr_0_05", lambda s: int((s == "high-high").sum())),
        months_low_low_fdr=("cluster_fdr_0_05", lambda s: int((s == "low-low").sum())),
    )
    persistence.to_csv(OUT / "hotspot_persistence.csv", index=False)

    # Candidate layer comparison uses province means and z-standardisation,
    # avoiding the incomparable raw max-minus-min scales in the submitted file.
    aggregate = panel.groupby(["province_code", "province"], as_index=False).agg(
        treatment_rate=("treatment_started_per_100k", "mean"),
        temperature_anomaly=("temperature_c_z", "mean"),
        precipitation_anomaly=("precipitation_mm_z", "mean"),
        humidity_anomaly=("relative_humidity_pct_z", "mean"),
        poverty=("poverty_pct", "mean"), sanitation=("sanitation_access_pct", "mean"),
        density=("population_density_per_km2", "mean"), disasters=("event_record_count", "mean"),
    ).set_index("province_code").loc[codes].reset_index()
    aggregate["log_density"] = np.log1p(aggregate.density)
    candidate_rows = []
    for variable in ["treatment_rate", "temperature_anomaly", "precipitation_anomaly", "humidity_anomaly",
                     "poverty", "sanitation", "log_density", "disasters"]:
        values = aggregate[variable].to_numpy(float)
        z = (values - values.mean()) / values.std(ddof=0)
        global_i = float((len(z) / w.sum()) * (z @ w @ z) / (z @ z))
        candidate_rows.append({
            "layer": variable, "n_provinces": int(np.isfinite(values).sum()),
            "standardized_iqr": float(np.percentile(z, 75) - np.percentile(z, 25)),
            "global_moran_i": global_i, "absolute_global_moran_i": abs(global_i),
            "selection_note": "Comparable z-scale; rank is descriptive, not a causal model-selection rule",
        })
        aggregate[f"{variable}_z"] = z
    candidates = pd.DataFrame(candidate_rows).sort_values("absolute_global_moran_i", ascending=False)
    candidates.to_csv(OUT / "map_layer_candidates.csv", index=False)

    geo = boundary.merge(aggregate, on=["province_code", "province"], how="left", validate="one_to_one")
    save_map(geo, "treatment_rate", "Rerata mulai pengobatan TB per 100.000 (2024–2025)", maps / "treatment_rate.png", "YlOrRd")
    save_map(geo, "precipitation_anomaly", "Rerata anomali presipitasi (z-score, 2024–2025)", maps / "precipitation_anomaly.png", "BrBG")
    save_map(geo, "poverty", "Rerata persentase kemiskinan BPS (2024–2025)", maps / "poverty.png", "Purples")
    geo.drop(columns="geometry").to_csv(OUT / "province_map_attributes.csv", index=False)

    validation = {
        "monthly_rows": int(len(monthly)), "province_count": int(monthly.province_code.nunique()),
        "period_count": int(monthly.period.nunique()), "permutations": 999,
        "seed": 20261017, "weights": "queen contiguity plus explicit shortest-component bridges",
        "raw_significant": int((monthly.cluster_raw_0_05 != "not_significant").sum()),
        "fdr_significant": int((monthly.cluster_fdr_0_05 != "not_significant").sum()),
        "maps_rendered": 3,
        "method_note": "Permutation p-values use complete-label randomisation; FDR is applied separately within each month.",
    }
    (OUT / "spatial_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
