# backend/src/auth.py

from datetime import timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token

# Removido: from app import app # ESTA LINHA CAUSAVA A IMPORTAÇÃO CIRCULAR!
from .extensions import bcrypt # AGORA IMPORTA A INSTÂNCIA 'bcrypt' DE extensions.py
from .models import User # Importa o modelo User

# As funções get_password_hash e verify_password usam a instância 'bcrypt'
def get_password_hash(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.check_password_hash(hashed_password, plain_password)

# A função create_access_token (do Flask-JWT-Extended) não precisa de alteração.

# Funções para obter usuário atual (para rotas protegidas)
def get_current_user_flask():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if user is None:
        return None
    return user