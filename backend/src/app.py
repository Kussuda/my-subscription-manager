# backend/src/app.py

import os
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLASession
from dotenv import load_dotenv
from .schemas import UserCreate, UserResponse, SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate
from .auth import get_password_hash, verify_password, create_access_token, get_current_active_user, oauth2_scheme
from .schemas import UserCreate, UserResponse, SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate, Token
from fastapi.security import OAuth2PasswordRequestForm

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
            hashed_password = get_password_hash("testpassword") # Senha de teste
            test_user = User(email="test@example.com", password_hash=hashed_password)
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
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
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: SQLASession = Depends(get_db)):
    existing_user = db.query(User).filter_by(email=user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado."
        )

    hashed_password = get_password_hash(user.password) # HASH da senha aqui!
    new_user = User(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/subscriptions/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    sub: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: SQLASession = Depends(get_db)
):
    new_sub = Subscription(user_id=current_user.id, **sub.dict()) # user_id vem do usuário autenticado
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@app.get("/subscriptions/", response_model=list[SubscriptionResponse])
async def get_all_subscriptions(
    current_user: User = Depends(get_current_active_user),
    db: SQLASession = Depends(get_db)
):
    # Agora filtra por user_id
    subscriptions = db.query(Subscription).filter_by(user_id=current_user.id).all()
    return subscriptions

@app.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: SQLASession = Depends(get_db)
):
    subscription = db.query(Subscription).filter_by(id=subscription_id, user_id=current_user.id).first() # FILTRAR POR USER_ID
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assinatura não encontrada ou não pertence ao usuário."
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

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SQLASession= Depends(get_db)):
    user = db.query(User).filter_by(email=form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}