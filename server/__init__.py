import os
import sys
import logging
from configobj import ConfigObj
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from server.extensiones import mail
from server.db.model import Role, User, db
from server.routes.auth import auth_router
from server.routes.health import health_router
from server.routes.resource import resource_router

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def init_webapp(config_path: str, test: bool = False) -> Flask:
    app = Flask(__name__)
    
    abs_config_path = os.path.abspath(config_path)
    
    if not test:
        if not os.path.exists(abs_config_path):
            log.error(f"Archivo de configuración no encontrado en: {abs_config_path}")
            sys.exit(1)
            
        try:
            config = ConfigObj(abs_config_path, encoding='utf8')
            database_uri = config["webapp"]["database_uri"]
        except Exception as e:
            log.error(f"Error al procesar config: {e}")
            sys.exit(1)
    else:
        database_uri = "sqlite://"

    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        
        SECRET_KEY=os.environ.get("SECRET_KEY", "abc1234_dev_key"),
        SECURITY_PASSWORD_HASH="pbkdf2_sha256",
        SECURITY_PASSWORD_SALT="salt_dev",
        WTF_CSRF_ENABLED=False,

        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME='openhands.path@gmail.com',
        MAIL_PASSWORD='bcosnfdfgdmkqbcq',  
        MAIL_DEFAULT_SENDER='Soporte OpenHands <openhands.path@gmail.com>'
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
