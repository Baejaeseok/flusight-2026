import os
from flask import Flask, jsonify
import requests
import pandas as pd
import numpy as np

app = Flask(__name__)

# ============ FLUVIEW (NSSP ILI) ============
def fetch_fluview_data():
    """Delphi Epidata API로 ILI 데이터 수집"""
    try:
        url = "https://api.delphi.cmu.edu/epidata/fluview/"
        params = {
            "regions": "nat",
            "epiweeks": ",".join(str(w) for w in range(202432, 202532))
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# ============ HUMIDITY (NASA POWER) ============
def fetch_humidity_data():
    """NASA POWER API에서 온도와 습도 데이터 수집, 절대습도 계산"""
    try:
        url = "https://power.larc.nasa.gov/api/v1/aggregate"
        
        params = {
            "longitude": -95.7129,
            "latitude": 37.0902,
            "start": 20240801,
            "end": 20250831,
            "community": "RE",
            "parameters": "T2M,RH2M",
            "format": "JSON"
        }
        
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        
        if "properties" not in data or "parameter" not in data["properties"]:
            return None
        
        params_data = data["properties"]["parameter"]
        temps = params_data.get("T2M", {})
        humids = params_data.get("RH2M", {})
        
        if not temps or not humids:
            return None
        
        records = []
        for date_str in sorted(temps.keys()):
            if date_str in humids:
                T = temps[date_str]
                RH = humids[date_str]
                
                exp_term = np.exp((17.67 * T) / (T + 243.5))
                AH = (RH / 100) * (6.112 * exp_term) / (461.5 * (T + 273.15))
                
                records.append({
                    "date": date_str,
                    "temp_c": T,
                    "rh_percent": RH,
                    "ah_g_m3": AH
                })
        
        df = pd.DataFrame(records)
        return df
        
    except Exception as e:
        print(f"[humidity] Error: {e}", flush=True)
        return None

# ============ CENSUS (65+ POPULATION) ============
def fetch_census_65plus():
    """Census Bureau ACS 2024 65+ 인구 수집"""
    try:
        url = "https://api.census.gov/data/2024/acs/acs5"
        
        states = ",".join(str(i).zfill(2) for i in range(1, 57))
        
        params = {
            "get": "B01003_001E,B01003_026E",
            "for": f"state:{states}",
            "key": "678f50449febdaa20ff97994defc563e6e0bb220"
        }
        
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        
        if not data or len(data) < 2:
            return None
        
        header = data[0]
        rows = data[1:]
        
        records = []
        for row in rows:
            try:
                state_fips = row[2]
                total_pop = int(row[0])
                pop_65plus = int(row[1])
                pct_65plus = (pop_65plus / total_pop * 100) if total_pop > 0 else 0
                
                records.append({
                    "state_fips": state_fips,
                    "total_pop": total_pop,
                    "pop_65plus": pop_65plus,
                    "pct_65plus": round(pct_65plus, 2)
                })
            except (ValueError, IndexError):
                continue
        
        df = pd.DataFrame(records)
        return df
        
    except Exception as e:
        print(f"[census] Error: {e}", flush=True)
        return None

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
    data = fetch_fluview_data()
    return jsonify(data), 200

@app.route("/humidity")
def humidity():
    df = fetch_humidity_data()
    if df is not None:
        return jsonify({"status": "ok", "records": len(df)}), 200
    else:
        return jsonify({"status": "error"}), 500

@app.route("/census")
def census():
    df = fetch_census_65plus()
    if df is not None:
        return jsonify({"status": "ok", "records": len(df)}), 200
    else:
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
