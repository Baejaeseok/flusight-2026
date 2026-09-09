import requests
import pandas as pd

def fetch_nssp_data():
    """Delphi Epidata API로 NSSP ILI 데이터 수집 (전국)"""
    try:
        url = "https://api.delphi.cmu.edu/epidata/fluview/"
        epiweeks = ",".join(str(w) for w in range(202432, 202532))
        
        params = {
            "regions": "nat",
            "epiweeks": epiweeks
        }
        
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("result") == 1 and data.get("epidata"):
            df = pd.DataFrame(data["epidata"])
            return df
        else:
            print(f"Error: {data}")
            return None
            
    except Exception as e:
        print(f"[flusight_features] Error: {e}")
        return None

def main():
    print("[flusight_features] Starting NSSP data collection")
    df = fetch_nssp_data()
    
    if df is not None:
        print(f"[flusight_features] Fetched {len(df)} records")
        df.to_csv("/tmp/nssp_data.csv", index=False)
        print("[flusight_features] Saved to /tmp/nssp_data.csv")
        return {"status": "ok", "records": len(df)}
    else:
        return {"status": "error"}

if __name__ == "__main__":
    main()
