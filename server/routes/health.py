from flask import (
    Blueprint, jsonify
)

from server.controllers.health import get_server_status
health_router = Blueprint('health', __name__, url_prefix='/healthz')


# /healthz/
@health_router.route("/")
def health():
    return "This is fine!"

# /healthz/status
@health_router.route("/status")
def healthz():
    """Return health and version info for the application.

    :return: JSON response with version info.
    """

    data_health = get_server_status()
    return jsonify(
        data_health
    )
