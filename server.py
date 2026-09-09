import os
from flask import Flask, jsonify
import requests
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

# ============ 초기화: 데이터 수집 ============
NSSP_DATA = None
HUMIDITY_DATA = None
CENSUS_DATA = None
MERGED_DATA = None

def init_data():
    """앱 시작 시 데이터 수집"""
    global NSSP_DATA, HUMIDITY_DATA, CENSUS_DATA, MERGED_DATA
    
    print("[init] Loading data...", flush=True)
    
    # 1. NSSP ILI
    try:
        url = "https://api.delphi.cmu.edu/epidata/fluview/"
        params = {
            "regions": "nat",
            "epiweeks": ",".join(str(w) for w in range(202432, 202532))
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") == 1 and data.get("epidata"):
            NSSP_DATA = pd.DataFrame(data["epidata"])
            print(f"[init] NSSP: {len(NSSP_DATA)} weeks", flush=True)
    except Exception as e:
        print(f"[init] NSSP error: {e}", flush=True)
    
    # 2. Humidity
    try:
        url = "https://raw.githubusercontent.com/Baejaeseok/flusight-2026/main/data/humidity_2024_25.csv"
        df_humidity_raw = pd.read_csv(url)
        df_humidity_raw['date'] = pd.to_datetime(df_humidity_raw['date'])
        df_humidity_raw['year'] = df_humidity_raw['date'].dt.isocalendar().year
        df_humidity_raw['week'] = df_humidity_raw['date'].dt.isocalendar().week
        df_humidity_raw['epiweek'] = df_humidity_raw['year'] * 100 + df_humidity_raw['week']
        
        HUMIDITY_DATA = df_humidity_raw.groupby('epiweek').agg({
            'temp_c': 'mean',
            'ah_g_m3': 'mean'
        }).reset_index()
        print(f"[init] Humidity: {len(HUMIDITY_DATA)} weeks", flush=True)
    except Exception as e:
        print(f"[init] Humidity error: {e}", flush=True)
    
    # 3. Census
    try:
        url = "https://raw.githubusercontent.com/Baejaeseok/flusight-2026/main/data/census_65plus_2024.csv"
        CENSUS_DATA = pd.read_csv(url)
        print(f"[init] Census: {len(CENSUS_DATA)} states", flush=True)
    except Exception as e:
        print(f"[init] Census error: {e}", flush=True)
    
    # 4. Merge
    if NSSP_DATA is not None and HUMIDITY_DATA is not None:
        MERGED_DATA = pd.merge(NSSP_DATA, HUMIDITY_DATA, on='epiweek', how='inner')
        print(f"[init] Merged: {len(MERGED_DATA)} weeks", flush=True)

# 앱 시작 시 데이터 로드
try:
    init_data()
except Exception as e:
    print(f"[init] Error during initialization: {e}", flush=True)

# ============ ROUTES ============
@app.route("/")
def index():
    return jsonify({
        "project": "FluSight 2026",
        "phase": "A",
        "status": "active"
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/collect")
def collect():
    try:
        url = "https://api.delphi.cmu.edu/epidata/fluview/"
        params = {
            "regions": "nat",
            "epiweeks": ",".join(str(w) for w in range(202432, 202532))
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return jsonify(resp.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/humidity")
def humidity():
    if HUMIDITY_DATA is not None:
        return jsonify({"status": "ok", "records": len(HUMIDITY_DATA)}), 200
    else:
        return jsonify({"status": "error"}), 500

@app.route("/census")
def census():
    if CENSUS_DATA is not None:
        return jsonify({"status": "ok", "records": len(CENSUS_DATA)}), 200
    else:
        return jsonify({"status": "error"}), 500

@app.route("/merged")
def merged():
    if MERGED_DATA is not None:
        return jsonify({"status": "ok", "records": len(MERGED_DATA), "columns": list(MERGED_DATA.columns)}), 200
    else:
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
