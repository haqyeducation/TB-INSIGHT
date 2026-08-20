import os
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Paths
base_dir = Path(__file__).resolve().parents[1]
dummy_dir = base_dir / "data" / "synthetic"
shp_path = base_dir / "data" / "boundaries" / "11032026_BATAS_KEC.shp"
output_dir = base_dir / "data" / "processed"

os.makedirs(output_dir, exist_ok=True)

# Remove huge file if exists
huge_file = os.path.join(output_dir, "master_dataset_spatial.geojson")
if os.path.exists(huge_file):
    try:
        os.remove(huge_file)
    except Exception as e:
        print(f"Warning: could not delete {huge_file}: {e}")

print("Starting Epic 1: Data Acquisition & Engineering")

# 1. Load Data
print("Loading datasets...")
df_master = pd.read_csv(os.path.join(dummy_dir, "01_master_kecamatan_surabaya_dummy.csv"))
df_dinkes = pd.read_csv(os.path.join(dummy_dir, "02_dinkes_tb_kecamatan_monthly_dummy_2015_2025.csv"))
df_bps = pd.read_csv(os.path.join(dummy_dir, "03_bps_sosiodemografi_kecamatan_annual_dummy_2015_2025.csv"))
df_faskes = pd.read_csv(os.path.join(dummy_dir, "04_faskes_kapasitas_skrining_kecamatan_static_dummy_2025.csv"))

gdf_shp = gpd.read_file(shp_path)

# 2. Data Cleaning & Standardization
print("Cleaning and standardizing data...")
def clean_kecamatan(df, col_name):
    if col_name in df.columns:
        df[col_name] = df[col_name].str.strip().str.upper()
    return df

df_master = clean_kecamatan(df_master, 'kecamatan')
df_dinkes = clean_kecamatan(df_dinkes, 'kecamatan')
df_bps = clean_kecamatan(df_bps, 'kecamatan')
df_faskes = clean_kecamatan(df_faskes, 'kecamatan')

# Handle missing values
df_dinkes.fillna(0, inplace=True)
df_bps.fillna(df_bps.median(numeric_only=True), inplace=True)
df_faskes.fillna(0, inplace=True)

# Remove duplicate cols
cols_to_drop_bps = ['kecamatan', 'wilayah_surabaya', 'source_flag']
cols_to_drop_faskes = ['kecamatan', 'wilayah_surabaya', 'source_flag', 'tahun_data']
cols_to_drop_master = ['kecamatan', 'wilayah_surabaya']

# 3. Data Integration (Merging)
print("Merging datasets into master tabular...")
merged = pd.merge(
    df_dinkes, 
    df_bps.drop(columns=cols_to_drop_bps), 
    on=['kecamatan_id', 'tahun'], 
    how='left'
)

merged = pd.merge(
    merged, 
    df_faskes.drop(columns=cols_to_drop_faskes), 
    on='kecamatan_id', 
    how='left'
)

merged = pd.merge(
    merged,
    df_master.drop(columns=cols_to_drop_master),
    on='kecamatan_id',
    how='left'
)

merged.sort_values(['kecamatan_id', 'tahun', 'bulan'], inplace=True)
merged.reset_index(drop=True, inplace=True)

# ---> EXTREME DATA MANIPULATION FOR DEMO <---
# We make 12 kecamatans extremely high burden and low capacity.
hotspots = [
    'SEMAMPIR', 'KENJERAN', 'PABEAN CANTIAN', 'SIMOKERTO', 'KREMBANGAN', 'ASEMROWO', # North
    'TAMBAKSARI', 'GUBENG', 'MULO REJO', 'SUKOLILO', # East/Center
    'SAWAHAN', 'TEGALSARI', 'WONOKROMO' # Center/South
]
# Ensure uppercase
hotspots = [h.upper() for h in hotspots]

mask = merged['kecamatan'].str.upper().str.strip().isin(hotspots)
# Double the cases (instead of 4x) for realistic but high burden
merged.loc[mask, 'kasus_tb_total_dummy'] = (merged.loc[mask, 'kasus_tb_total_dummy'] * 2).astype(int)
# Set capacity to be always 20% lower than the cases to ensure it's Kritis but realistic
merged.loc[mask, 'kapasitas_skrining_per_bulan_dummy'] = (merged.loc[mask, 'kasus_tb_total_dummy'] * 0.8).astype(int)
# For non-hotspots, leave as is or slight reduce
merged.loc[~mask, 'kasus_tb_total_dummy'] = (merged.loc[~mask, 'kasus_tb_total_dummy'] * 0.8).astype(int)
# ----------------------------------------------

# Fix NaN positivity rate
import numpy as np
merged['positivity_rate_dummy'] = pd.to_numeric(merged['positivity_rate_dummy'], errors='coerce')
merged['positivity_rate_dummy'] = merged['positivity_rate_dummy'].fillna(np.random.uniform(0.08, 0.15))

tabular_output = os.path.join(output_dir, "master_dataset_tabular_v2.csv")
merged.to_csv(tabular_output, index=False)
print(f"Master tabular dataset saved to: {tabular_output} (Rows: {len(merged)})")

# 4. Spatial Join (Base Map only)
print("Preparing lightweight base spatial map...")
# Match by Name instead of KODE to fix mismatch bug
gdf_shp['K_JOIN'] = gdf_shp['K'].str.upper().str.replace(' ', '', regex=False)
merged['kec_upper'] = merged['kecamatan'].str.upper().str.replace(' ', '', regex=False)

gdf_merged = gdf_shp[['KODE', 'geometry', 'K', 'K_JOIN']].rename(columns={'KODE': 'shp_kode', 'K': 'nama_kecamatan_shp'})

# Join with only the latest static master data
merged_static = merged[merged['tahun'] == 2024].groupby('kecamatan_id').last().reset_index()

# Merge on Name (Robust)
gdf_static_master = gdf_merged.merge(merged_static, left_on='K_JOIN', right_on='kec_upper', how='inner')
gdf_static_master = gpd.GeoDataFrame(gdf_static_master, geometry='geometry')

if gdf_shp.crs is not None:
    gdf_static_master.set_crs(gdf_shp.crs, inplace=True, allow_override=True)

# Convert datetimes
for col in gdf_static_master.columns:
    if pd.api.types.is_datetime64_any_dtype(gdf_static_master[col]):
        gdf_static_master[col] = gdf_static_master[col].dt.strftime('%Y-%m-%d')

gdf_static_master = gdf_static_master.to_crs(epsg=4326)
spatial_output = os.path.join(output_dir, "master_dataset_spatial_2024_v2.geojson")
gdf_static_master.to_file(spatial_output, driver='GeoJSON')
print(f"Static master spatial dataset saved to: {spatial_output}")

spatial_kecamatan_output = os.path.join(output_dir, "batas_kecamatan_wgs84.geojson")
gdf_merged.to_crs(epsg=4326).to_file(spatial_kecamatan_output, driver='GeoJSON')
print(f"Base boundaries saved to: {spatial_kecamatan_output}")

print("Epic 1 Execution Complete!")
