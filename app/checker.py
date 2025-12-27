import requests

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
