import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash


def generer_token(client_id):
    payload = {
        'client_id': client_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def token_requis(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            client_id_courant = data['client_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        return f(client_id_courant, *args, **kwargs)
    return decorated