import requests
import pandas as pd

def fetch_census_65plus():
    """
    US Census Bureau ACS 2024 65+ population by state
    API 키 필수 (무료 발급)
    """
    try:
        # Census API
        url = "https://api.census.gov/data/2024/acs/acs5"
        
        # 모든 주 FIPS 코드 (01~56)
        states = ",".join(str(i).zfill(2) for i in range(1, 57))
        
        params = {
            "get": "B01003_001E,B01003_026E",  # 총 인구, 65+ 인구
            "for": f"state:{states}",
            "key": "678f50449febdaa20ff97994defc563e6e0bb220"
        }
        
        print("[census] Fetching ACS 2024 data...", flush=True)
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        
        if not data or len(data) < 2:
            print("[census] No data returned", flush=True)
            return None
        
        # 헤더와 행 분리
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
        print(f"[census] Fetched {len(df)} states", flush=True)
        return df
        
    except Exception as e:
        print(f"[census] Error: {e}", flush=True)
        return None

def main():
    print("[census] Starting Census 65+ data collection", flush=True)
    df = fetch_census_65plus()
    
    if df is not None:
        df.to_csv("/tmp/census_65plus_2024.csv", index=False)
        print(f"[census] Saved to /tmp/census_65plus_2024.csv", flush=True)
        return {"status": "ok", "records": len(df)}
    else:
        return {"status": "error"}

if __name__ == "__main__":
    main()
