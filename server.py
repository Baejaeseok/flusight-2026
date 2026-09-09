import os, sys, subprocess
try:
    import epidatr
except ImportError:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'epidatr', '-q'], stderr=subprocess.DEVNULL)
        print("[startup] epidatr installed", flush=True)
    except Exception as e:
        print(f"[startup] install failed: {e}", flush=True)

from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"project": "FluSight 2026", "phase": "A", "status": "active"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
