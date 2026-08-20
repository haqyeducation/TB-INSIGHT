"""Extract province covariates from official BPS PDF tables, preserving survey periods."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "bps"
CURATED = ROOT / "data" / "processed"

PROVINCES = [
    ("11", "Aceh"), ("12", "Sumatera Utara"), ("13", "Sumatera Barat"),
    ("14", "Riau"), ("15", "Jambi"), ("16", "Sumatera Selatan"),
    ("17", "Bengkulu"), ("18", "Lampung"), ("19", "Kepulauan Bangka Belitung"),
    ("21", "Kepulauan Riau"), ("31", "DKI Jakarta"), ("32", "Jawa Barat"),
    ("33", "Jawa Tengah"), ("34", "DI Yogyakarta"), ("35", "Jawa Timur"),
    ("36", "Banten"), ("51", "Bali"), ("52", "Nusa Tenggara Barat"),
    ("53", "Nusa Tenggara Timur"), ("61", "Kalimantan Barat"),
    ("62", "Kalimantan Tengah"), ("63", "Kalimantan Selatan"),
    ("64", "Kalimantan Timur"), ("65", "Kalimantan Utara"),
    ("71", "Sulawesi Utara"), ("72", "Sulawesi Tengah"),
    ("73", "Sulawesi Selatan"), ("74", "Sulawesi Tenggara"),
    ("75", "Gorontalo"), ("76", "Sulawesi Barat"), ("81", "Maluku"),
    ("82", "Maluku Utara"), ("91", "Papua Barat"), ("92", "Papua Barat Daya"),
    ("94", "Papua"), ("95", "Papua Selatan"), ("96", "Papua Tengah"),
    ("97", "Papua Pegunungan"),
]

ALIASES = {
    "Kepulauan Bangka Belitung": ["Kepulauan Bangka Belitung", "Bangka Belitung", "Kep. Bangka Belitung"],
    "Kepulauan Riau": ["Kepulauan Riau", "Kep. Riau"],
    "Riau": ["Riau", "R i a u"], "Jambi": ["Jambi", "J a m b i"], "Bali": ["Bali", "B a l i"],
}


def number_id(value: str) -> float:
    return float(value.strip().replace(".", "").replace(",", "."))


def extract_after_name(text: str, aliases: list[str], count: int) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    index = next(i for i, line in enumerate(lines) if line in aliases)
    values = []
    for line in lines[index + 1:]:
        if re.fullmatch(r"-?\d[\d.]*,?\d*", line) and line not in {"2020", "2023", "2024", "2025", "2026"}:
            values.append(line)
            if len(values) == count:
                return values
    raise ValueError(f"Only found {len(values)} values after {aliases}")


def extract_population() -> pd.DataFrame:
    specs = [
        (RAW / "Statistik_Indonesia_2024.pdf", 165, 166, {2023: 1}),
        (RAW / "Statistik_Indonesia_2025.pdf", 176, 177, {2024: 1, 2025: 2}),
        (RAW / "Statistik_Indonesia_2026.pdf", 196, 197, {2026: 2}),
    ]
    rows = []
    for pdf, population_page, density_page, years in specs:
        doc = pymupdf.open(pdf)
        pop_text, density_text = doc[population_page].get_text(), doc[density_page].get_text()
        for code, province in PROVINCES:
            aliases = ALIASES.get(province, [province])
            pop_values = extract_after_name(pop_text, aliases, 6)[:3]
            density_all = extract_after_name(density_text, aliases, 6)
            for year, position in years.items():
                # The four provinces created from Papua have an en dash for 2020.
                # PDF text extraction drops that placeholder, shifting numeric positions left.
                if province in {"Papua Barat Daya", "Papua Selatan", "Papua Tengah", "Papua Pegunungan"}:
                    population_position = {2023: 0, 2024: 0, 2025: 1, 2026: 1}[year]
                    density_position = {2023: 2, 2024: 2, 2025: 3, 2026: 3}[year]
                else:
                    population_position = position
                    density_position = 3 + position
                rows.append({
                    "province_code": code, "province": province.upper(), "year": year,
                    "population": round(number_id(pop_values[population_position]) * 1000),
                    "population_density_per_km2": number_id(density_all[density_position]),
                    "population_reference_date": f"{year}-06-30",
                    "population_source_file": pdf.name,
                    "population_source_table": "Tabel 3.1.1",
                })
    return pd.DataFrame(rows)


def extract_sanitation() -> pd.DataFrame:
    pdf = RAW / "Indikator_SDGS_Kesejahteraan_Rakyat_2025.pdf"
    text = pymupdf.open(pdf)[186].get_text()
    rows = []
    for code, province in PROVINCES:
        aliases = ALIASES.get(province, [province])
        values = extract_after_name(text, aliases, 3)
        for year, value in zip([2023, 2024, 2025], values):
            rows.append({
                "province_code": code, "year": year,
                "sanitation_access_pct": number_id(re.sub(r"(?<=\d)[12]$", "", value)),
                "sanitation_reference_period": f"{year} (Susenas)",
                "sanitation_source_file": pdf.name,
                "sanitation_source_table": "Tabel 5.4",
            })
    return pd.DataFrame(rows)


def extract_poverty() -> pd.DataFrame:
    rows = []
    # Statistik Indonesia 2025 Table 4.6.2 contains March and September 2024;
    # use March to align with the March 2025 Susenas estimate below.
    pdf_2024 = RAW / "Statistik_Indonesia_2025.pdf"
    text_2024 = pymupdf.open(pdf_2024)[358].get_text()
    for code, province in PROVINCES:
        aliases = ALIASES.get(province, [province])
        values = extract_after_name(text_2024, aliases, 6)
        rows.append({
            "province_code": code, "year": 2024, "poverty_pct": number_id(values[4]),
            "poverty_reference_period": "Maret 2024 (Susenas)",
            "poverty_source_file": pdf_2024.name, "poverty_source_table": "Tabel 4.6.2",
        })

    pdf_2025 = RAW / "Penghitungan_dan_Analisis_Kemiskinan_Makro_2025.pdf"
    doc_2025 = pymupdf.open(pdf_2025)
    text_2025 = doc_2025[27].get_text() + "\n" + doc_2025[28].get_text()
    for code, province in PROVINCES:
        aliases = ALIASES.get(province, [province])
        values = extract_after_name(text_2025, aliases, 6)
        rows.append({
            "province_code": code, "year": 2025, "poverty_pct": number_id(values[5]),
            "poverty_reference_period": "Maret 2025 (Susenas)",
            "poverty_source_file": pdf_2025.name, "poverty_source_table": "Tabel 2.5",
        })
    return pd.DataFrame(rows)


def main() -> None:
    population = extract_population()
    sanitation = extract_sanitation()
    poverty = extract_poverty()
    annual = population.merge(sanitation, on=["province_code", "year"], how="left")
    annual = annual.merge(poverty, on=["province_code", "year"], how="left")
    annual["source_publisher"] = "Badan Pusat Statistik"
    annual["extraction_method"] = "Machine extraction from official PDF table; row-count and national-total QA"
    annual = annual.sort_values(["province_code", "year"])
    CURATED.mkdir(parents=True, exist_ok=True)
    annual.to_csv(CURATED / "bps_province_annual_official.csv", index=False)

    checks = {
        "rows": len(annual), "provinces": int(annual.province_code.nunique()),
        "years": sorted(annual.year.unique().tolist()),
        "population_totals": annual.groupby("year").population.sum().astype(int).to_dict(),
        "missing_sanitation": int(annual.sanitation_access_pct.isna().sum()),
        "missing_poverty": int(annual.poverty_pct.isna().sum()),
        "notes": [
            "Population is the official mid-year projection and may be joined to all months as a denominator, not treated as a monthly observation.",
            "Poverty and sanitation retain their survey/reference period and are not interpolated.",
        ],
    }
    (CURATED / "bps_province_validation.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
