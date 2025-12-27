import requests
from datetime import datetime, timezone
from app.db import get_conn

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
TIMEOUT = 5


def get_alert_settings(url: str):
    with get_conn() as conn:
        conn.row_factory = lambda c, r: {col[0]: r[i] for i, col in enumerate(c.description)}
        return conn.execute(
            "SELECT * FROM alert_settings WHERE url = ? AND enabled = 1",
            (url,)
        ).fetchone()


def already_sent(url: str, alert_type: str, incident_id: int):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM alert_log
            WHERE url = ? AND type = ? AND incident_id = ?
            """,
            (url, alert_type, incident_id)
        ).fetchone()
        return row is not None


def log_alert(url: str, alert_type: str, incident_id: int):
    ts = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO alert_log (url, type, incident_id, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (url, alert_type, incident_id, ts)
        )


def send_message(token: str, chat_id: str, text: str):
    try:
        requests.post(
            TELEGRAM_API.format(token=token),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=TIMEOUT
        )
    except Exception:
        # alerting не должен ломать мониторинг
        pass


def send_offline(url: str, error: str, incident_id: int, token: str):
    settings = get_alert_settings(url)
    if not settings:
        return

    if already_sent(url, "offline", incident_id):
        return

    text = (
        "❌ <b>Сайт недоступен</b>\n\n"
        f"<b>URL:</b> {url}\n"
        f"<b>Ошибка:</b> {error}\n"
        f"<b>Incident ID:</b> {incident_id}"
    )

    send_message(token, settings["telegram_chat_id"], text)
    log_alert(url, "offline", incident_id)


def send_recovery(url: str, duration: int, incident_id: int, token: str):
    settings = get_alert_settings(url)
    if not settings:
        return

    if already_sent(url, "recovery", incident_id):
        return

    minutes = duration // 60
    seconds = duration % 60

    text = (
        "✅ <b>Сайт восстановлен</b>\n\n"
        f"<b>URL:</b> {url}\n"
        f"<b>Downtime:</b> {minutes}м {seconds}с\n"
        f"<b>Incident ID:</b> {incident_id}"
    )

    send_message(token, settings["telegram_chat_id"], text)
    log_alert(url, "recovery", incident_id)
