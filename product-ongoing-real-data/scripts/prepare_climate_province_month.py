"""Download and aggregate official NASA POWER climate data to Indonesian provinces.

The script uses the BIG province polygon service already downloaded to
data/raw/big/big_province_boundaries_generalized.geojson. NASA POWER
regional requests are tiled because the API limits each request to a 10 degree
latitude/longitude span. Monthly observations from 1981-2025 are retained so
1991-2020 month-specific normals and z-scores can be calculated reproducibly.
"""

from __future__ import annotations

import calendar
import json
import math
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import xarray as xr
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "nasa_power"
CURATED_DIR = ROOT / "data" / "processed"
BIG_PATH = ROOT / "data" / "raw" / "big" / "big_province_boundaries_generalized.geojson"
POWER_ENDPOINT = "https://power.larc.nasa.gov/api/temporal/monthly/regional"
BIG_SOURCE = "https://geoservices.big.go.id/rbi/rest/services/BATASWILAYAH/BATAS_WILAYAH/MapServer/12"
POWER_DOCS = "https://power.larc.nasa.gov/docs/services/api/temporal/monthly/"

PARAMETERS = {
    "T2M": "temperature_c",
    "RH2M": "relative_humidity_pct",
    "PRECTOTCORR": "precipitation_mm_day",
}
LON_TILES = [(94.5, 104.5), (104.5, 114.5), (114.5, 124.5), (124.5, 134.5), (134.5, 141.5)]
LAT_TILES = [(-11.5, -1.5), (-1.5, 6.5)]

NAME_MAP = {
    "Daerah Istimewa Yogyakarta": "DI YOGYAKARTA",
    "Kepulauan Bangka Belitung": "KEP. BANGKA BELITUNG",
}


def download_tiles() -> list[dict]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    session = requests.Session()
    session.headers.update({"User-Agent": "TB-INSIGHT research data preparation/1.0"})
    for parameter in PARAMETERS:
        for lat_min, lat_max in LAT_TILES:
            for lon_min, lon_max in LON_TILES:
                name = f"power_{parameter}_1981_2025_lat{lat_min:g}_{lat_max:g}_lon{lon_min:g}_{lon_max:g}.nc".replace("-", "m")
                path = RAW_DIR / name
                params = {
                    "latitude-min": lat_min,
                    "latitude-max": lat_max,
                    "longitude-min": lon_min,
                    "longitude-max": lon_max,
                    "parameters": parameter,
                    "community": "SB",
                    "start": 1981,
                    "end": 2025,
                    "format": "NETCDF",
                }
                if not path.exists() or path.stat().st_size < 1000:
                    for attempt in range(4):
                        response = session.get(POWER_ENDPOINT, params=params, timeout=180)
                        if response.ok and response.content[:4] == b"\x89HDF":
                            path.write_bytes(response.content)
                            break
                        if attempt == 3:
                            raise RuntimeError(f"POWER request failed for {name}: {response.status_code} {response.text[:500]}")
                        time.sleep(2 ** attempt)
                manifest.append({
                    "parameter": parameter,
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "bytes": path.stat().st_size,
                    "latitude_min": lat_min,
                    "latitude_max": lat_max,
                    "longitude_min": lon_min,
                    "longitude_max": lon_max,
                    "start_year": 1981,
                    "end_year": 2025,
                    "source_url": requests.Request("GET", POWER_ENDPOINT, params=params).prepare().url,
                })
    (RAW_DIR / "extraction_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_provinces() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(BIG_PATH)[["wadmpr", "kdppum", "geometry"]].copy()
    gdf["province"] = gdf["wadmpr"].replace(NAME_MAP).str.upper()
    # The generalized BIG export contains a small number of ring-topology
    # defects. Repair each land-part before combining province geometries.
    # buffer(0) both repairs invalid rings and drops mixed-dimension remnants
    # introduced by generalisation, leaving only polygonal area.
    gdf["geometry"] = gdf.geometry.apply(lambda geom: geom.buffer(0))
    # The service represents provinces as multiple island/land-part records.
    dissolved = gdf.dissolve(by="province", as_index=False)
    dissolved["geometry"] = dissolved.geometry.make_valid()
    # BIG's Papua codes in this service snapshot predate the current code
    # scheme. Harmonise by province name to the validated SITB/BPS lookup.
    lookup = pd.read_csv(CURATED_DIR / "tb_treatment_outcomes_province_month_official.csv")[["province_code", "province"]].drop_duplicates()
    dissolved = dissolved.merge(lookup, on="province", how="left", validate="one_to_one")
    if dissolved.province_code.isna().any():
        raise AssertionError(f"Unmatched BIG province names: {dissolved.loc[dissolved.province_code.isna(), 'province'].tolist()}")
    return dissolved[["province_code", "province", "geometry"]]


def open_parameter(parameter: str) -> xr.DataArray:
    arrays = []
    for path in sorted(RAW_DIR.glob(f"power_{parameter}_1981_2025_*.nc")):
        ds = xr.open_dataset(path)
        da = ds[parameter].sel(time=[t for t in ds.time.values if int(t) % 100 <= 12]).load()
        arrays.append(da)
        ds.close()
    merged = xr.combine_by_coords([a.to_dataset(name=parameter) for a in arrays], combine_attrs="override")[parameter]
    # Shared tile boundaries create duplicate coordinates; keep the first copy.
    _, lat_idx = np.unique(merged.lat.values, return_index=True)
    _, lon_idx = np.unique(merged.lon.values, return_index=True)
    return merged.isel(lat=np.sort(lat_idx), lon=np.sort(lon_idx)).sortby(["lat", "lon"])


def province_grid_membership(provinces: gpd.GeoDataFrame, lats: np.ndarray, lons: np.ndarray) -> dict[int, dict]:
    grid = [(i, j, float(lat), float(lon), Point(float(lon), float(lat))) for i, lat in enumerate(lats) for j, lon in enumerate(lons)]
    membership = {}
    for row in provinces.itertuples(index=False):
        hits = [(i, j, lat, lon) for i, j, lat, lon, point in grid if row.geometry.covers(point)]
        method = "grid_cells_within_BIG_polygon"
        if not hits:
            rp = row.geometry.representative_point()
            i, j, lat, lon, _ = min(grid, key=lambda item: (item[3] - rp.x) ** 2 + (item[2] - rp.y) ** 2)
            hits = [(i, j, lat, lon)]
            method = "nearest_POWER_grid_to_BIG_representative_point"
        membership[int(row.province_code)] = {
            "province": row.province,
            "cells": hits,
            "method": method,
            "n_grid_cells": len(hits),
        }
    return membership


def aggregate_parameter(da: xr.DataArray, parameter: str, membership: dict[int, dict]) -> pd.DataFrame:
    records = []
    for province_code, meta in membership.items():
        values = []
        weights = []
        for i, j, lat, _ in meta["cells"]:
            values.append(da.isel(lat=i, lon=j).values.astype(float))
            weights.append(math.cos(math.radians(lat)))
        matrix = np.vstack(values)
        matrix[(matrix < -900) | ~np.isfinite(matrix)] = np.nan
        w = np.asarray(weights)[:, None]
        valid_w = np.where(np.isfinite(matrix), w, 0.0)
        avg = np.nansum(matrix * w, axis=0) / np.sum(valid_w, axis=0)
        for time_code, value in zip(da.time.values, avg):
            year, month = divmod(int(time_code), 100)
            records.append({
                "province_code": province_code,
                "province": meta["province"],
                "year": year,
                "month": month,
                PARAMETERS[parameter]: value,
                "climate_spatial_method": meta["method"],
                "climate_grid_cells": meta["n_grid_cells"],
            })
    return pd.DataFrame(records)


def main() -> None:
    download_tiles()
    provinces = load_provinces()
    if len(provinces) != 38:
        raise AssertionError(f"Expected 38 provinces from BIG, found {len(provinces)}")

    parameter_frames = []
    membership = None
    for parameter in PARAMETERS:
        da = open_parameter(parameter)
        if membership is None:
            membership = province_grid_membership(provinces, da.lat.values, da.lon.values)
        frame = aggregate_parameter(da, parameter, membership)
        parameter_frames.append(frame)

    keys = ["province_code", "province", "year", "month", "climate_spatial_method", "climate_grid_cells"]
    climate = parameter_frames[0]
    for frame in parameter_frames[1:]:
        climate = climate.merge(frame, on=keys, how="outer", validate="one_to_one")
    climate["days_in_month"] = [calendar.monthrange(int(y), int(m))[1] for y, m in zip(climate.year, climate.month)]
    climate["precipitation_mm"] = climate["precipitation_mm_day"] * climate["days_in_month"]

    base = climate.query("1991 <= year <= 2020").copy()
    variables = ["temperature_c", "relative_humidity_pct", "precipitation_mm"]
    normals = base.groupby(["province_code", "province", "month"], as_index=False)[variables].agg(["mean", "std"])
    normals.columns = ["province_code", "province", "month"] + [f"{v}_{s}_1991_2020" for v in variables for s in ("mean", "std")]
    # Flattened aggregation order is variable-major in current pandas; explicitly rename for safety.
    expected = 3 + len(variables) * 2
    if len(normals.columns) != expected:
        raise AssertionError("Unexpected climatology column count")

    with_normals = climate.merge(normals, on=["province_code", "province", "month"], how="left", validate="many_to_one")
    for variable in variables:
        mean_col = f"{variable}_mean_1991_2020"
        std_col = f"{variable}_std_1991_2020"
        with_normals[f"{variable}_anomaly"] = with_normals[variable] - with_normals[mean_col]
        with_normals[f"{variable}_z"] = with_normals[f"{variable}_anomaly"] / with_normals[std_col].replace(0, np.nan)
    with_normals = with_normals.sort_values(["province_code", "year", "month"])
    lag_variables = ["temperature_c_z", "relative_humidity_pct_z", "precipitation_mm_z"]
    for variable in lag_variables:
        grouped = with_normals.groupby("province_code")[variable]
        with_normals[f"{variable}_lag1"] = grouped.shift(1)
        with_normals[f"{variable}_lag2"] = grouped.shift(2)
        with_normals[f"{variable}_lag3"] = grouped.shift(3)
        with_normals[f"{variable}_mean_lag0_2"] = grouped.transform(lambda s: s.rolling(3, min_periods=3).mean())
    observed = with_normals.query("year in [2024, 2025]").copy()
    observed["heavy_rain_anomaly"] = (observed["precipitation_mm_z"] >= 1.0).astype(int)
    observed["hot_anomaly"] = (observed["temperature_c_z"] >= 1.0).astype(int)
    observed["period"] = pd.to_datetime(dict(year=observed.year, month=observed.month, day=1)).dt.strftime("%Y-%m")
    observed["climate_source"] = "NASA POWER (MERRA-2 meteorology)"
    observed["boundary_source"] = "Badan Informasi Geospasial (BIG)"
    observed["source_url"] = POWER_DOCS
    observed["boundary_source_url"] = BIG_SOURCE
    observed = observed.sort_values(["province_code", "year", "month"])

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    observed.to_csv(CURATED_DIR / "climate_province_month_official.csv", index=False)
    normals.to_csv(CURATED_DIR / "climate_province_climatology_1991_2020.csv", index=False)

    validation = {
        "rows": len(observed),
        "provinces": int(observed.province_code.nunique()),
        "periods": int(observed[["year", "month"]].drop_duplicates().shape[0]),
        "duplicate_keys": int(observed.duplicated(["province_code", "year", "month"]).sum()),
        "missing_by_column": {k: int(v) for k, v in observed.isna().sum().items() if v},
        "spatial_methods": observed[["province_code", "province", "climate_spatial_method", "climate_grid_cells"]].drop_duplicates().to_dict("records"),
        "normal_period": "1991-2020",
        "observation_period": "2024-2025",
        "notes": [
            "POWER monthly PRECTOTCORR is a mean daily precipitation rate; precipitation_mm multiplies it by calendar days.",
            "Grid-cell averages are cosine-latitude weighted over POWER grid centres within BIG province polygons.",
            "Small/island provinces without a contained grid centre use the nearest POWER grid cell to a BIG representative point and are flagged.",
        ],
    }
    (CURATED_DIR / "climate_province_month_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(json.dumps({k: validation[k] for k in ["rows", "provinces", "periods", "duplicate_keys", "missing_by_column"]}, indent=2))


if __name__ == "__main__":
    main()
