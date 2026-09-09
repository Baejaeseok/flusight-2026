import subprocess, sys
try:
    import epidatr
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'epidatr', '-q'], stderr=subprocess.DEVNULL)

def main():
    import epidatr
    import pandas as pd
    epiweeks = list(range(202432, 202532))
    nat = epidatr.fluview(regions="nat", epiweeks=epiweeks)
    print(f"[NSSP] Fetched {len(nat)} weeks (national)")
    nat.to_csv("/tmp/nssp_data.csv", index=False)
    return {"records": len(nat), "path": "/tmp/nssp_data.csv"}

if __name__ == "__main__":
    main()
