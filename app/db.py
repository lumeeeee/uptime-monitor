import sqlite3

DB_FILE = "data/uptime.db"

def get_conn():
    return sqlite3.connect(DB_FILE)
