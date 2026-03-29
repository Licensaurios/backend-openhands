from functools import wraps
from flask import request, jsonify, make_response
from server.db.model import OAuth2Token, db
import time

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_val = request.cookies.get('access_token')
        
        if not token_val:
            return make_response(jsonify({"error": "No hay sesión activa (Falta access_token)"}), 401)

        token_record = OAuth2Token.query.filter_by(access_token=token_val).first()

        if not token_record:
            return make_response(jsonify({"error": "Token no reconocido"}), 401)
            
        if token_record.expires_at < int(time.time()):
            return make_response(jsonify({"error": "Tu sesión ha expirado. Por favor, re-autentícate."}), 401)

        current_user = token_record.user
        return f(current_user, *args, **kwargs)

    return decorated