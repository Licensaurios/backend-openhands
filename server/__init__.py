import importlib
import logging
import os
import sys

from authlib.integrations.flask_client import OAuth
from configobj import ConfigObj
from flask import Flask, jsonify, redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
    auth_required,
    current_user,
)
from werkzeug.middleware.proxy_fix import ProxyFix

from server.db.model import Role, User, db
from server.routes.auth import auth_router
from server.routes.health import health_router
from server.controllers.authentication import authlib_fetch_token, authlib_token_update

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

__all__ = ["app", "init_webapp"]


app = Flask(__name__)

app.register_blueprint(auth_router)
app.register_blueprint(health_router)


@app.cli.command()
def version() -> None:
    """Print the current version of server.

    :return: None

    """
    _version = importlib.metadata.version("server")
    print(f"server v{{_version}}")


def init_webapp(config_path: str, test: bool = False) -> Flask:
    """Initialize the web application.

    Initializes and configures the Flask web application. Call this method to
    make the web application and respective database engine usable.

    If initialized with `test=True` the application will use an in-memory
    SQLite database, and should be used for unit testing, but not much else.

    :param config_path: The path to the ConfigObj configuration file.
    :param test: True if should initialize the webapp for testing (use
        in-memory database).
    :return: The initialized Flask app instance.
    :raises OSError: If the configuration file cannot be loaded.

    """

    if not test:
        try:
            config = ConfigObj(config_path, configspec=f"{config_path}spec")
        except OSError:
            print(f"Failed to load the configuration file at {config_path}.")
            sys.exit(1)

    # Make app work with proxies (like nginx) that set proxy headers.
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Initialize Flask configuration
    #
    # FIXME: Port to configuration
    if test:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = config["webapp"]["database_uri"]
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID", "abc123")
    app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get(
        "GOOGLE_CLIENT_SECRET", "password"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "abc123")
    app.config["SECURITY_TOKEN_MAX_AGE"] = 60
    app.config["SECURITY_TOKEN_AUTHENTICATION_HEADER"] = "Auth-Token"
    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_PASSWORD_SALT"] = os.environ.get("SALT", "salt123")
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_CONFIRMABLE"] = False
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
    app.config["WTF_CSRF_ENABLED"] = False  # Doesn't play nice with token-based auth

    # Initialize Flask-SQLAlchemy
    db.app = app
    db.init_app(app)

    # Only create the database during testing. In production, use alembic to
    # manage the database.
    if test:
        with app.app_context():
            db.create_all()

    # Initialize Flask-CORS
    CORS(app, supports_credentials=True)
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

    # Initialize Flask-Bootstrap
    Bootstrap(app)

    # Initialize Flask-Security
    app.user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(app, app.user_datastore)

    # Initialize Authlib.
    oauth = OAuth()
    oauth.init_app(app)
    app.oauth = oauth

    # Register Google identity provider
    app.google = oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        fetch_token=authlib_fetch_token,
        update_token=authlib_token_update,
        client_kwargs={
            "scope": " ".join(
                [
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                ]
            ),
        },
        authorize_params={
            "access_type": "offline",
            "prompt": "consent",
        },  # for refresh_token
    )

    # Initialize Flask-Admin
    admin = Admin(app, name="Admin")
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Role, db.session))

    return app


@app.route("/")
def index():
    return jsonify( 
        {
            "ok": True
        }
    )


@app.route("/protected")
@auth_required("token", "session")
def protected():
    """Example protected endpoint.

    :return: JSON response with user info.
    """
    return jsonify(
        {
            "username": current_user.email,
            "is_authenticated": current_user.is_authenticated,
        }
    )

