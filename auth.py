from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import RefreshToken 

SECRET_KEY = "50146eb35c7eaa52ed8d87918073b68bc5ae0496cd5964cff4d2b32f0ae8b5a0"
REFRESH_SECRET_KEY = "61257fc46d8fbb63fe9e98029184c79cd6bf1507de6075dgg5e3c43g1bf9cb1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUITES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUITES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(db: Session, data: dict):
    expire = datetime.utcnow() + timedelta(days=7)
    token = jwt.encode({"sub": data["sub"], "exp": expire}, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

 
    db_token = RefreshToken(token=token, user_id=data["user_id"])
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return token


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        exp: int = payload.get("exp")

        # Check if token is expired
        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

        return email
    except JWTError:
        raise credentials_exception

def verify_refresh_token(refresh_token: str, db: Session):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
        if not db_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        return email
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_access_token(token, credentials_exception)