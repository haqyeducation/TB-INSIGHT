"""Extract province-level 2024 TB indicators from official Kemenkes Profile Appendix 56.a."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "kemenkes" / "Profil_Kesehatan_Indonesia_2024.pdf"
OUTPUT = ROOT / "data" / "processed" / "tb_province_annual_official.csv"

PROVINCE_CODES = {
    "ACEH": "11", "SUMATERA UTARA": "12", "SUMATERA BARAT": "13", "RIAU": "14",
    "JAMBI": "15", "SUMATERA SELATAN": "16", "BENGKULU": "17", "LAMPUNG": "18",
    "KEP. BANGKA BELITUNG": "19", "KEPULAUAN RIAU": "21", "DKI JAKARTA": "31",
    "JAWA BARAT": "32", "JAWA TENGAH": "33", "DI YOGYAKARTA": "34", "JAWA TIMUR": "35",
    "BANTEN": "36", "BALI": "51", "NUSA TENGGARA BARAT": "52", "NUSA TENGGARA TIMUR": "53",
    "KALIMANTAN BARAT": "61", "KALIMANTAN TENGAH": "62", "KALIMANTAN SELATAN": "63",
    "KALIMANTAN TIMUR": "64", "KALIMANTAN UTARA": "65", "SULAWESI UTARA": "71",
    "SULAWESI TENGAH": "72", "SULAWESI SELATAN": "73", "SULAWESI TENGGARA": "74",
    "GORONTALO": "75", "SULAWESI BARAT": "76", "MALUKU": "81", "MALUKU UTARA": "82",
    "PAPUA BARAT": "91", "PAPUA BARAT DAYA": "92", "PAPUA": "94", "PAPUA SELATAN": "95",
    "PAPUA TENGAH": "96", "PAPUA PEGUNUNGAN": "97",
}


def integer(text: str) -> int:
    return int(text.replace(".", ""))


def main() -> None:
    # PDF page 466 (1-based) contains the complete 38-province Appendix 56.a table.
    text = PdfReader(str(SOURCE)).pages[465].extract_text() or ""
    pattern = re.compile(
        r"^(\d+)\s+(.+?)\s+([\d.]+)\s+([\d.]+)\s+(\d+)%\s+"
        r"([\d.]+)\s+(\d+)%\s+([\d.]+)\s+(\d+)%\s+([\d.]+)\s+"
        r"(\d+)\s+([\d.]+)\s+(\d+)%\s+([\d.]+)\s+(\d+)%$",
        re.MULTILINE,
    )
    rows = []
    for match in pattern.finditer(text):
        (row_number, province, estimated_suspects, suspects_standard, suspects_pct,
         male_cases, male_pct, female_cases, female_pct, total_cases, cnr,
         estimated_incidence, treatment_coverage, child_cases, child_coverage) = match.groups()
        province = re.sub(r"\s+", " ", province.replace("\t", " ")).strip().upper()
        rows.append({
            "province_code": PROVINCE_CODES[province], "province": province, "year": 2024,
            "estimated_tb_suspects": integer(estimated_suspects),
            "tb_suspects_standard_service": integer(suspects_standard),
            "tb_suspects_standard_service_pct": int(suspects_pct),
            "tb_cases_male": integer(male_cases), "tb_cases_male_pct": int(male_pct),
            "tb_cases_female": integer(female_cases), "tb_cases_female_pct": int(female_pct),
            "tb_cases_total": integer(total_cases), "case_notification_rate_per_100k": int(cnr),
            "estimated_tb_incidence": integer(estimated_incidence),
            "treatment_coverage_pct": int(treatment_coverage),
            "tb_cases_age_0_14": integer(child_cases), "child_case_detection_coverage_pct": int(child_coverage),
            "source_publisher": "Kementerian Kesehatan RI",
            "source_file": SOURCE.name, "source_table": "Lampiran 56.a",
            "source_page_pdf": 466, "reference_period": "2024",
            "data_status_date": "2025-03-17", "source_system": "Ditjen Penanggulangan Penyakit",
            "extraction_method": "Machine extraction from official PDF table; totals and row-count QA",
        })
    frame = pd.DataFrame(rows).sort_values("province_code")
    if len(frame) != 38 or frame["province_code"].nunique() != 38:
        raise ValueError(f"Expected 38 provinces, extracted {len(frame)} rows")
    if int(frame["tb_cases_total"].sum()) != 856_420:
        raise ValueError("TB case total does not match official Indonesia total 856,420")
    if not (frame["tb_cases_male"] + frame["tb_cases_female"] == frame["tb_cases_total"]).all():
        raise ValueError("Male + female does not equal total for one or more provinces")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT, index=False)
    validation = {
        "rows": len(frame), "provinces": frame["province_code"].nunique(), "year": 2024,
        "tb_cases_total": int(frame["tb_cases_total"].sum()),
        "official_national_total": 856420,
        "sex_sum_matches_total_all_rows": True,
        "source_page_pdf": 466,
    }
    (OUTPUT.parent / "tb_province_annual_validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
