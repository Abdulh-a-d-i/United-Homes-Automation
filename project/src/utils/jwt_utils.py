import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
import logging

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        logging.error(f"JWT decode error: {e}")
        return None


def create_password_reset_token(email: str, expires_delta: timedelta = timedelta(hours=1)):
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": email,
        "type": "password_reset",
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")
        if token_type != "password_reset" or not email:
            return None
        return email
    except JWTError:
        return None
