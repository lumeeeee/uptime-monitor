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

# ---------- DB ----------

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
        conn.execute("""
        CREATE TABLE IF NOT EXISTS site_notifications (
            url TEXT PRIMARY KEY,
            telegram_chat_id TEXT
        )
        """)


# ---------- CONFIG ----------

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- CHECK ----------

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

# ---------- MONITOR LOOP ----------

def monitor_loop():
    config = load_config()
    interval = config["check_interval_seconds"]

    print(f"[MONITOR] started, interval = {interval} seconds")

    while True:
        cycle_time = datetime.now(timezone.utc).isoformat()
        print(f"[MONITOR] check cycle started at {cycle_time}")

        for url in config["sites"]:
            status, error = check_site(url)
            now = datetime.now(timezone.utc).isoformat()

            with sqlite3.connect(DB_FILE) as conn:
                cur = conn.cursor()

                cur.execute("SELECT status FROM sites WHERE url=?", (url,))
                row = cur.fetchone()

                # first time
                if row is None:
                    cur.execute(
                        "INSERT INTO sites VALUES (?, ?, ?, ?)",
                        (url, status, None, error)
                    )

                # transition online -> offline
                elif status == "offline" and row[0] == "online":
                    cur.execute(
                    "UPDATE sites SET status=?, last_downtime=?, last_error=? WHERE url=?",
                    (status, now, error, url)
                    )

                # normal update
                else:
                    cur.execute(
                        "UPDATE sites SET status=?, last_error=? WHERE url=?",
                        (status, error, url)
                )

                # LOG EVERY OFFLINE CHECK
                if status == "offline" and row and row[0] == "online":
                     cur.execute(
                        "INSERT INTO downtime_log (url, timestamp, error) VALUES (?, ?, ?)",
                         (url, now, error)
                    )
                     
                conn.commit()
    
    

        print(f"[MONITOR] check cycle finished, sleeping {interval} seconds\n")
        time.sleep(interval)

# ---------- ROUTES ----------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM sites").fetchall()
        return jsonify([dict(r) for r in rows])

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

# ---------- START ----------

if __name__ == "__main__":
    init_db()
    threading.Thread(target=monitor_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)

import requests

TELEGRAM_TOKEN = "PASTE_BOT_TOKEN_HERE"

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })
