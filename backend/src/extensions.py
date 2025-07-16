# backend/src/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt # ADICIONADO: Importar Bcrypt
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt() # ADICIONADO: Inicializar Bcrypt aqui
jwt = JWTManager()