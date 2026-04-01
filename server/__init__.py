import os
import sys
import logging
from configobj import ConfigObj
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flasgger import Swagger
from dotenv import load_dotenv
# 1. IMPORTACIONES DE TU PROYECTO
from server.db.model import Role, User, db
from server.extensiones import mail
from server.extensiones import socketio
from server.routes.auth import auth_router
from server.routes.health import health_router
from server.routes.resource import resource_router
from server.routes.community import community_router
from server.routes.chat import chat_router
from server.sockets.events import register_chat_events 

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

load_dotenv()
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

def init_webapp(config_path: str, test: bool = False) -> Flask:
    app = Flask(__name__)
    
    database_uri = os.environ.get("DATABASE_URL")
    
    if not test and not database_uri:
        abs_config_path = os.path.abspath(config_path)
        if os.path.exists(abs_config_path):
            config = ConfigObj(abs_config_path, encoding='utf8')
            database_uri = config["webapp"]["database_uri"]
        else:
            log.error("No se encontró DATABASE_URL en .env ni dev.config")
            sys.exit(1)
    elif test:
        database_uri = "sqlite:///:memory:"

    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev_key_fallback"),
        SECURITY_PASSWORD_SALT=os.environ.get("SECURITY_PASSWORD_SALT", "salt_fallback"),
        SECURITY_PASSWORD_HASH="pbkdf2_sha256",
        WTF_CSRF_ENABLED=False,
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.environ.get("MAIL_DEFAULT_SENDER")
    )

    # Iniciar Extensiones (DB y Mail)
    db.init_app(app)
    mail.init_app(app)
    Swagger(app, config=swagger_config) 

    socketio.init_app(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    register_chat_events(socketio)
    app.register_blueprint(auth_router)
    app.register_blueprint(health_router)
    app.register_blueprint(resource_router)
    app.register_blueprint(community_router) 
    app.register_blueprint(chat_router) 
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(app, user_datastore)
    app.config['SECURITY_EXEMPT_METHODS'] = {'OPTIONS'}

    with app.app_context():
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "postgresql" in uri or "postgres" in uri:
            db.create_all()
            log.info("Sincronizando modelos de OpenHands con Supabase...")

    return app


def start_server():
    app = init_webapp('./config/dev.config')
    socketio.run(app, debug=True, port=5000, host="0.0.0.0", use_reloader=True)
# __all__ = ["init_webapp", "socketio"]
