import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from pathlib import Path

# Configuration
plt.style.use('dark_background') # Better for modern dashboard look
sns.set_theme(style="darkgrid")
base_dir = Path(__file__).resolve().parents[1]
input_dir = base_dir / "data" / "processed"
output_dir = base_dir / "results" / "epic_2_eda_charts"
os.makedirs(output_dir, exist_ok=True)

summary_file = base_dir / "results" / "epic_2_summary.txt"

with open(summary_file, "w") as f:
    f.write("=== EPIC 2: EDA & RISK FACTOR ANALYSIS SUMMARY ===\n\n")

print("Starting Epic 2 EDA...")

# 1. Load Data
df = pd.read_csv(os.path.join(input_dir, "master_dataset_tabular.csv"))
gdf = gpd.read_file(os.path.join(input_dir, "batas_kecamatan_wgs84.geojson"))

# Aggregate data by kecamatan for static mapping/correlation
df_agg = df.groupby('kecamatan_id').agg({
    'kasus_tb_total_dummy': 'sum',
    'kasus_tb_anak_dummy': 'sum',
    'tb_dm_agregat_dummy': 'sum',
    'tb_hiv_agregat_dummy': 'sum',
    'kepadatan_penduduk_per_km2_dummy': 'mean',
    'persentase_kemiskinan_dummy': 'mean',
    'akses_sanitasi_layak_persen_dummy': 'mean'
}).reset_index()

# 2. T-202: Tren Waktu Kasus TB (Time Series Plot)
plt.figure(figsize=(12, 6))
df_time = df.groupby(['tahun', 'bulan'])['kasus_tb_total_dummy'].sum().reset_index()
df_time['date'] = pd.to_datetime(df_time['tahun'].astype(str) + '-' + df_time['bulan'].astype(str) + '-01')
sns.lineplot(data=df_time, x='date', y='kasus_tb_total_dummy', color='cyan', linewidth=2)
plt.title('Tren Kasus TB Bulanan di Surabaya (2015-2025)')
plt.xlabel('Waktu')
plt.ylabel('Total Kasus')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "T202_time_series_trend.png"), dpi=300)
plt.close()

# 3. T-203: Distribusi Spasial (Choropleth Map)
gdf_map = gdf.merge(df_agg, on='kecamatan_id', how='left')
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
gdf_map.plot(column='kasus_tb_total_dummy', ax=ax, legend=True, 
             cmap='YlOrRd', edgecolor='0.8',
             legend_kwds={'label': "Total Kasus TB", 'orientation': "horizontal"})
plt.title('Peta Distribusi Kasus TB per Kecamatan Surabaya')
ax.axis('off')
plt.savefig(os.path.join(output_dir, "T203_choropleth_map.png"), dpi=300)
plt.close()

# 4. T-204: Komorbiditas (TB + DM, TB + HIV)
comorbid = df[['kasus_tb_total_dummy', 'tb_dm_agregat_dummy', 'tb_hiv_agregat_dummy']].sum()
plt.figure(figsize=(8, 6))
comorbid_data = pd.DataFrame({'Tipe': ['Total TB', 'TB + DM', 'TB + HIV'], 'Jumlah': comorbid.values})
sns.barplot(data=comorbid_data, x='Tipe', y='Jumlah', palette=['#1f77b4', '#ff7f0e', '#d62728'])
plt.title('Proporsi Komorbiditas Kasus TB')
for i, v in enumerate(comorbid_data['Jumlah']):
    plt.text(i, v + (v*0.02), str(int(v)), ha='center')
plt.savefig(os.path.join(output_dir, "T204_comorbidity.png"), dpi=300)
plt.close()

# 5. T-205: Profiling High-burden vs Low-burden
df_agg_sorted = df_agg.sort_values('kasus_tb_total_dummy', ascending=False)
top5 = df_agg_sorted.head(5)
bottom5 = df_agg_sorted.tail(5)

with open(summary_file, "a") as f:
    f.write("--- T-205: HIGH-BURDEN KECAMATAN (TOP 5) ---\n")
    f.write(top5.to_string(index=False) + "\n\n")
    f.write("--- T-205: LOW-BURDEN KECAMATAN (BOTTOM 5) ---\n")
    f.write(bottom5.to_string(index=False) + "\n\n")

# 6. T-206 - T-208: Uji Korelasi Pearson & Heatmap
vars_to_corr = ['kasus_tb_total_dummy', 'kepadatan_penduduk_per_km2_dummy', 
                'persentase_kemiskinan_dummy', 'akses_sanitasi_layak_persen_dummy']
corr_matrix = df_agg[vars_to_corr].corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
plt.title('Heatmap Korelasi Kasus TB dan Faktor Sosio-Ekonomi')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "T206_correlation_heatmap.png"), dpi=300)
plt.close()

with open(summary_file, "a") as f:
    f.write("--- T-206 sd T-208: CORRELATION MATRIX ---\n")
    f.write(corr_matrix.to_string() + "\n\n")

# Scatter plots for correlations
for var in vars_to_corr[1:]:
    plt.figure(figsize=(6, 5))
    sns.regplot(data=df_agg, x=var, y='kasus_tb_total_dummy', scatter_kws={'alpha':0.5}, line_kws={'color':'red'})
    plt.title(f'Korelasi TB vs {var.replace("_dummy", "")}')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"T207_scatter_{var}.png"), dpi=300)
    plt.close()

# 7. T-209: Multiple Linear Regression (OLS)
X = df_agg[['kepadatan_penduduk_per_km2_dummy', 'persentase_kemiskinan_dummy', 'akses_sanitasi_layak_persen_dummy']]
y = df_agg['kasus_tb_total_dummy']
X_sm = sm.add_constant(X)
model = sm.OLS(y, X_sm).fit()

with open(summary_file, "a") as f:
    f.write("--- T-209: MULTIPLE LINEAR REGRESSION (OLS) ---\n")
    f.write(model.summary().as_text() + "\n\n")

# 8. T-210: Feature Importance (Random Forest)
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X, y)
importances = rf.feature_importances_
feat_df = pd.DataFrame({'Feature': X.columns, 'Importance': importances}).sort_values('Importance', ascending=False)

plt.figure(figsize=(8, 4))
sns.barplot(data=feat_df, x='Importance', y='Feature', palette='viridis')
plt.title('Feature Importance (Random Forest)')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "T210_feature_importance.png"), dpi=300)
plt.close()

with open(summary_file, "a") as f:
    f.write("--- T-210: FEATURE IMPORTANCE ---\n")
    f.write(feat_df.to_string(index=False) + "\n\n")

print(f"Epic 2 EDA Complete! Charts saved to {output_dir}")
print(f"Summary report saved to {summary_file}")
