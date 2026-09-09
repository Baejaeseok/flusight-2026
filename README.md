# FluSight 2026

CDC Influenza Forecast Challenge

## Phase A (Sep-Oct)
- Data: NSSP ED ILI%, Absolute Humidity, Census 65+
- Model: LightGBM (7 quantiles)
- Goal: WIS < 1.1 (baseline < 0.65)

## Setup
```
pip install -r requirements.txt
python server.py
```

Deployment: Render (Auto-Deploy on push)
