ALTER TABLE downtime_log ADD COLUMN incident_id INTEGER;
ALTER TABLE sites ADD COLUMN fail_count INTEGER DEFAULT 0;
CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    error TEXT,            
    timestamp TEXT NOT NULL
);