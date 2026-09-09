import requests
import pandas as pd
import numpy as np
from datetime import datetime

def fetch_humidity_data():
    """
    NASA POWER API에서 온도와 습도 데이터 수집
    절대습도(Absolute Humidity, g/m³) 계산
    """
    try:
        # NASA POWER API (미국 전국 평균)
        url = "https://power.larc.nasa.gov/api/v1/aggregate"
        
        params = {
            "longitude": -95.7129,  # 미국 중부
            "latitude": 37.0902,    # 미국 중부
            "start": 20240801,      # 2024-08-01
            "end": 20250831,        # 2025-08-31
            "community": "RE",
            "parameters": "T2M,RH2M",
            "format": "JSON"
        }
        
        print("[humidity] Fetching NASA POWER data...", flush=True)
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        
        if "properties" not in data or "parameter" not in data["properties"]:
            print(f"[humidity] Error: {data}", flush=True)
            return None
        
        # 데이터 파싱
        params_data = data["properties"]["parameter"]
        temps = params_data.get("T2M", {})  # Temperature (Celsius)
        humids = params_data.get("RH2M", {})  # Relative Humidity (%)
        
        if not temps or not humids:
            print("[humidity] No temperature or humidity data", flush=True)
            return None
        
        # 절대습도 계산
        records = []
        for date_str in sorted(temps.keys()):
            if date_str in humids:
                T = temps[date_str]  # Celsius
                RH = humids[date_str]  # %
                
                # 절대습도 (g/m³)
                # AH = (RH/100) * (6.112 * exp((17.67*T)/(T+243.5))) / (461.5*(T+273.15))
                exp_term = np.exp((17.67 * T) / (T + 243.5))
                AH = (RH / 100) * (6.112 * exp_term) / (461.5 * (T + 273.15))
                
                records.append({
                    "date": date_str,
                    "temp_c": T,
                    "rh_percent": RH,
                    "ah_g_m3": AH
                })
        
        df = pd.DataFrame(records)
        print(f"[humidity] Fetched {len(df)} days", flush=True)
        return df
        
    except Exception as e:
        print(f"[humidity] Error: {e}", flush=True)
        return None

def main():
    print("[humidity] Starting humidity data collection", flush=True)
    df = fetch_humidity_data()
    
    if df is not None:
        df.to_csv("/tmp/humidity_data.csv", index=False)
        print(f"[humidity] Saved to /tmp/humidity_data.csv", flush=True)
        return {"status": "ok", "records": len(df)}
    else:
        return {"status": "error"}

if __name__ == "__main__":
    main()
