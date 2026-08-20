from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import json
import pulp
from pathlib import Path

app = FastAPI(
    title="TB-INSIGHT Synthetic Demo API",
    description="Demonstration only. All epidemiological and operational values are synthetic.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

# Load Data
try:
    df_forecast = pd.read_csv(DATA_DIR / "forecast_results_2026.csv")
    df_master = pd.read_csv(DATA_DIR / "master_dataset_tabular_v2.csv")
    
    # Get latest capacity data per kecamatan
    df_capacity = df_master.sort_values(by=['tahun', 'bulan']).groupby('kecamatan_id').last().reset_index()
    cols_to_keep = ['kecamatan_id', 'kapasitas_skrining_per_bulan_dummy', 
                    'kapasitas_kunjungan_rumah_per_bulan_dummy', 
                    'jumlah_puskesmas_dummy', 'jumlah_rs_dummy', 'jumlah_klinik_dummy',
                    'kepadatan_penduduk_per_km2_dummy', 'persentase_kemiskinan_dummy']
    
    # Merge forecast with capacity
    df_merged = pd.merge(df_forecast, df_capacity[cols_to_keep], on='kecamatan_id', how='left')
    
    with (DATA_DIR / "master_dataset_spatial_risk_2024.geojson").open("r", encoding="utf-8") as f:
        geojson_data = json.load(f)
except Exception as e:
    print(f"Error loading data: {e}")
    df_merged = pd.DataFrame()
    geojson_data = {}

@app.get("/")
def read_root():
    return {
        "message": "TB-INSIGHT synthetic demonstration API",
        "data_status": "SYNTHETIC - NOT FOR RESEARCH OR POLICY DECISIONS",
    }

@app.get("/api/data")
def get_all_data():
    if df_merged.empty:
        raise HTTPException(status_code=404, detail="Data not found")
    return df_merged.to_dict(orient="records")

@app.get("/api/map")
def get_map():
    if not geojson_data:
        raise HTTPException(status_code=404, detail="Map data not found")
    return geojson_data

class OptimizationRequest(BaseModel):
    total_nakes_available: int
    budget_limit: int

@app.post("/api/optimize")
def optimize_resources(req: OptimizationRequest):
    if df_merged.empty:
        raise HTTPException(status_code=404, detail="Data not found")

    df_opt = df_merged.copy()
    df_opt['risk_weight'] = df_opt['avg_pred_Q1'] / df_opt['avg_pred_Q1'].max()
    kecamatan_list = df_opt['kecamatan_id'].tolist()
    
    prob = pulp.LpProblem("TB_Resource_Allocation", pulp.LpMaximize)
    nakes_vars = pulp.LpVariable.dicts("Nakes", kecamatan_list, lowBound=0, cat='Integer')
    
    prob += pulp.lpSum([nakes_vars[i] * 50 * df_opt.loc[df_opt['kecamatan_id'] == i, 'risk_weight'].values[0] for i in kecamatan_list])
    prob += pulp.lpSum([nakes_vars[i] for i in kecamatan_list]) <= req.total_nakes_available, "Total_Nakes"
    prob += pulp.lpSum([nakes_vars[i] * 5000000 for i in kecamatan_list]) <= req.budget_limit, "Total_Budget"
    
    for i in kecamatan_list:
        prob += nakes_vars[i] <= 15, f"Max_Nakes_{i}"
        
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    if pulp.LpStatus[prob.status] != 'Optimal':
        return {"status": "Failed to find optimal solution"}
        
    allocation = []
    total_assigned = 0
    total_cost = 0
    for i in kecamatan_list:
        assigned = int(nakes_vars[i].varValue)
        if assigned > 0:
            kec_name = df_opt.loc[df_opt['kecamatan_id'] == i, 'kecamatan'].values[0]
            allocation.append({
                "kecamatan_id": i,
                "kecamatan": kec_name,
                "nakes_assigned": assigned,
                "estimated_screened": assigned * 50
            })
            total_assigned += assigned
            total_cost += (assigned * 5000000)
            
    allocation = sorted(allocation, key=lambda x: x['nakes_assigned'], reverse=True)
            
    return {
        "status": "Optimal",
        "total_nakes_assigned": total_assigned,
        "total_cost": total_cost,
        "allocation": allocation
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
