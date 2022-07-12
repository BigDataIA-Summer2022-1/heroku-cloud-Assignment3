from sqlalchemy.orm import Session
import fastapi.security as security
import api.models as _model
import api.schemas as schemas
import jwt
from fastapi import HTTPException, Security，status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from passlib.hash import sha256_crypt
import api.user as user

JWT_SECRET = 'myjwtsecret'

oauth2schema = security.OAuth2PasswordBearer(tokenUrl="/token")

def get_user(db: Session, user_id: int):
    return db.query(_model.User).filter(_model.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(_model.User).filter(_model.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(_model.User).offset(skip).limit(limit).all()

user_handler = user.UserHandler()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = user_handler.get_password_hash(user.password)
    db_user = _model.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not user_handler.verify_password(password,user.hashed_password):
        return False
    return user

async def create_token(user: _model.User):
    user_obj = schemas.User.from_orm(user)

    token = jwt.encode(user_obj.dict(), JWT_SECRET)

    return dict(access_token=token, token_type="bearer")

async def get_current_user(token: str = Depends(oauth2schema)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        # token_data = TokenData(email=email)
    except jwt.InvalidTokenError:
        raise credentials_exception
    return email

