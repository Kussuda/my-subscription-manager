# backend/src/app.py

import os
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS # Para lidar com CORS

# Para JWT
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity

# Carrega variáveis de ambiente do .env
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Inicializa o Flask
app = Flask(__name__)

# Configuração do banco de dados (usando variável de ambiente)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL_FLASK", "postgresql://user:password@localhost:5432/subscriptions_db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Desativa rastreamento de modificações (recomendado)

# Configuração JWT
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY") # Chave secreta para JWT (do seu .env)
jwt = JWTManager(app)

# Configuração CORS
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"]) # Permite seu frontend

# Inicializa o SQLAlchemy
db = SQLAlchemy(app)

# --- Importa os modelos (precisam ser definidos depois de 'db = SQLAlchemy(app)') ---
# from .models import User, Subscription # Será importado aqui depois

# --- Rota de Teste ---
@app.route('/')
def hello_world():
    return jsonify(message="Hello, World from Flask Subscription Manager Backend!")

if __name__ == '__main__':
    # --- Importar modelos e criar tabelas aqui para que 'db' esteja disponível ---
    with app.app_context(): # Necessário para operações de DB fora de uma requisição
        from .models import User, Subscription # Importa os modelos aqui
        db.create_all() # Cria as tabelas
        print("Tabelas criadas ou já existentes.")

        # Adicionar usuário de teste (se não existir)
        if not User.query.filter_by(email="test@example.com").first():
            from .auth import get_password_hash
            hashed_password = get_password_hash("testpassword")
            test_user = User(email="test@example.com", password_hash=hashed_password)
            db.session.add(test_user)
            db.session.commit()
            print("Usuário de teste 'test@example.com' criado.")
        else:
            print("Usuário de teste 'test@example.com' já existe.")

    app.run(host='0.0.0.0', port=5000, debug=True)