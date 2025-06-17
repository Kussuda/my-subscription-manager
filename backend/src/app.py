# backend/src/app.py

import os
from datetime import datetime, date
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLASession
from dotenv import load_dotenv
from .schemas import UserCreate, UserResponse, SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate

# Carrega variáveis de ambiente do .env (localizado na pasta 'backend')
# O 'dotenv_path' garante que ele encontre o .env na pasta pai 'backend'
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Importa os modelos que criamos
from .models import Base, User, Subscription

app = FastAPI(
    title="Gerenciador de Assinaturas Pessoais API",
    description="API para gerenciar assinaturas de usuários.",
    version="0.1.0",
)

# --- Configuração do Banco de Dados ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL não configurado nas variáveis de ambiente.")

engine = create_engine(DATABASE_URL)

# Cada instância de SessionLocal é uma sessão de banco de dados.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependência para obter uma sessão de banco de dados por requisição
def get_db():
    db = SessionLocal()
    try:
        yield db # Retorna a sessão e a mantém ativa durante a requisição
    finally:
        db.close() # Garante que a sessão seja fechada após a requisição

# --- Funções de Inicialização ---
def create_tables():
    """Cria todas as tabelas definidas nos modelos no banco de dados."""
    print("Tentando criar tabelas...")
    Base.metadata.create_all(engine)
    print("Tabelas criadas ou já existentes.")

# Evento de inicialização do FastAPI: Chamado quando a aplicação inicia
@app.on_event("startup")
async def startup_event():
    create_tables()
    # Opcional: Adicionar um usuário de teste na inicialização, se não existir
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(email="test@example.com").first():
            test_user = User(email="test@example.com", password_hash="hashed_password_placeholder")
            db.add(test_user)
            db.commit()
            db.refresh(test_user) # Atualiza o objeto para ter o ID gerado
            print("Usuário de teste 'test@example.com' criado.")
        else:
            print("Usuário de teste 'test@example.com' já existe.")
    except Exception as e:
        print(f"Erro ao criar usuário de teste na inicialização: {e}")
        db.rollback()
    finally:
        db.close()


# --- Rotas (Endpoints) da API ---

@app.get("/")
async def read_root():
    """Endpoint de teste para verificar se a API está funcionando."""
    return {"message": "Bem-vindo ao Gerenciador de Assinaturas Pessoais API!"}


# --- Exemplo de Rota para Usuário (simplificado, sem autenticação real ainda) ---
@app.post("/users/")
async def create_user(email: str, password: str, db: SQLASession = Depends(get_db)):
    """Cria um novo usuário (apenas para demonstração inicial, senhas não hasheadas)."""
    # NO FUTURO: Você deve hashear a senha antes de salvar!
    existing_user = db.query(User).filter_by(email=email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado."
        )
    
    new_user = User(email=email, password_hash=password) # Usar password diretamente para teste
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Atualiza o objeto para ter o ID gerado

    return new_user.to_dict()

# --- Exemplo de Rota para Assinaturas (simplificado, sem autenticação real ainda) ---
@app.get("/subscriptions/")
async def get_all_subscriptions(db: SQLASession = Depends(get_db)):
    """Retorna todas as assinaturas (sem filtro por usuário ainda)."""
    subscriptions = db.query(Subscription).all()
    return [sub.to_dict() for sub in subscriptions]

@app.post("/subscriptions/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(sub: SubscriptionCreate, db: SQLASession = Depends(get_db)):
    # POR ENQUANTO: user_id fixo para o usuário de teste criado na inicialização
    # NO FUTURO: o user_id virá da autenticação (do JWT)
    test_user = db.query(User).filter_by(email="test@example.com").first()
    if not test_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário de teste não encontrado. Execute a inicialização do DB."
        )

    new_sub = Subscription(user_id=test_user.id, **sub.dict()) # sub.dict() converte o Pydantic model para dict
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub) # Atualiza o objeto com o ID gerado pelo DB
    return new_sub

@app.get("/subscriptions/", response_model=list[SubscriptionResponse])
async def get_all_subscriptions(db: SQLASession = Depends(get_db)):
    # POR ENQUANTO: Retorna todas as assinaturas sem filtro de usuário
    subscriptions = db.query(Subscription).all()
    return subscriptions

@app.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: int, db: SQLASession = Depends(get_db)):
    subscription = db.query(Subscription).filter_by(id=subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assinatura não encontrada."
        )
    return subscription

@app.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(subscription_id: int, updated_sub: SubscriptionUpdate, db: SQLASession = Depends(get_db)):
    subscription = db.query(Subscription).filter_by(id=subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assinatura não encontrada."
        )

    # Atualiza os campos que foram fornecidos no updated_sub
    for key, value in updated_sub.dict(exclude_unset=True).items():
        setattr(subscription, key, value)

    subscription.updated_at = datetime.utcnow() # Atualiza o timestamp
    db.commit()
    db.refresh(subscription)
    return subscription

@app.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: int, db: SQLASession = Depends(get_db)):
    subscription = db.query(Subscription).filter_by(id=subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assinatura não encontrada."
        )

    db.delete(subscription)
    db.commit()
    return {} # Retorna vazio com status 204
