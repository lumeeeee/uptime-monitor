import threading
from app import create_app
from app.db import init_db
from app.monitor import monitor_loop

if __name__ == "__main__":
    init_db()
    threading.Thread(target=monitor_loop, daemon=True).start()

    app = create_app()
    app.run(host="0.0.0.0", port=8000)
