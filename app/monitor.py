import time
from app.config import load_config
from app.checker import check_site
from app.models import (
    get_site,
    insert_site,
    update_site_status,
    mark_site_down,
)

def monitor_loop():
    config = load_config()
    interval = config["check_interval_seconds"]
    sites = config["sites"]

    while True:
        for url in sites:
            status, error = check_site(url)

            existing = get_site(url)

            if existing is None:
                insert_site(url, status, error)

            elif status == "offline" and existing["status"] == "online":
                mark_site_down(url, error or "unknown")

            else:
                update_site_status(url, status, error)

        time.sleep(interval)
