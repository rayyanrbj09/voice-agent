from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.db import repositories
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        customer = repositories.create_customer(
            db=db,
            name=customer_data.name,
            email=str(customer_data.email),
            phone=customer_data.phone,
            company=customer_data.company,
            user_id=current_user.id,
        )

        return customer

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create customer",
        )


@router.get(
    "",
    response_model=list[CustomerResponse],
)
def list_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return repositories.get_customers(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = repositories.get_customer(
        db=db,
        customer_id=customer_id,
        user_id=current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = repositories.update_customer(
        db=db,
        customer_id=customer_id,
        user_id=current_user.id,
        name=customer_data.name,
        email=str(customer_data.email) if customer_data.email else None,
        phone=customer_data.phone,
        company=customer_data.company,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = repositories.delete_customer(
        db=db,
        customer_id=customer_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return None