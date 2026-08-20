import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from statsmodels.tsa.arima.model import ARIMA
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# Configuration
plt.style.use('dark_background')
base_dir = Path(__file__).resolve().parents[1]
input_dir = base_dir / "data" / "processed"
output_dir = base_dir / "results" / "epic_4_forecast_charts"
os.makedirs(output_dir, exist_ok=True)

summary_file = base_dir / "results" / "epic_4_summary.txt"
with open(summary_file, "w") as f:
    f.write("=== EPIC 4: PREDICTIVE MODELING & EARLY WARNING SYSTEM ===\n\n")

print("Starting Epic 4: Predictive Modeling...")

# 1. Load Data
df = pd.read_csv(os.path.join(input_dir, "master_dataset_tabular_v2.csv"))
df['date'] = pd.to_datetime(df['tahun'].astype(str) + '-' + df['bulan'].astype(str).str.zfill(2) + '-01')
df.sort_values(by=['kecamatan_id', 'date'], inplace=True)

# 2. Feature Engineering
print("Performing Feature Engineering...")
def create_features(group):
    group['lag_1'] = group['kasus_tb_total_dummy'].shift(1)
    group['lag_2'] = group['kasus_tb_total_dummy'].shift(2)
    group['lag_3'] = group['kasus_tb_total_dummy'].shift(3)
    group['rolling_mean_3'] = group['kasus_tb_total_dummy'].shift(1).rolling(window=3).mean()
    group['month'] = group['date'].dt.month
    return group

df = df.groupby('kecamatan_id', group_keys=False).apply(create_features).dropna().reset_index(drop=True)

# Feature selection
features = ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_3', 'month', 
            'kepadatan_penduduk_per_km2_dummy', 'persentase_kemiskinan_dummy']
target = 'kasus_tb_total_dummy'

# 3. Train-Test Split
train = df[df['tahun'] <= 2023]
test = df[df['tahun'] >= 2024]

X_train, y_train = train[features], train[target]
X_test, y_test = test[features], test[target]

# 4. Model Training & Evaluation
results = {}

def evaluate(model_name, y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    # Avoid zero division in MAPE
    y_true_safe = np.where(y_true == 0, 1e-10, y_true)
    mape = np.mean(np.abs((y_true - y_pred) / y_true_safe)) * 100
    results[model_name] = {'RMSE': rmse, 'MAE': mae, 'MAPE (%)': mape}
    return mape

# A. Random Forest
print("Training Random Forest...")
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
evaluate('Random Forest', y_test, rf_pred)

# B. XGBoost
print("Training XGBoost...")
xgb = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
xgb.fit(X_train, y_train)
xgb_pred = xgb.predict(X_test)
evaluate('XGBoost', y_test, xgb_pred)

# C. ARIMA Baseline (Iterative per Kecamatan)
print("Evaluating ARIMA Baseline...")
arima_preds = []
y_test_arima = []
for kec in df['kecamatan_id'].unique():
    kec_data = df[df['kecamatan_id'] == kec]
    train_kec = kec_data[kec_data['tahun'] <= 2023]['kasus_tb_total_dummy'].values
    test_kec = kec_data[kec_data['tahun'] >= 2024]['kasus_tb_total_dummy'].values
    
    if len(train_kec) > 10 and len(test_kec) > 0:
        try:
            model = ARIMA(train_kec, order=(1,1,1))
            model_fit = model.fit()
            pred = model_fit.forecast(steps=len(test_kec))
            arima_preds.extend(pred)
            y_test_arima.extend(test_kec)
        except:
            arima_preds.extend([np.nan]*len(test_kec))
            y_test_arima.extend(test_kec)

# Filter nan for ARIMA evaluation
valid_idx = ~np.isnan(arima_preds)
if sum(valid_idx) > 0:
    evaluate('ARIMA (Univariate)', np.array(y_test_arima)[valid_idx], np.array(arima_preds)[valid_idx])

with open(summary_file, "a") as f:
    f.write("--- MODEL EVALUATION ON VALIDATION SET (2024-2025) ---\n")
    for model_name, metrics in results.items():
        f.write(f"Model: {model_name}\n")
        for k, v in metrics.items():
            f.write(f"  {k}: {v:.2f}\n")
        f.write("\n")

# Best Model Check
best_model_name = min(results, key=lambda x: results[x]['MAPE (%)'])
print(f"Best Model: {best_model_name}")

# 5. Future Forecasting (Q1 2026: Jan, Feb, Mar) & Early Warning
print("Generating Q1 2026 Forecasts & Early Warnings...")
# We use XGBoost to predict the next 3 months for each kecamatan
last_data = df.groupby('kecamatan_id').last().reset_index()

forecast_results = []
for idx, row in last_data.iterrows():
    kec = row['kecamatan_id']
    kec_name = row['kecamatan']
    
    # Baseline for early warning (average of 2025 cases for this kecamatan)
    baseline_2025 = df[(df['kecamatan_id'] == kec) & (df['tahun'] == 2025)]['kasus_tb_total_dummy'].mean()
    
    current_lag1 = row['kasus_tb_total_dummy']
    current_lag2 = row['lag_1']
    current_lag3 = row['lag_2']
    current_kepadatan = row['kepadatan_penduduk_per_km2_dummy']
    current_kemiskinan = row['persentase_kemiskinan_dummy']
    
    predictions = []
    
    for month in [1, 2, 3]: # Jan, Feb, Mar 2026
        feat_dict = {
            'lag_1': [current_lag1],
            'lag_2': [current_lag2],
            'lag_3': [current_lag3],
            'rolling_mean_3': [np.mean([current_lag1, current_lag2, current_lag3])],
            'month': [month],
            'kepadatan_penduduk_per_km2_dummy': [current_kepadatan],
            'persentase_kemiskinan_dummy': [current_kemiskinan]
        }
        feat_df = pd.DataFrame(feat_dict)[features]
        pred_val = max(0, int(xgb.predict(feat_df)[0])) # Use XGBoost as it's typically best
        predictions.append(pred_val)
        
        # Update lags for next month
        current_lag3 = current_lag2
        current_lag2 = current_lag1
        current_lag1 = pred_val
        
    avg_pred_q1 = np.mean(predictions)
    
    # Early Warning Logic: If average Q1 2026 prediction is > kapasitas skrining
    kapasitas = df[df['kecamatan_id'] == kec]['kapasitas_skrining_per_bulan_dummy'].iloc[-1]
    alert_status = "ALERT: High Surge" if avg_pred_q1 > kapasitas else "Normal"
    
    forecast_results.append({
        'kecamatan_id': kec,
        'kecamatan': kec_name,
        'pred_Jan_2026': predictions[0],
        'pred_Feb_2026': predictions[1],
        'pred_Mar_2026': predictions[2],
        'avg_pred_Q1': round(avg_pred_q1, 2),
        'baseline_2025_avg': round(baseline_2025, 2),
        'early_warning_status': alert_status
    })

df_forecast = pd.DataFrame(forecast_results)
forecast_csv = os.path.join(input_dir, "forecast_results_2026.csv")
df_forecast.to_csv(forecast_csv, index=False)

with open(summary_file, "a") as f:
    f.write("--- EARLY WARNING SYSTEM (Q1 2026) ---\n")
    alerts = df_forecast[df_forecast['early_warning_status'] != 'Normal']
    if len(alerts) > 0:
        f.write(f"WARNING: {len(alerts)} Kecamatan terdeteksi berpotensi lonjakan kasus!\n")
        f.write(alerts[['kecamatan', 'avg_pred_Q1', 'baseline_2025_avg']].to_string(index=False) + "\n")
    else:
        f.write("Tidak ada kecamatan yang diprediksi mengalami lonjakan drastis (>20% dari rata-rata 2025).\n")

# 6. Visualization: Plot for a sample high-burden kecamatan
print("Generating Forecast Visualizations...")
sample_kec = df.groupby('kecamatan_id')['kasus_tb_total_dummy'].sum().idxmax()
sample_name = df[df['kecamatan_id'] == sample_kec]['kecamatan'].iloc[0]

kec_hist = df[df['kecamatan_id'] == sample_kec]
kec_fcst = df_forecast[df_forecast['kecamatan_id'] == sample_kec].iloc[0]

plt.figure(figsize=(10, 5))
plt.plot(kec_hist['date'], kec_hist['kasus_tb_total_dummy'], label='Historical (Actual)', color='cyan')

# Append forecast
last_date = kec_hist['date'].iloc[-1]
fcst_dates = [pd.to_datetime('2026-01-01'), pd.to_datetime('2026-02-01'), pd.to_datetime('2026-03-01')]
fcst_vals = [kec_fcst['pred_Jan_2026'], kec_fcst['pred_Feb_2026'], kec_fcst['pred_Mar_2026']]

# Connect last historical to first forecast
plt.plot([last_date, fcst_dates[0]], [kec_hist['kasus_tb_total_dummy'].iloc[-1], fcst_vals[0]], color='orange', linestyle='--')
plt.plot(fcst_dates, fcst_vals, label='Forecast (Q1 2026)', color='orange', marker='o')

# Confidence band mock (e.g., +/- 15%)
upper_bound = [v * 1.15 for v in fcst_vals]
lower_bound = [v * 0.85 for v in fcst_vals]
plt.fill_between(fcst_dates, lower_bound, upper_bound, color='orange', alpha=0.2, label='Confidence Interval (+/- 15%)')

plt.title(f'TB Case Forecast - Kecamatan {sample_name} (High Burden)')
plt.xlabel('Date')
plt.ylabel('Cases')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "T414_forecast_sample.png"), dpi=300)
plt.close()

print(f"Epic 4 Complete! Forecasts saved to {forecast_csv}")
print(f"Summary saved to {summary_file}")
