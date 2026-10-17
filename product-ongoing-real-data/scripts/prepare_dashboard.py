"""Prepare a traceable local dashboard snapshot without changing source datasets."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
from shapely import force_2d, make_valid, union_all
from shapely.geometry import mapping, shape
try:
    from .dashboard_provenance import enrich_metadata
except ImportError:
    from dashboard_provenance import enrich_metadata

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend" / "public"
PROCESSED = ROOT / "data" / "processed"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value):
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (ValueError, TypeError):
        return None


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def province_key(name):
    return name.upper().strip().replace("KEP.", "KEPULAUAN").replace("DAERAH ISTIMEWA", "DI")


def province_geometries(boundary):
    def polygon_parts(geometry):
        if geometry.geom_type == "Polygon":
            return [] if geometry.is_empty else [geometry]
        if hasattr(geometry, "geoms"):
            return [polygon for part in geometry.geoms for polygon in polygon_parts(part)]
        return []

    groups = {}
    for feature in boundary["features"]:
        code = feature["properties"]["province_code"]
        geometry = force_2d(shape(feature["geometry"]))
        parts = polygon_parts(geometry)
        polygons = [valid for part in parts for valid in polygon_parts(part if part.is_valid else make_valid(part))]
        groups.setdefault(code, {"properties": feature["properties"], "geometries": []})["geometries"].extend(polygons)
    features = []
    for code, group in sorted(groups.items()):
        geometry = union_all(group["geometries"])
        if geometry.is_empty or geometry.geom_type not in ("Polygon", "MultiPolygon"):
            raise ValueError("Province geometry cannot be displayed: " + code)
        features.append({"type": "Feature", "properties": group["properties"], "geometry": mapping(geometry)})
    return {"type": "FeatureCollection", "features": features}


def prepare(reference_dir, climate_zip):
    panel_path = PROCESSED / "analysis_panel_tb_climate_disaster_2024_2025.csv"
    tb_path = PROCESSED / "tb_treatment_outcomes_province_month_official.csv"
    panel = read_csv(panel_path)
    tb = read_csv(tb_path)
    index = {(r["province_code"], r["period"]): r for r in panel}
    if len(index) != len(panel):
        raise ValueError("Duplicate province-month in analysis panel")
    keys = [(r["province_code"], r["period"]) for r in tb]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate province-month in treatment data")
    numeric_context = ["population", "population_density_per_km2", "poverty_pct",
                       "sanitation_access_pct", "temperature_c", "temperature_c_anomaly",
                       "temperature_c_z", "relative_humidity_pct", "precipitation_mm",
                       "precipitation_mm_anomaly", "precipitation_mm_z", "event_record_count",
                       "flood_events", "landslide_events", "extreme_weather_events"]
    outcomes = ["sembuh", "pengobatan_lengkap", "lost_to_follow_up", "meninggal",
                "gagal", "tidak_dievaluasi_pindah", "belum_ada_hasil"]
    rows, issues = [], []
    for source in tb:
        context = index.get((source["province_code"], source["period"]), {})
        row = {"province_code": source["province_code"].zfill(2), "province_name": source["province"],
               "period": source["period"], "treatment_started": number(source["jumlah_pasien"]),
               "source_url": source.get("source_url"), "source_snapshot_at": source.get("snapshot_retrieved_at"),
               "context_snapshot_at": context.get("snapshot_retrieved_at"), "warnings": []}
        row.update({field: number(context.get(field)) for field in numeric_context})
        row.update({field: number(source.get(field)) for field in outcomes})
        for field in ["population_reference_date", "poverty_reference_period", "sanitation_reference_period", "climate_spatial_method"]:
            row[field] = context.get(field) or None
        for field in ["poverty_pct", "sanitation_access_pct"]:
            if row[field] is not None and not 0 <= row[field] <= 100:
                row["warnings"].append(field + " di luar rentang 0–100%; nilai tidak ditampilkan.")
                issues.append({"province_code": row["province_code"], "province_name": row["province_name"],
                               "period": row["period"], "field": field, "reason": "INVALID_PERCENTAGE"})
                row[field] = None
        if row["population"] is not None and row["population"] <= 0:
            row["population"] = None
        count, population = row["treatment_started"], row["population"]
        row["rate_per_100k"] = count / population * 100000 if count is not None and population else None
        pending = row["belum_ada_hasil"]
        row["pending_share_pct"] = pending / count * 100 if pending is not None and count else None
        row["revision_status"] = "provisional" if row["period"].startswith("2025-") else "unknown"
        if count != number(context.get("jumlah_pasien")):
            row["warnings"].append("Jumlah pasien berbeda dari panel konteks; rate dihitung ulang dari kohort saat ini.")
        rows.append(row)
    provinces = sorted({(r["province_code"], r["province_name"]) for r in rows})
    aliases = {province_key(name): code for code, name in provinces}
    spatial = {}
    artifact_meta = []
    spatial_zip = reference_dir / "task_03" / "clickup-attachments-2026-10-11-16-26.zip"
    for zip_path in [spatial_zip, climate_zip]:
        if not zip_path or not zip_path.exists():
            continue
        with ZipFile(zip_path) as archive:
            for name in archive.namelist():
                if not name.endswith((".csv", ".json", ".Rmd")):
                    continue
                raw = archive.read(name)
                target = ROOT / "data" / "reference" / "dame_s3" / Path(name).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                artifact_meta.append({"name": target.name, "sha256": hashlib.sha256(raw).hexdigest(), "archive": zip_path.name})
                if name.endswith(".json"):
                    spatial[Path(name).stem] = json.loads(raw.decode("utf-8-sig"))
                elif name.endswith(".csv"):
                    records = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
                    for record in records:
                        if "province" in record:
                            record["province_code"] = aliases.get(province_key(record["province"]))
                            if not record["province_code"]:
                                raise ValueError("Unresolved province in Dame attachment: " + record["province"])
                        for key, value in list(record.items()):
                            if key not in ["province", "province_code", "period", "quadrant", "label_fdr", "persistence_category", "persistence_category_raw", "variable", "is_candidate_main_map"]:
                                record[key] = number(value)
                    spatial[Path(name).stem] = records
    periods = sorted({r["period"] for r in rows})
    boundary_path = ROOT / "data" / "raw" / "big" / "big_province_boundaries_generalized.geojson"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8-sig"))
    names = dict(provinces)
    for feature in boundary["features"]:
        boundary_code = str(feature["properties"]["kdppum"]).strip().zfill(2)
        code = aliases.get(province_key(feature["properties"]["wadmpr"]))
        if code not in names:
            raise ValueError("Boundary code not in data master: " + code)
        feature["properties"] = {"province_code": code, "province_name": names[code], "boundary_source_code": boundary_code}
    source_parts = len(boundary["features"])
    boundary = province_geometries(boundary)
    (PUBLIC / "maps").mkdir(parents=True, exist_ok=True)
    (PUBLIC / "maps" / "provinces.geojson").write_text(json.dumps(boundary, separators=(",", ":")), encoding="utf-8")
    generated = datetime.now(timezone.utc).isoformat()
    payload = {"contract_version": "dashboard-alpha-1", "rows": rows, "spatial": spatial,
               "meta": {"dataset_version": "local-" + checksum(tb_path)[:10] + "-" + checksum(panel_path)[:10],
                        "prepared_at": generated, "periods": periods,
                        "provinces": [{"code": code, "name": name} for code, name in provinces],
                        "observed_rows": len(rows), "expected_rows": len(provinces) * len(periods),
                        "duplicate_keys": 0, "invalid_fields": issues,
                        "invalid_field_counts": dict(Counter(r["field"] for r in issues)),
                        "sources": read_csv(PROCESSED / "project_source_ledger.csv"), "artifacts": artifact_meta,
                        "input_files": [{"name": p.name, "sha256": checksum(p)} for p in [tb_path, panel_path, boundary_path]],
                        "spatial_reconciliation": "Belum direkonsiliasi dengan snapshot kohort saat ini. Hasil Dame ditampilkan sebagai lampiran analisis terpisah.",
                        "qa_scope": "Pemeriksaan tampilan: kunci unik, persentase 0–100%, dan pencocokan kode wilayah. Bukan sign-off QA penelitian.",
                        "boundary": {"province_count": len(names), "parts": len(boundary["features"]), "source_parts": source_parts,
                                     "source": "BIG", "representation": "geographic", "display_processing": "Valid polygon components unioned by canonical province identity; collapsed non-area components omitted. Source geometry unchanged."}}}
    payload["meta"].update(enrich_metadata(ROOT, payload["meta"]["sources"], rows, artifact_meta))
    payload["meta"]["spatial_periods"] = sorted({r["period"] for r in spatial.get("hotspot_monthly_lisa_R", [])})
    payload["meta"]["spatial_methods"] = spatial.get("hotspot_persistence_validation_R", {})
    (PUBLIC / "data").mkdir(parents=True, exist_ok=True)
    (PUBLIC / "data" / "dashboard-snapshot.json").write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "provinces": len(provinces), "periods": len(periods), "invalid_fields": len(issues), "artifacts": len(artifact_meta)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--climate-zip", type=Path)
    arguments = parser.parse_args()
    prepare(arguments.reference_dir, arguments.climate_zip)
