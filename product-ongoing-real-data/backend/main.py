"""TB-INSIGHT API serving only traceable official Kemenkes and BPS data."""

from __future__ import annotations

import os
import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="TB-INSIGHT API", description="Official national and province TB data")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
STATIC_DIR = ROOT / "frontend" / "dist"


def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path, dtype={"province_code": str})
    if "province_code" in frame:
        frame["province_code"] = frame["province_code"].str.zfill(2)
    return frame


tb_month = load_csv("tb_national_month_official.csv")
tb_province = load_csv("tb_province_annual_official.csv")
tb_province_month = load_csv("tb_treatment_outcomes_province_month_official.csv")
bps_annual = load_csv("bps_province_annual_official.csv")
analysis_panel = load_csv("analysis_panel_tb_climate_disaster_2024_2025.csv")
source_ledger = load_csv("project_source_ledger.csv")
province_panel = (
    tb_province.merge(
        bps_annual[bps_annual["year"] == 2024],
        on=["province_code", "province", "year"],
        how="left",
        suffixes=("_kemenkes", "_bps"),
        validate="one_to_one",
    )
    if not tb_province.empty and not bps_annual.empty
    else pd.DataFrame()
)


def records(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    safe = frame.astype(object).where(pd.notna(frame), None)
    return safe.to_dict(orient="records")


@app.get("/")
def read_root():
    index = STATIC_DIR / "index.html"
    if index.exists():
        from fastapi.responses import FileResponse
        return FileResponse(index)
    return {"message": "TB-INSIGHT official-data API"}


@app.get("/api/summary")
def get_summary():
    if tb_province.empty or tb_month.empty:
        raise HTTPException(status_code=503, detail="Curated official datasets are not ready")
    latest = tb_month.sort_values("period").iloc[-1]
    return {
        "province_reference_year": 2024,
        "province_count": int(tb_province["province_code"].nunique()),
        "tb_cases_2024": int(tb_province["tb_cases_total"].sum()),
        "national_month_period_min": str(tb_month["period"].min()),
        "national_month_period_max": str(tb_month["period"].max()),
        "national_month_indicators": int(tb_month["indicator"].nunique()),
        "latest_series_period": str(latest["period"]),
        "province_month_rows": int(len(tb_province_month)),
        "province_month_period_min": str(tb_province_month["period"].min()),
        "province_month_period_max": str(tb_province_month["period"].max()),
        "province_month_status": "Tersedia: kohort pasien mulai pengobatan TBC SO dan outcome, 38 provinsi x 12 bulan untuk 2024-2025",
    }


@app.get("/api/tb/national-monthly")
def get_tb_national_monthly():
    return records(tb_month)


@app.get("/api/tb/province-annual")
def get_tb_province_annual():
    return records(tb_province)


@app.get("/api/tb/province-monthly-treatment-outcomes")
def get_tb_province_monthly_treatment_outcomes():
    return records(tb_province_month)


@app.get("/api/bps/province-annual")
def get_bps_province_annual():
    return records(bps_annual)


@app.get("/api/analysis/province-2024")
def get_province_panel():
    return records(province_panel)


@app.get("/api/analysis/panel")
def get_analysis_panel(province_code: str | None = None, start: str = "2024-01", end: str = "2025-12"):
    frame = analysis_panel
    if province_code:
        frame = frame[frame.province_code == province_code.zfill(2)]
    if "period" in frame:
        frame = frame[(frame.period >= start) & (frame.period <= end)]
    return records(frame)


@app.get("/api/spatial/provinces")
def get_province_boundaries():
    path = DATA_DIR / "spatial" / "province_boundaries_38.geojson"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Canonical province boundary is not ready")
    import json
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))


@app.get("/api/spatial/lisa")
def get_lisa(period: str = "2025-12"):
    path = ROOT / "results" / "spatial" / "hotspot_monthly_lisa.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="LISA results are not ready")
    frame = pd.read_csv(path, dtype={"province_code": str})
    return records(frame[frame.period == period])


@app.get("/api/provenance")
def get_provenance():
    return records(source_ledger)


@app.get("/api/download/panel.csv")
def download_panel():
    path = DATA_DIR / "analysis_panel_tb_climate_disaster_2024_2025.csv"
    return FileResponse(path, filename=path.name, media_type="text/csv")


@app.get("/api/metadata")
def get_metadata():
    return {
        "sources": [
            {
                "publisher": "Kementerian Kesehatan RI",
                "dataset": "Pemantauan Kasus Tuberkulosis (SITB)",
                "url": "https://satusehat.kemkes.go.id/data/dashboard/5acb4fb6-af4a-48ac-abf5-3c255cfb5a26",
                "coverage": "Nasional bulanan, 2023-01 s.d. 2026-06",
            },
            {
                "publisher": "Kementerian Kesehatan RI",
                "dataset": "SITB TB Dashboard - kohort pengobatan provinsi per bulan",
                "url": "https://tbdashboard.sitb.id/ss_data_tbc03so_2025_provinsi_bulanan_list.php",
                "coverage": "38 provinsi x 12 bulan, kohort mulai pengobatan 2024 dan 2025",
            },
            {
                "publisher": "Kementerian Kesehatan RI",
                "dataset": "Profil Kesehatan Indonesia 2024, Lampiran 56.a",
                "url": "https://www.kemkes.go.id/id/profil-kesehatan-indonesia-2024",
                "coverage": "38 provinsi, tahun 2024",
            },
            {
                "publisher": "Badan Pusat Statistik",
                "dataset": "Statistik Indonesia dan indikator kesejahteraan resmi",
                "url": "https://www.bps.go.id",
                "coverage": "38 provinsi, 2023-2026; periode tiap variabel dipertahankan",
            },
        ],
        "limitations": [
            "Seri provinsi-bulanan adalah kohort pasien mulai pengobatan TBC sensitif obat beserta outcome, bukan estimasi insidensi atau semua notifikasi.",
            "TB Dashboard adalah sumber hidup; snapshot 2024-2025 dapat direvisi setelah ekstraksi.",
            "Data BPS merupakan observasi/proyeksi tahunan atau periode Susenas; tidak diinterpolasi menjadi bulanan.",
            "Tidak ada prediksi, skor risiko, optimasi SDM, kapasitas faskes, atau nilai sintetis di API ini.",
        ],
    }


@app.get("/api/dashboard")
def get_dashboard_snapshot():
    """Same alpha response used by the frontend's explicit local snapshot mode."""
    path = ROOT / "frontend" / "public" / "data" / "dashboard-snapshot.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Dashboard snapshot has not been prepared")
    return json.loads(path.read_text(encoding="utf-8"))


if STATIC_DIR.exists():
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{file_name:path}")
    async def serve_static_or_index(file_name: str):
        file_path = STATIC_DIR / file_name
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
