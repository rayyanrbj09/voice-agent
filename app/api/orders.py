from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db import repositories
from app.db.models import User
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        order = repositories.create_order(
            db=db,
            user_id=current_user.id,
            customer_id=data.customer_id,
            order_number=data.order_number,
            description=data.description,
            total_amount=data.total_amount,
            status=data.status,
        )
        return order
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "Customer not found" in str(exc) else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An order with this order number already exists for your account.",
        ) from exc


@router.get(
    "",
    response_model=list[OrderResponse],
)
def list_orders(
    status_filter: str | None = Query(None, alias="status"),
    customer_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return repositories.get_orders(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        customer_id=customer_id,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = repositories.get_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
)
def update_order(
    order_id: int,
    data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        order = repositories.update_order(
            db=db,
            order_id=order_id,
            user_id=current_user.id,
            description=data.description,
            total_amount=data.total_amount,
            status=data.status,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = repositories.delete_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return None
