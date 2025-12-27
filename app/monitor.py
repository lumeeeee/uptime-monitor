import time
from app.config import load_config
from app.checker import check_site
from app.models import insert_status_event
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
                    insert_status_event(url, status)

            elif status != existing["status"]:
                insert_status_event(url, status)

                if status == "offline":
                    mark_site_down(url, error or "unknown")

                else:
                    update_site_status(url, status, None)

            else:
                update_site_status(url, status, error)

        time.sleep(interval)
