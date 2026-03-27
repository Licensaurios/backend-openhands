import re
import uuid
import secrets
import logging
import sqlalchemy
from flask_security import current_user
from flask_security.utils import verify_password
from werkzeug.security import generate_password_hash, check_password_hash

from server.db.model import OAuth2Token, User, db

# Configuración de Logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# --- FUNCIONES DE APOYO Y VALIDACIÓN ---

def validar_email(email: str) -> bool:
    if not email: return False
    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(patron, email) is not None

def authorize_user():
    return {
        "authorized": "yes"
    }

# --- LÓGICA DE AUTENTICACIÓN (REGISTRO Y LOGIN) ---

def register_user(data):
    nombre = data.get("nombre")
    apellido1 = data.get("apellido1")
    apellido2 = data.get("apellido2")
    email = data.get("email")
    password = data.get("password")
    password_confirm = data.get("password_confirm")

    if not all([nombre, apellido1, email, password, password_confirm]):
        return {"error": "Faltan datos obligatorios"}, 400

    if not validar_email(email):
        return {"error": "Formato de correo inválido"}, 400

    if password != password_confirm:
        return {"error": "Las contraseñas no coinciden"}, 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return {"error": "El correo ya está registrado"}, 400
        
    try:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        nuevo_usuario = User(
            nombre=nombre,
            apellido1=apellido1,
            apellido2=apellido2,
            email=email,
            password=hashed_password,
            fs_uniquifier=secrets.token_hex(16),
            active=True
        )

        db.session.add(nuevo_usuario)
        db.session.commit()
        return {"status": "registrado", "email": email}, 201
        
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al guardar en base de datos: {str(e)}"}, 500

def login_user(data):
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email y contraseña son requeridos"}, 400

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        if not user.active:
            return {"error": "Esta cuenta está desactivada"}, 403
            
        return {
            "msg": "Login exitoso",
            "user": {
                "nombre": user.nombre,
                "email": user.email
            }
        }, 200
    
    return {"error": "Credenciales inválidas"}, 401

# --- CONSTRUCTOS DE AUTHLIB (OAUTH2) ---

def authlib_token_update(
    name: str,
    token: dict,
    refresh_token: str = None,
    access_token: str = None
) -> dict | None:
    item = None

    if refresh_token:
        item = OAuth2Token.query.filter_by(
            name=name, refresh_token=refresh_token
        ).first()
    elif access_token:
        item = OAuth2Token.query.filter_by(name=name, access_token=access_token).first()
    else:
        return

    if item:
        item.from_token(token)
        db.session.add(item)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            log.error("Failed to commit updated token...")
            db.session.rollback()

    return item.to_token() if item else None

def authlib_fetch_token(name: str) -> dict | None:
    log.info("Fetching token for [%s].", name)

    user_id = current_user.id

    item = OAuth2Token.query.filter_by(
        name=name,
        user_id=user_id,
    ).first()

    if item:
        return item.to_token()

    log.warning("Failed to fetch token for [%s].", name)
    return None