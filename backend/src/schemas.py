from pydantic import BaseModel, EmailStr
from datetime import date, datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionBase(BaseModel):
    name: str
    cost: float
    frequency: str
    renewal_date: date
    category: str = "Uncategorized"
    status: str = "activate"

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(SubscriptionBase):
    name: str | None = None
    cost: float | None = None
    frequency: str | None = None
    renewal_date: date | None = None
    category: str | None = None
    status: str | None = None

class SubscriptionResponse(SubscriptionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None # Para usar no token