from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import UserCreate, UserResponse, Token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    "/register", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    existing_user = (db.query(User).filter(User.email == user_create.email).first())

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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