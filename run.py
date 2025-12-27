import threading

from app import create_app
from app.models import create_tables
from app.monitor import monitor_loop

if __name__ == "__main__":
    create_tables()

    threading.Thread(
        target=monitor_loop,
        daemon=True
    ).start()

    app = create_app()
    app.run(host="0.0.0.0", port=8000)
