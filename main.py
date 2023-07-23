import datetime
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, Depends
from fastapi_users import fastapi_users, FastAPIUsers
from pydantic import BaseModel, Field

from auth.auth import auth_backend
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate

app = FastAPI(title='Trading App')

users = [
    {"id": 1, "role": "admin", "name": ["Bob"]},
    {"id": 2, "role": "investor", "name": "John"},
    {"id": 3, "role": "trader", "name": "Matt"},
    {"id": 4, "role": "investor", "name": "Homer", "degree": [
        {"id": 1, "created_at": "2020-01-01T00:00:00", "type_degree": "expert"}
    ]},
]
trades = [
    {"id": 1, "user_id": 1, "currency": "BTC", "side": "buy", "price": 123, "amount": 2.12},
    {"id": 2, "user_id": 1, "currency": "BTC", "side": "sell", "price": 125, "amount": 2.12},
]


class DegreeType(Enum):
    noob = 'noob'
    expert = 'expert'


class Degree(BaseModel):
    id: int
    created_at: datetime.datetime
    type_degree: DegreeType


class User(BaseModel):
    id: int
    role: str
    name: str
    degree: Optional[List[Degree]] = []


@app.get('/users/{user_id}', response_model=List[User])
def get_user(user_id: int):
    return [user for user in users if user.get('id') == user_id]


@app.put('/users/{user_id}')
def change_user_name(user_id: int, new_name: str):
    user = list(filter(lambda user: user.get('id') == user_id, users))[0]
    user['name'] = new_name
    return {'status': 200, 'data': user}


@app.get('/trades')
def get_trade(limit: int = 10, offset: int = 0):
    return trades[offset:][:limit]


class Trade(BaseModel):
    id: int
    user_id: int
    currency: str = Field(max_length=5)
    side: str
    price: float = Field(ge=0)
    amount: float


@app.post('/trades')
def add_trades(new_trades: List[Trade]):
    trades.extend(new_trades)
    return trades

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

current_user = fastapi_users.current_user()


@app.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.username}"


@app.get("/unprotected-route")
def unprotected_route():
    return f"Hello, anonymous"