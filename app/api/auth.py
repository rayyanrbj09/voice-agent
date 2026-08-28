from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token,
    decode_access_token
)
from app.schemas.auth import(
    UserCreate, 
    UserResponse, 
    Token,
    LoginRequest)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

security = HTTPBearer()

@router.post(
    "/register", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    existing_user = (db.query(User).filter(User.email == user_create.email).first())

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        full_name=user_create.full_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.post("/login", response_model=Token)
def login(
    login_request: LoginRequest, 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_request.email).first()

    if not user or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(user_id=str(user.id))

    return Token(access_token=access_token, token_type="bearer"
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
        token = credentials.credentials

        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
        except HTTPException as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Invalid token or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Invalid token or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # return db.query(User).filter(User.id == user_id).first()
        return user 

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user