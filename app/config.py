import json

CONFIG_FILE = "data/sites.json"

def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)
