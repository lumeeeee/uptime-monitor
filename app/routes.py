from flask import jsonify, render_template
from app.models import get_all_sites, get_last_downtimes


def register_routes(app):

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/status")
    def api_status():
        sites = get_all_sites()
        return jsonify(sites)

    @app.route("/api/downtime-log")
    def api_downtime_log():
        log = get_last_downtimes()
        return jsonify(log)
