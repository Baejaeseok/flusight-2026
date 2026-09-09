import os
from flask import Flask, jsonify
import requests
import pandas as pd

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

# ============ HUMIDITY (GitHub CSV) ============
def fetch_humidity_data():
    """GitHub에서 humidity CSV 읽기"""
    try:
        url = "https://raw.githubusercontent.com/Baejaeseok/flusight-2026/main/data/humidity_2024_25.csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        print(f"[humidity] Error: {e}", flush=True)
        return None

# ============ CENSUS (GitHub CSV) ============
def fetch_census_65plus():
    """GitHub에서 census CSV 읽기"""
    try:
        url = "https://raw.githubusercontent.com/Baejaeseok/flusight-2026/main/data/census_65plus_2024.csv"
        df = pd.read_csv(url)
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
