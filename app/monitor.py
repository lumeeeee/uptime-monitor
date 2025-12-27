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
    update_fail_count,
)


def monitor_loop():
    config = load_config()
    threshold = config.get("failure_threshold", 1)
    interval = config["check_interval_seconds"]
    sites = config["sites"]

    while True:
        for url in sites:
            status, error = check_site(url)
            existing = get_site(url)
            
            if not existing:
                insert_site(url, "online", None)
                existing = get_site(url)
            
            current_fail_count = existing["fail_count"] or 0
            prev_status = existing["status"]

            # --- OFFLINE ---
            if status == "offline":
                new_fail_count = current_fail_count + 1
                update_fail_count(url, new_fail_count)

                # старт инцидента ТОЛЬКО при достижении threshold
                if prev_status == "online" and new_fail_count >= threshold:
                    start_incident(url)
                    mark_site_down(url, error or "unknown")
                    insert_status_event(url, "offline")

                update_site_status(url, "offline", error)

            # --- ONLINE ---
            else:
                # если сайт восстановился — закрываем инцидент
                if prev_status == "offline":
                    close_incident(url)
                    insert_status_event(url, "online")

                # сбрасываем счётчик
                update_fail_count(url, 0)
                update_site_status(url, "online", None)

        time.sleep(interval)

