"""Rebuild the synthetic demonstration artifacts. Never use for real-data analysis."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "epic_1_data_engineering.py",
    "demo_data_manipulator.py",
    "epic_2_eda_analysis.py",
    "epic_3_spatial_ai.py",
    "epic_4_predictive_modeling.py",
]


def main() -> None:
    print("WARNING: rebuilding SYNTHETIC DEMO outputs; not real epidemiological data.")
    for step in STEPS:
        print(f"\n==> {step}", flush=True)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / step)],
            cwd=ROOT,
            check=True,
        )
    print("\nSynthetic demo pipeline selesai.")


if __name__ == "__main__":
    main()

