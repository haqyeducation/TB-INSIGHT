"""Rebuild all processed datasets and preliminary results from local raw snapshots."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "prepare_national_province_data.py",
    "prepare_kemenkes_province_annual.py",
    "prepare_bps_province_covariates.py",
    "build_analysis_panel.py",
    "prepare_sitb_province_month.py",
    "prepare_climate_province_month.py",
    "prepare_bnpb_province_month.py",
    "build_tb_climate_project_panel.py",
    "run_preliminary_tb_climate_models.py",
]


def main() -> None:
    for step in STEPS:
        print(f"\n==> {step}", flush=True)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / step)],
            cwd=ROOT,
            check=True,
        )
    print("\nPipeline selesai. Jalankan scripts/validate_project.py.")


if __name__ == "__main__":
    main()

