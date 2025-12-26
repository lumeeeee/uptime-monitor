import threading
import time
import json
import sqlite3
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template

DB_FILE = "uptime.db"
CONFIG_FILE = "sites.json"

app = Flask(__name__)

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            url TEXT PRIMARY KEY,
            status TEXT,
            last_downtime TEXT,
            last_error TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS downtime_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            timestamp TEXT,
            error TEXT
        )
        """)

    

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def check_site(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code >= 500:
            return "offline", f"HTTP {r.status_code}"
        return "online", None
    except requests.exceptions.Timeout:
        return "offline", "timeout"
    except requests.exceptions.RequestException:
        return "offline", "connection_error"

def monitor_loop():
    config = load_config()
    interval = config["check_interval_seconds"]

    while True:
        for url in config["sites"]:
            status, error = check_site(url)
            now = datetime.now(timezone.utc).isoformat()
            if status == "offline":
                conn = sqlite3.connect(DB_FILE)
                conn.execute(
                "INSERT INTO downtime_log (url, timestamp, error) VALUES (?, ?, ?)",
                (url, now, error)
                )
                conn.commit()
                conn.close()


            with sqlite3.connect(DB_FILE) as conn:
                cur = conn.cursor()
                cur.execute("SELECT status FROM sites WHERE url=?", (url,))
                row = cur.fetchone()

                if row is None:
                    cur.execute(
                        "INSERT INTO sites VALUES (?, ?, ?, ?)",
                        (url, status, None, error)
                    )
                else:
                    if status == "offline" and row[0] == "online":
                        cur.execute(
                            "UPDATE sites SET status=?, last_downtime=?, last_error=? WHERE url=?",
                            (status, now, error, url)
                        )
                    else:
                        cur.execute(
                            "UPDATE sites SET status=?, last_error=? WHERE url=?",
                            (status, error, url)
                        )

        time.sleep(interval)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM sites").fetchall()
        return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    init_db()
    threading.Thread(target=monitor_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)

@app.route("/api/downtime-log")
def api_downtime_log():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT url, timestamp, error
            FROM downtime_log
            ORDER BY id DESC
            LIMIT 30
        """).fetchall()

        return jsonify([dict(r) for r in rows])
