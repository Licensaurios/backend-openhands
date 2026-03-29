import os
import sys
import logging
from configobj import ConfigObj
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flasgger import Swagger

from server.extensiones impopython3 -m venv .venvrt mail
from server.db.model import Role, User, db
from server.routes.auth import auth_router
from server.routes.health import health_router
from server.routes.resource import resource_router

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

from dotenv import load_dotenv  # Asegúrate de instalarlo: pip install python-dotenv

load_dotenv()
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,  # incluir todos los endpoints
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger_template = {
    "info": {
        "title": "OpenHands API",
        "version": "1.0.0",
        "description": "Documentación de la API de la plataforma OpenHands"
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http", "https"],
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
        database_uri = "sqlite://"

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

    db.init_app(app)
    mail.init_app(app)
    
    app.register_blueprint(auth_router)
    app.register_blueprint(health_router)
    app.register_blueprint(resource_router)

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(app, user_datastore)

    with app.app_context():
        if "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"]:
            log.info("Sincronizando modelos con Supabase...")
            db.create_all()
        else:
            log.warning("No se detectó Postgres, omitiendo create_all()")


    return app
