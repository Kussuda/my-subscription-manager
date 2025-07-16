# backend/src/app.py

import os
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity # Importar do Flask-JWT-Extended
from flask_jwt_extended import decode_token # Adicionado para uso futuro se necessário

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Importar as extensões ---
from .extensions import db, bcrypt, jwt # AGORA IMPORTA DB, BCRYPT e JWT de extensions.py

# --- Importar modelos e autenticação (agora podem ser importados aqui) ---
from .models import User, Subscription
from .auth import get_password_hash, verify_password, get_current_user_flask # IMPORTAÇÃO CORRETA DE AUTH

app = Flask(__name__)

# --- Configurações ---
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL_FLASK", "postgresql://user:password@localhost:5432/subscriptions_db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30)))

# --- Inicializar as extensões com a app Flask ---
db.init_app(app)
bcrypt.init_app(app) # ADICIONADO: Inicializar Bcrypt com a app
jwt.init_app(app)

# Configuração CORS
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# --- Rotas de Teste (já existente) ---
@app.route('/')
def hello_world():
    return jsonify(message="Hello, World from Flask Subscription Manager Backend!")

# --- Rotas de Autenticação ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify(message="Email and password are required"), 400

    if User.query.filter_by(email=email).first():
        return jsonify(message="User with this email already exists"), 409

    hashed_password = get_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify(message="User registered successfully"), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and verify_password(password, user.password_hash):
        access_token = create_access_token(identity=user.email)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify(message="Invalid credentials"), 401

# --- Rotas de Assinaturas (CRUD) ---

@app.route('/subscriptions', methods=['POST'])
@jwt_required() # Protege a rota, requer JWT válido
def create_subscription():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    if not user:
        return jsonify(message="User not found"), 404 # Deveria ser pego pelo jwt_required, mas para segurança

    data = request.get_json()
    name = data.get('name')
    cost = data.get('cost')
    frequency = data.get('frequency')
    renewal_date_str = data.get('renewal_date')
    category = data.get('category')
    status = data.get('status')

    if not all([name, cost, frequency, renewal_date_str]):
        return jsonify(message="Missing required fields: name, cost, frequency, renewal_date"), 400

    try:
        cost = float(cost)
        renewal_date = datetime.strptime(renewal_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify(message="Invalid cost or renewal_date format. Use YYYY-MM-DD for date."), 400

    new_subscription = Subscription(
        user_id=user.id,
        name=name,
        cost=cost,
        frequency=frequency,
        renewal_date=renewal_date,
        category=category,
        status=status
    )
    db.session.add(new_subscription)
    db.session.commit()

    return jsonify(new_subscription.to_dict()), 201

@app.route('/subscriptions', methods=['GET'])
@jwt_required()
def get_subscriptions():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    if not user:
        return jsonify(message="User not found"), 404

    subscriptions = Subscription.query.filter_by(user_id=user.id).all()
    return jsonify([sub.to_dict() for sub in subscriptions]), 200

@app.route('/subscriptions/<int:subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription(subscription_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    if not user:
        return jsonify(message="User not found"), 404

    subscription = Subscription.query.filter_by(id=subscription_id, user_id=user.id).first()

    if not subscription:
        return jsonify(message="Subscription not found or you don't have access"), 404

    return jsonify(subscription.to_dict()), 200

@app.route('/subscriptions/<int:subscription_id>', methods=['PUT'])
@jwt_required()
def update_subscription(subscription_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    if not user:
        return jsonify(message="User not found"), 404

    subscription = Subscription.query.filter_by(id=subscription_id, user_id=user.id).first()

    if not subscription:
        return jsonify(message="Subscription not found or you don't have access"), 404

    data = request.get_json()
    
    if 'name' in data:
        subscription.name = data['name']
    if 'cost' in data:
        try:
            subscription.cost = float(data['cost'])
        except (ValueError, TypeError):
            return jsonify(message="Invalid cost format"), 400
    if 'frequency' in data:
        subscription.frequency = data['frequency']
    if 'renewal_date' in data:
        try:
            subscription.renewal_date = datetime.strptime(data['renewal_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return jsonify(message="Invalid renewal_date format. Use YYYY-MM-DD."), 400
    if 'category' in data:
        subscription.category = data['category']
    if 'status' in data:
        subscription.status = data['status']

    db.session.commit()
    return jsonify(subscription.to_dict()), 200

@app.route('/subscriptions/<int:subscription_id>', methods=['DELETE'])
@jwt_required()
def delete_subscription(subscription_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    if not user:
        return jsonify(message="User not found"), 404

    subscription = Subscription.query.filter_by(id=subscription_id, user_id=user.id).first()

    if not subscription:
        return jsonify(message="Subscription not found or you don't have access"), 404

    db.session.delete(subscription)
    db.session.commit()
    return jsonify(message="Subscription deleted successfully"), 204

# --- Bloco de Execução Principal ---
if __name__ == '__main__':
    with app.app_context(): # Necessário para operações de DB fora de uma requisição
        db.create_all() # Cria as tabelas se não existirem
        print("Tabelas criadas ou já existentes.")

        # Adicionar usuário de teste (se não existir)
        if not User.query.filter_by(email="test@example.com").first():
            hashed_password = get_password_hash("testpassword")
            test_user = User(email="test@example.com", password_hash=hashed_password)
            db.session.add(test_user)
            db.session.commit()
            print("Usuário de teste 'test@example.com' criado.")
        else:
            print("Usuário de teste 'test@example.com' já existe.")

    app.run(host='0.0.0.0', port=5000, debug=True)