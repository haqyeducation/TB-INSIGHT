"""Regression gates for the official-data S3 rebuild."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import networkx as nx
import pandas as pd
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def test_panel_is_complete_and_unique():
    panel = pd.read_csv(PROCESSED / "analysis_panel_tb_climate_disaster_2024_2025.csv")
    assert len(panel) == 912
    assert panel.province_code.nunique() == 38
    assert panel[["province_code", "year", "month"]].duplicated().sum() == 0
    assert panel[["jumlah_pasien", "population", "poverty_pct", "sanitation_access_pct",
                  "temperature_c_z", "precipitation_mm_z"]].notna().all().all()
    assert panel.poverty_pct.between(0, 100).all()


def test_boundary_and_primary_weights_are_valid_and_connected():
    boundary = gpd.read_file(PROCESSED / "spatial" / "province_boundaries_38.geojson")
    assert len(boundary) == 38
    assert boundary.geometry.is_valid.all()
    edges = pd.read_csv(PROCESSED / "spatial" / "spatial_weights_queen_bridge.csv", dtype=str)
    graph = nx.from_pandas_edgelist(edges, "province_code_i", "province_code_j")
    graph.add_nodes_from(boundary.province_code.astype(str).str.zfill(2))
    assert nx.is_connected(graph)
    assert set(edges.edge_type) == {"queen_contiguity", "bridge_shortest_component"}


def test_s3_model_counts_and_spatial_output():
    lag = pd.read_csv(ROOT / "results" / "models" / "climate_lags" / "coefficients_all_lags.csv")
    interaction = pd.read_csv(ROOT / "results" / "models" / "social_interactions" / "coefficients_all_interactions.csv")
    lisa = pd.read_csv(ROOT / "results" / "spatial" / "hotspot_monthly_lisa.csv")
    assert len(lag) == 12 and lag.converged.all()
    assert interaction.model_id.nunique() == 9
    assert len(lisa) == 912


def test_api_contracts():
    path = ROOT / "backend" / "main.py"
    spec = importlib.util.spec_from_file_location("tb_insight_api_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = TestClient(module.app)
    assert client.get("/api/summary").status_code == 200
    assert len(client.get("/api/analysis/panel", params={"province_code": "11"}).json()) == 24
    geojson = client.get("/api/spatial/provinces").json()
    assert len(geojson["features"]) == 38
    assert len(client.get("/api/spatial/lisa", params={"period": "2025-12"}).json()) == 38


def test_validation_files_are_green():
    panel = json.loads((PROCESSED / "analysis_panel_tb_climate_validation.json").read_text())
    spatial = json.loads((PROCESSED / "spatial" / "spatial_assets_validation.json").read_text())
    assert panel["all_required_complete"] is True
    assert panel["outcome_balance_failures"] == 0
    assert spatial["all_geometries_valid"] is True
    assert spatial["connected_primary_graph"] is True
