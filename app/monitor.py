import time
from app.config import load_config
from app.checker import check_site
from app.models import insert_status_event
from app.models import (
    get_site,
    insert_site,
    update_site_status,
    mark_site_down,
    insert_status_event,
    start_incident,
    close_incident,
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

                if status == "offline":
                    start_incident(url)
                    mark_site_down(url, error or "unknown")

                continue

            prev_status = existing["status"]

            # ONLINE - OFFLINE 
            if prev_status == "online" and status == "offline":
                start_incident(url)
                mark_site_down(url, error or "unknown")
                insert_status_event(url, "offline")

            # OFFLINE - ONLINE
            elif prev_status == "offline" and status == "online":
                close_incident(url)
                insert_status_event(url, "online")

            # Обновляем текущее состояние
            update_site_status(
                url,
                status,
                error if status == "offline" else None
            )

        time.sleep(interval)

