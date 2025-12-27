# Uptime Monitor — Architecture

## 1. Overview

Website accessibility monitoring.
- Web (Flask)
- Monitoring (background worker)
- Data (SQLite)

## 2. Directory Structure

```text
uptime-monitor/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── routes.py          # HTTP routes (API + pages)
│   ├── monitor.py         # Background monitoring loop
│   ├── checker.py         # HTTP availability checks
│   ├── models.py          # DB access layer (SQL, dict results)
│   ├── db.py              # DB connection helpers
│   ├── config.py          # Runtime configuration (sites.json)
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── style.css
│
├── data/
│   ├── uptime.db          # SQLite database
│   └── sites.json         # Monitored sites + settings
│
├── run.py                 # Application entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── ARCHITECTURE.md
└── README.md
