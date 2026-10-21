"""Build canonical 38-province boundaries and auditable spatial weights.

The primary graph starts with polygon queen contiguity.  Because Indonesia is
an archipelago, disconnected components are joined by the shortest polygon-to-
polygon links in an equal-area CRS until the graph is connected.  These added
links are explicitly labelled as bridges instead of being hidden as contiguity.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import networkx as nx
import pandas as pd

from prepare_climate_province_month import BIG_SOURCE, load_provinces


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "spatial"


def canonical_pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    provinces = load_provinces().sort_values("province_code").reset_index(drop=True)
    provinces["province_code"] = provinces.province_code.astype(str).str.zfill(2)
    if len(provinces) != 38 or not provinces.geometry.is_valid.all():
        raise AssertionError("Canonical BIG boundary must contain 38 valid provinces")

    boundary_path = OUT / "province_boundaries_38.geojson"
    provinces.to_file(boundary_path, driver="GeoJSON")

    projected = provinces.to_crs(6933)
    graph = nx.Graph()
    graph.add_nodes_from(provinces.province_code)
    records: dict[tuple[str, str], dict] = {}

    for i, left in projected.iterrows():
        for j in range(i + 1, len(projected)):
            right = projected.iloc[j]
            if left.geometry.intersects(right.geometry):
                pair = canonical_pair(left.province_code, right.province_code)
                distance_km = float(left.geometry.distance(right.geometry) / 1000)
                records[pair] = {
                    "province_code_i": pair[0], "province_code_j": pair[1],
                    "edge_type": "queen_contiguity", "distance_km": distance_km,
                }
                graph.add_edge(*pair)

    queen_edges = graph.number_of_edges()
    bridge_records = []
    while not nx.is_connected(graph):
        components = [set(c) for c in nx.connected_components(graph)]
        best = None
        for a_idx, comp_a in enumerate(components):
            for comp_b in components[a_idx + 1:]:
                for code_a in comp_a:
                    geom_a = projected.loc[projected.province_code == code_a, "geometry"].iloc[0]
                    for code_b in comp_b:
                        geom_b = projected.loc[projected.province_code == code_b, "geometry"].iloc[0]
                        distance = float(geom_a.distance(geom_b) / 1000)
                        candidate = (distance, *canonical_pair(code_a, code_b))
                        if best is None or candidate < best:
                            best = candidate
        if best is None:
            raise RuntimeError("Unable to connect spatial graph")
        distance_km, code_i, code_j = best
        record = {
            "province_code_i": code_i, "province_code_j": code_j,
            "edge_type": "bridge_shortest_component", "distance_km": distance_km,
        }
        records[(code_i, code_j)] = record
        bridge_records.append(record)
        graph.add_edge(code_i, code_j)

    names = provinces.set_index("province_code").province.to_dict()
    edges = pd.DataFrame(records.values()).sort_values(["edge_type", "province_code_i", "province_code_j"])
    edges["province_i"] = edges.province_code_i.map(names)
    edges["province_j"] = edges.province_code_j.map(names)
    edges = edges[["province_code_i", "province_i", "province_code_j", "province_j", "edge_type", "distance_km"]]
    edges.to_csv(OUT / "spatial_weights_queen_bridge.csv", index=False)

    # Three-nearest-neighbour alternative for sensitivity analysis.
    centroids = projected.geometry.centroid
    knn_rows: dict[tuple[str, str], dict] = {}
    for i, row in projected.iterrows():
        distances = []
        for j, other in projected.iterrows():
            if i == j:
                continue
            distances.append((float(centroids.iloc[i].distance(centroids.iloc[j]) / 1000), other.province_code))
        for distance_km, code_j in sorted(distances)[:3]:
            code_i, code_j = canonical_pair(row.province_code, code_j)
            knn_rows[(code_i, code_j)] = {
                "province_code_i": code_i, "province_i": names[code_i],
                "province_code_j": code_j, "province_j": names[code_j],
                "edge_type": "knn3_centroid", "distance_km": distance_km,
            }
    pd.DataFrame(knn_rows.values()).sort_values(["province_code_i", "province_code_j"]).to_csv(
        OUT / "spatial_weights_knn3.csv", index=False
    )

    metadata = {
        "boundary_source": "Badan Informasi Geospasial (BIG)",
        "boundary_source_url": BIG_SOURCE,
        "province_count": 38,
        "crs": str(provinces.crs),
        "all_geometries_valid": bool(provinces.geometry.is_valid.all()),
        "queen_edges": queen_edges,
        "bridge_edges": len(bridge_records),
        "total_primary_edges": int(len(edges)),
        "connected_primary_graph": bool(nx.is_connected(graph)),
        "components_before_bridging": None,
        "bridge_rule": "Iteratively join the two closest polygons in different components in EPSG:6933",
        "bridges": bridge_records,
        "note": "Bridges represent analytical neighbourhood links across water, not shared administrative borders.",
    }
    # Recompute pre-bridge component count without relying on a derived formula.
    queen_graph = nx.Graph()
    queen_graph.add_nodes_from(provinces.province_code)
    queen_graph.add_edges_from([
        (r["province_code_i"], r["province_code_j"])
        for r in records.values() if r["edge_type"] == "queen_contiguity"
    ])
    metadata["components_before_bridging"] = nx.number_connected_components(queen_graph)
    (OUT / "spatial_assets_validation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
