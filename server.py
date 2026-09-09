import os
from flask import Flask, jsonify
import requests
import sys

app = Flask(__name__)

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

def fetch_humidity_data():
    """NASA POWER API에서 절대습도 수집"""
    try:
        sys.path.insert(0, '/app/collectors')
        from humidity import fetch_humidity_data as get_humidity
        df = get_humidity()
        if df is not None:
            return {"status": "ok", "records": len(df)}
        else:
            return {"status": "error"}
    except Exception as e:
        return {"error": str(e)}

def fetch_census_65plus():
    """Census Bureau API에서 65+ 인구 수집"""
    try:
        sys.path.insert(0, '/app/collectors')
        from census import fetch_census_65plus
        df = fetch_census_65plus()
        if df is not None:
            return {"status": "ok", "records": len(df)}
        else:
            return {"status": "error"}
    except Exception as e:
        return {"error": str(e)}

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
    data = fetch_humidity_data()
    return jsonify(data), 200

@app.route("/census")
def census():
    data = fetch_census_65plus()
    return jsonify(data), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
