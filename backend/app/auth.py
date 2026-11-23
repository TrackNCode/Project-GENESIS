"""Authentication utilities (placeholder).
Provides simple JWT‑like token generation using HS256 via PyJWT.
In production replace with a full auth provider (OAuth, Clerk, etc.).
"""
import os
import datetime
from typing import Optional
import jwt  # PyJWT is part of the environment (installed via fastapi dependency)

SECRET_KEY = os.getenv("GENESIS_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise ValueError("Invalid token")
