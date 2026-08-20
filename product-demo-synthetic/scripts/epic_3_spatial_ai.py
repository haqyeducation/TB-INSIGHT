import os
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from libpysal.weights import Queen
from esda.moran import Moran
from esda.getisord import G_Local
import folium
from pathlib import Path

# Configuration
base_dir = Path(__file__).resolve().parents[1]
input_dir = base_dir / "data" / "processed"
output_dir = base_dir / "results" / "epic_3_risk_maps"
os.makedirs(output_dir, exist_ok=True)

summary_file = base_dir / "results" / "epic_3_summary.txt"
with open(summary_file, "w") as f:
    f.write("=== EPIC 3: SPATIAL AI & RISK MAPPING SUMMARY ===\n\n")

print("Starting Epic 3: Spatial AI & Risk Mapping...")

# 1. Load Data
# We use the static 2024 spatial dataset
gdf = gpd.read_file(os.path.join(input_dir, "master_dataset_spatial_2024_v2.geojson"))

# Fill missing values if any
gdf['kasus_tb_total_dummy'] = gdf['kasus_tb_total_dummy'].fillna(0)
gdf['kepadatan_penduduk_per_km2_dummy'] = gdf['kepadatan_penduduk_per_km2_dummy'].fillna(gdf['kepadatan_penduduk_per_km2_dummy'].median())
gdf['persentase_kemiskinan_dummy'] = gdf['persentase_kemiskinan_dummy'].fillna(gdf['persentase_kemiskinan_dummy'].median())

# 2. Spatial Autocorrelation & Hotspot Analysis
print("Calculating Moran's I and Getis-Ord Gi*...")
# Create spatial weights
w = Queen.from_dataframe(gdf)
w.transform = 'r'

# Moran's I
y = gdf['kasus_tb_total_dummy'].values
moran = Moran(y, w)
with open(summary_file, "a") as f:
    f.write("--- SPATIAL AUTOCORRELATION (MORAN'S I) ---\n")
    f.write(f"Moran's I Index: {moran.I:.4f}\n")
    f.write(f"P-value: {moran.p_sim:.4f}\n")
    f.write(f"Interpretation: {'Clustered' if moran.I > 0 and moran.p_sim < 0.05 else 'Random or Dispersed'}\n\n")

# Getis-Ord Gi*
g_local = G_Local(y, w)
gdf['hotspot_zscore'] = g_local.Zs
gdf['hotspot_pvalue'] = g_local.p_sim

# 3. Machine Learning Clustering (K-Means & DBSCAN)
print("Executing Clustering Algorithms...")
features = ['kasus_tb_total_dummy', 'kepadatan_penduduk_per_km2_dummy', 'persentase_kemiskinan_dummy']
X = gdf[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# K-Means
kmeans = KMeans(n_clusters=3, random_state=42)
gdf['kmeans_cluster'] = kmeans.fit_predict(X_scaled)
sil_score = silhouette_score(X_scaled, gdf['kmeans_cluster'])
db_score = davies_bouldin_score(X_scaled, gdf['kmeans_cluster'])

with open(summary_file, "a") as f:
    f.write("--- K-MEANS CLUSTERING EVALUATION ---\n")
    f.write(f"Silhouette Score: {sil_score:.4f} (Closer to 1 is better)\n")
    f.write(f"Davies-Bouldin Index: {db_score:.4f} (Lower is better)\n\n")

# DBSCAN for Anomaly Detection
dbscan = DBSCAN(eps=1.5, min_samples=2)
gdf['dbscan_anomaly'] = dbscan.fit_predict(X_scaled)
anomalies = gdf[gdf['dbscan_anomaly'] == -1]['nama_kecamatan_shp'].tolist()
with open(summary_file, "a") as f:
    f.write("--- DBSCAN ANOMALY DETECTION ---\n")
    f.write(f"Anomalous Kecamatan (Outliers): {', '.join(anomalies) if anomalies else 'None'}\n\n")

# 4. Composite Risk Index & Zone Classification
print("Calculating Risk Index...")
# Using weighted sum based on normalized Epic 2 feature importance
# Weights approx: Kepadatan 0.70, Kemiskinan 0.15, TB Cases (as proxy for risk) 0.15
norm_kepadatan = (gdf['kepadatan_penduduk_per_km2_dummy'] - gdf['kepadatan_penduduk_per_km2_dummy'].min()) / (gdf['kepadatan_penduduk_per_km2_dummy'].max() - gdf['kepadatan_penduduk_per_km2_dummy'].min())
norm_kemiskinan = (gdf['persentase_kemiskinan_dummy'] - gdf['persentase_kemiskinan_dummy'].min()) / (gdf['persentase_kemiskinan_dummy'].max() - gdf['persentase_kemiskinan_dummy'].min())
norm_kasus = (gdf['kasus_tb_total_dummy'] - gdf['kasus_tb_total_dummy'].min()) / (gdf['kasus_tb_total_dummy'].max() - gdf['kasus_tb_total_dummy'].min())

gdf['risk_score'] = (norm_kepadatan * 0.70) + (norm_kemiskinan * 0.15) + (norm_kasus * 0.15)
gdf['risk_score'] = gdf['risk_score'] * 100 # Scale 0-100

# Classification
def classify_risk(score):
    if score >= 60: return 'High Risk'
    elif score >= 30: return 'Medium Risk'
    else: return 'Low Risk'

gdf['risk_zone'] = gdf['risk_score'].apply(classify_risk)

with open(summary_file, "a") as f:
    f.write("--- RISK ZONE CLASSIFICATION ---\n")
    f.write(gdf['risk_zone'].value_counts().to_string() + "\n\n")

# 5. Visualizations
print("Generating Static and Interactive Maps...")

# Ensure no Timestamps exist before JSON serialization
for col in gdf.columns:
    if pd.api.types.is_datetime64_any_dtype(gdf[col]):
        gdf[col] = gdf[col].astype(str)

# Static Risk Map
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
gdf.plot(column='risk_score', ax=ax, legend=True, 
         cmap='Reds', edgecolor='black',
         legend_kwds={'label': "Composite Risk Score (0-100)", 'orientation': "horizontal"})
plt.title('Peta Risiko TB Surabaya (Risk Score)')
ax.axis('off')
plt.savefig(os.path.join(output_dir, "T307_static_risk_map.png"), dpi=300, bbox_inches='tight')
plt.close()

# Interactive Folium Map
center_lat = gdf.geometry.centroid.y.mean()
center_lon = gdf.geometry.centroid.x.mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles='CartoDB dark_matter')

folium.Choropleth(
    geo_data=gdf,
    name='Risk Zone',
    data=gdf,
    columns=['kecamatan_id', 'risk_score'],
    key_on='feature.properties.kecamatan_id',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='TB Risk Score'
).add_to(m)

# Add Tooltips
folium.GeoJson(
    gdf[['kecamatan_id', 'nama_kecamatan_shp', 'risk_zone', 'risk_score', 'geometry']],
    tooltip=folium.GeoJsonTooltip(fields=['nama_kecamatan_shp', 'risk_zone', 'risk_score'],
                                  aliases=['Kecamatan:', 'Risk Zone:', 'Score:'],
                                  localize=True),
    style_function=lambda x: {'color': 'transparent', 'fillColor': 'transparent'}
).add_to(m)

folium.LayerControl().add_to(m)
interactive_map_path = os.path.join(output_dir, "T308_interactive_risk_map.html")
m.save(interactive_map_path)

# 6. Save Updated GeoJSON
final_geojson_path = os.path.join(input_dir, "master_dataset_spatial_risk_2024.geojson")
gdf.to_file(final_geojson_path, driver='GeoJSON')

print(f"Epic 3 Complete! Interactive map saved at {interactive_map_path}")
print(f"Final Risk GeoJSON saved at {final_geojson_path}")
