import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
input_dir = base_dir / "data" / "processed"

# 1. Manipulate Tabular Data
df_csv_path = os.path.join(input_dir, "master_dataset_tabular.csv")
df_csv_path_v2 = os.path.join(input_dir, "master_dataset_tabular_v2.csv")
df = pd.read_csv(df_csv_path)

# Target hotpot kecamatans (North Surabaya)
hotspots = ['35.78.21', '35.78.22', '35.78.12', '35.78.16']

# Multiply cases by 3 for hotspots, and reduce capacity by 30%
mask = df['kecamatan_id'].isin(hotspots)
df.loc[mask, 'kasus_tb_total_dummy'] = (df.loc[mask, 'kasus_tb_total_dummy'] * 3).astype(int)
df.loc[mask, 'kapasitas_skrining_per_bulan_dummy'] = (df.loc[mask, 'kapasitas_skrining_per_bulan_dummy'] * 0.7).astype(int)

# For non-hotspots, reduce cases slightly to make the contrast huge
df.loc[~mask, 'kasus_tb_total_dummy'] = (df.loc[~mask, 'kasus_tb_total_dummy'] * 0.5).astype(int)

df.to_csv(df_csv_path_v2, index=False)
print("Tabular data manipulated successfully.")

# 2. Manipulate Spatial GeoJSON Data (Base 2024 for Epic 3)
geojson_path = os.path.join(input_dir, "master_dataset_spatial_2024.geojson")
geojson_path_v2 = os.path.join(input_dir, "master_dataset_spatial_2024_v2.geojson")
with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

for feature in geojson_data['features']:
    props = feature['properties']
    if props['kecamatan_id'] in hotspots:
        props['kasus_tb_total_dummy'] = int(props['kasus_tb_total_dummy'] * 3)
        props['kapasitas_skrining_per_bulan_dummy'] = int(props['kapasitas_skrining_per_bulan_dummy'] * 0.7)
    else:
        props['kasus_tb_total_dummy'] = int(props['kasus_tb_total_dummy'] * 0.5)

with open(geojson_path_v2, "w") as f:
    json.dump(geojson_data, f)
print("GeoJSON data manipulated successfully.")
