import os
from flask import Flask, jsonify, request, Response
import requests
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import io

app = Flask(__name__)

# ============ 전역 변수 ============
NSSP_DATA = None
HUMIDITY_DATA = None
CENSUS_DATA = None
MERGED_DATA = None
MODELS = None
SCALER = None
FEATURES = None
QUANTILES = None

def init_data():
    """앱 시작 시 데이터 + 모델 수집"""
    global NSSP_DATA, HUMIDITY_DATA, CENSUS_DATA, MERGED_DATA, MODELS, SCALER, FEATURES, QUANTILES
    
    print("[init] Loading data and models...", flush=True)
    
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
    
    # 5. 모델 로드
    try:
        url = "https://raw.githubusercontent.com/Baejaeseok/flusight-2026/main/models/flusight_phase_a_models.pkl"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        model_data = pickle.loads(resp.content)
        MODELS = model_data['models']
        SCALER = model_data['scaler']
        FEATURES = model_data['features']
        QUANTILES = model_data['quantiles']
        
        print(f"[init] Models: {len(MODELS)} quantiles loaded", flush=True)
    except Exception as e:
        print(f"[init] Model loading error: {e}", flush=True)

# 앱 시작
try:
    init_data()
except Exception as e:
    print(f"[init] Error: {e}", flush=True)

# ============ ROUTES ============
@app.route("/")
def index():
    return jsonify({
        "project": "FluSight 2026",
        "phase": "A",
        "status": "active",
        "models_loaded": MODELS is not None,
        "merged_records": len(MERGED_DATA) if MERGED_DATA is not None else 0
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/test")
def test():
    """자동 테스트 (Render 배포 확인용)"""
    if MODELS is None or MERGED_DATA is None:
        return jsonify({"status": "error", "message": "Models or data not loaded"}), 500
    
    try:
        # 마지막 주 데이터로 테스트
        sample = MERGED_DATA.iloc[-1]
        
        features = [
            float(sample['lag']),
            float(sample['num_ili']),
            float(sample['num_patients']),
            float(sample['num_providers']),
            float(sample['temp_c']),
            float(sample['ah_g_m3'])
        ]
        
        X = np.array([features])
        X_scaled = SCALER.transform(X)
        
        predictions = {}
        for q_name, model in MODELS.items():
            pred = float(model.predict(X_scaled)[0])
            predictions[q_name] = round(pred, 4)
        
        return jsonify({
            "status": "ok",
            "test": "success",
            "epiweek": int(sample['epiweek']),
            "predictions": predictions,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

@app.route("/export_csv")
def export_csv():
    """NSSP + Humidity 병합 데이터를 CSV로 내보내기"""
    if MERGED_DATA is None:
        return jsonify({"error": "Merged data not available"}), 500
    
    try:
        csv_buffer = io.StringIO()
        MERGED_DATA.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=flusight_merged_data.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict", methods=['POST'])
def predict():
    """LightGBM 예측"""
    if MODELS is None or SCALER is None:
        return jsonify({"error": "Models not loaded"}), 500
    
    try:
        data = request.get_json()
        
        # 입력: lag, num_ili, num_patients, num_providers, temp_c, ah_g_m3
        features = [
            float(data['lag']),
            float(data['num_ili']),
            float(data['num_patients']),
            float(data['num_providers']),
            float(data['temp_c']),
            float(data['ah_g_m3'])
        ]
        
        X = np.array([features])
        X_scaled = SCALER.transform(X)
        
        # 7개 quantile 예측
        predictions = {}
        for q_name, model in MODELS.items():
            pred = float(model.predict(X_scaled)[0])
            predictions[q_name] = round(pred, 4)
        
        return jsonify({
            "status": "ok",
            "input": features,
            "predictions": predictions,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
