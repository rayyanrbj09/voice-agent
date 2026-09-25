from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db import repositories
from app.db.models import User
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketUpdate,
)

router = APIRouter(
    prefix="/support-tickets",
    tags=["Support Tickets"],
)


@router.post(
    "",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_support_ticket(
    data: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        ticket = repositories.create_support_ticket(
            db=db,
            user_id=current_user.id,
            customer_id=data.customer_id,
            subject=data.subject,
            description=data.description,
            priority=data.priority,
        )
        return ticket
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "Customer not found" in str(exc) else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[SupportTicketResponse],
)
def list_support_tickets(
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    customer_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return repositories.get_support_tickets(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        priority=priority,
        customer_id=customer_id,
    )


@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def get_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = repositories.get_support_ticket(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
    )
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )
    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def update_support_ticket(
    ticket_id: int,
    data: SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = repositories.update_support_ticket(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        status=data.status,
    )
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )
    return ticket


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = repositories.delete_support_ticket(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )
    return None
