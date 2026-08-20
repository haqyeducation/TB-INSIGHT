"""Prepare official public TB exports without inventing province-month observations."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "satusehat_tb"
CURATED_DIR = ROOT / "data" / "processed"

MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
    "september": 9, "oktober": 10, "november": 11, "desember": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
}


def parse_number(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    return int(value.replace(".", "").replace(",", ""))


def parse_date(value: str) -> pd.Timestamp:
    slash_match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", value.strip())
    if slash_match:
        day, month, year = slash_match.groups()
        return pd.Timestamp(int(year), int(month), int(day))
    match = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", value.strip())
    if not match:
        raise ValueError(f"Unrecognized Indonesian date: {value!r}")
    day, month_name, year = match.groups()
    return pd.Timestamp(int(year), MONTHS[month_name.lower()], int(day))


def read_export(path: Path) -> pd.DataFrame:
    match = re.match(r"(\d{4})_national_(.+)\.csv", path.name)
    if not match:
        raise ValueError(f"Unexpected export filename: {path.name}")
    requested_year, indicator = match.groups()
    raw = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-16")
    if raw.shape[1] < 2:
        raise ValueError(f"No daily series in {path.name}")
    raw = raw.iloc[:, :2]
    raw.columns = ["date_text", "value"]
    raw["value"] = raw["value"].map(parse_number)
    raw = raw[raw["date_text"].str.strip().ne("")].dropna(subset=["value"])
    raw["date"] = raw["date_text"].map(parse_date)
    raw["indicator"] = indicator
    raw["requested_year"] = int(requested_year)
    raw["source_file"] = path.name
    return raw


def main() -> None:
    paths = sorted(RAW_DIR.glob("20??_national_*.csv"))
    if not paths:
        raise SystemExit("No national SATUSEHAT crosstab exports found")
    frames, failures = [], []
    for path in paths:
        try:
            frames.append(read_export(path))
        except Exception as exc:
            failures.append({"file": path.name, "error": str(exc)})
    monthly = pd.concat(frames, ignore_index=True).drop_duplicates(["indicator", "date", "value"])
    monthly["year"] = monthly["date"].dt.year
    monthly["month"] = monthly["date"].dt.month
    monthly["period"] = monthly["date"].dt.to_period("M").astype(str)
    monthly = monthly.sort_values(["indicator", "period"])
    monthly["is_complete_month"] = monthly["date"].dt.to_period("M") < pd.Timestamp.now().to_period("M")
    monthly["geographic_level"] = "national"
    monthly["source_system"] = "SITB"
    monthly["source_publisher"] = "Kementerian Kesehatan RI - SATUSEHAT Data"
    monthly["source_url"] = "https://satusehat.kemkes.go.id/data/dashboard/5acb4fb6-af4a-48ac-abf5-3c255cfb5a26"
    monthly["extraction_method"] = "Official Tableau crosstab monthly trend; no imputation"
    monthly["retrieved_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    monthly["quality_flag"] = monthly["is_complete_month"].map({True: "complete_calendar_month", False: "partial_current_month"})

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(CURATED_DIR / "tb_national_month_official.csv", index=False, quoting=csv.QUOTE_MINIMAL, date_format="%Y-%m-%d")
    province_month_path = CURATED_DIR / "tb_province_month_sitb_official.csv"
    province_month_rows = len(pd.read_csv(province_month_path)) if province_month_path.exists() else 0
    validation = {
        "raw_files": len(paths), "successful_files": len(frames), "failed_files": failures,
        "monthly_rows": len(monthly),
        "period_min": monthly["period"].min(), "period_max": monthly["period"].max(),
        "geographic_level": "national",
        "province_month_rows": province_month_rows,
        "province_month_status": "managed_by_prepare_sitb_province_month.py",
        "no_imputation_or_geographic_reconstruction": True,
    }
    (CURATED_DIR / "tb_national_month_validation.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(validation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
