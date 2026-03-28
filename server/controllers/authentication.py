import re
import uuid
import secrets
import logging
import time

from flask_mail import Message
from server.extensiones import mail
from flask import make_response, jsonify
from flask_security import logout_user, current_user, login_user as security_login_user
from werkzeug.security import generate_password_hash, check_password_hash
from server.db.model import db, User, OAuth2Token
from server.db.model import OAuth2Token, User, db
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def validar_email(email: str) -> bool:
    if not email: return False
    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(patron, email) is not None

def authorize_user():
    return {
        "authorized": "yes"
    }

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
        return make_response(jsonify({"error": "Email y contraseña son requeridos"}), 400)

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password) and user.active:
        
        security_login_user(user) 
        
        # --- SOLUCIÓN AL UNIQUE VIOLATION ---
        # Borramos cualquier token 'default' previo de este usuario
        OAuth2Token.query.filter_by(user_id=user.id, name="default").delete()
        # ------------------------------------

        access_t = secrets.token_urlsafe(32)
        refresh_t = secrets.token_urlsafe(32)
      
        nuevo_token = OAuth2Token(
            user_id=user.id,
            name="default",              
            token_type="Bearer",        
            access_token=access_t,
            refresh_token=refresh_t,
            expires_at=int(time.time()) + 3600 
        )

        try:
            db.session.add(nuevo_token)
            db.session.commit()
            
            response_data = {
                "msg": "Login exitoso",
                "user": {
                    "nombre": user.nombre,
                    "email": user.email
                }
            }
            
            # --- SOLUCIÓN AL TYPEERROR ---
            # Siempre devolvemos el objeto response directamente
            response = make_response(jsonify(response_data), 200)

            response.set_cookie(
                'access_token', 
                access_t, 
                httponly=True, 
                secure=True, 
                samesite='Lax',
                max_age=3600
            )
            
            response.set_cookie(
                'refresh_token', 
                refresh_t, 
                httponly=True, 
                secure=True, 
                samesite='Lax',
                max_age=86400 * 7
            )

            return response

        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": f"Error al generar sesión: {str(e)}"}), 500)
    
    return make_response(jsonify({"error": "Credenciales inválidas"}), 401)

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

def process_logout():
    try:
        if current_user.is_authenticated:
            # 1. Defensa en profundidad: Borramos los tokens activos del usuario en la BD.
            # Si alguien robó el token, ya no le servirá de nada.
            OAuth2Token.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            
            logout_user()
            
            return {"msg": "Sesión cerrada y tokens invalidados con éxito"}, 200
        else:
            return {"error": "No hay ninguna sesión activa para cerrar"}, 400
            
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error crítico al cerrar sesión: {str(e)}"}, 500    


def renew_session(data):
    old_refresh_token = data.get("refresh_token")
    
    if not old_refresh_token:
        return {"error": "Se requiere el refresh_token para renovar"}, 400
    token_entry = OAuth2Token.query.filter_by(refresh_token=old_refresh_token).first()

    if not token_entry:
        return {"error": "Token no encontrado o ya fue invalidado"}, 401

    # 2. Lógica de "Rotación de Tokens" (Seguridad avanzada)
    # Generamos nuevos nombres/valores para los tokens
    new_access_token = secrets.token_urlsafe(32)
    new_refresh_token = secrets.token_urlsafe(32)
    
    token_entry.access_token = new_access_token
    token_entry.refresh_token = new_refresh_token
    token_entry.expires_at = int(time.time()) + 3600  # Expira en 1 hora
    
    try:
        db.session.commit()
        return {
            "status": "success",
            "tokens": {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al actualizar tokens: {str(e)}"}, 500

def request_password_reset(data):
    email = data.get("email")
    if not email:
        return {"error": "El email es requerido"}, 400

    user = User.query.filter_by(email=email).first()

    response_msg = {"msg": "Si el correo existe en nuestro sistema, recibirás un enlace de recuperación."}

    if user:
        token = secrets.token_urlsafe(32)
        
        user.reset_token = token
        user.reset_token_expires_at = int(time.time()) + 900
        
        try:
            db.session.commit()

            msg = Message(
                subject="Recuperación de Contraseña - OpenHands Community",
                recipients=[user.email]
            )
            
            msg.body = f"""Hola {user.nombre},

Has solicitado restablecer tu contraseña. Copia y pega el siguiente token en la aplicación:

TOKEN: {token}

Este código expirará en 15 minutos. Si no solicitaste este cambio, ignora este correo o contacta a soporte.
"""
            mail.send(msg)

        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Error enviando mail: {e}")
            return {"error": "Error interno al procesar la solicitud"}, 500

    return response_msg, 200

def execute_password_reset(data):
    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("password_confirm")

    if not all([token, new_password, confirm_password]):
        return {"error": "Faltan datos requeridos"}, 400

    if new_password != confirm_password:
        return {"error": "Las contraseñas no coinciden"}, 400

    user = User.query.filter_by(reset_token=token).first()

    if not user:
        return {"error": "Token inválido o expirado"}, 400

    tiempo_actual = int(time.time())
    if tiempo_actual > user.reset_token_expires_at:
        return {"error": "El token ha expirado. Solicita uno nuevo."}, 400

    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    
    user.reset_token = None
    user.reset_token_expires_at = None

    try:
        db.session.commit()

        msg = Message(
            subject="Seguridad: Tu contraseña ha sido actualizada",
            recipients=[user.email]
        )
        msg.body = f"""Hola {user.nombre},

Te informamos que la contraseña de tu cuenta en OpenHands ha sido cambiada exitosamente hoy {time.strftime('%d/%m/%Y %H:%M')}.

Si tú realizaste este cambio, puedes ignorar este correo.

Si NO realizaste este cambio, por favor contacta a nuestro equipo de seguridad de inmediato, ya que tu cuenta podría estar en riesgo.
"""
        mail.send(msg)
        return {"msg": "Contraseña actualizada correctamente"}, 200
    except Exception as e:
        db.session.rollback()
        print(f"Error en el proceso final de reset: {e}")
        return {"error": "Error al actualizar la contraseña"}, 500