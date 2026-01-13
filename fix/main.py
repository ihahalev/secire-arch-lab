from __future__ import annotations

import os
import uuid
import logging
from typing import Annotated

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field, SecretStr
from passlib.context import CryptContext

# ---- Logging (мінімальний baseline) ----
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("user-api")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="User API", version="1.0.0")


class UserOut(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: SecretStr


class LoginOut(BaseModel):
    status: str
    request_id: str


@app.middleware("http")
async def request_id_mw(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


@app.get("/health", response_model=dict)
def health():
    return {"ok": True}


@app.get("/user", response_model=UserOut)
def get_user(id: int):
    # Демонстраційний приклад: типізація + response_model = контракт для тестів/гейтів
    return UserOut(id=id, name="Alice")


@app.post("/login", response_model=LoginOut)
def login(payload: LoginIn, request: Request):
    # Секрет має приходити з K8s Secret / Vault (env var, injected at runtime)
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if not stored_hash:
        # Безпечно провалюємось, якщо секрет не підʼєднаний
        raise HTTPException(status_code=500, detail="Server misconfigured")

    ok = pwd_context.verify(payload.password.get_secret_value(), stored_hash)

    rid = request.state.request_id
    if ok:
        log.info(f'{{"event":"auth.login.success","user":"{payload.username}","request_id":"{rid}"}}')
        return LoginOut(status="ok", request_id=rid)

    log.info(f'{{"event":"auth.login.fail","user":"{payload.username}","request_id":"{rid}"}}')
    raise HTTPException(status_code=401, detail="Unauthorized")
