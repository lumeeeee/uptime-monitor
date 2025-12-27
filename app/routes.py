from flask import jsonify, render_template
from .db import get_conn
from .models import get_all_sites, get_last_downtimes

def register_routes(app):

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/status")
    def api_status():
        ...
