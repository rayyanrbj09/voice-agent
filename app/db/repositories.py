"""
The repository should know how to talk to SQLAlchemy/PostgreSQL, 
but it should not know anything about HTTP, JWT, LLMs, or voice.
API / Tool
    ↓
Repository
    ↓
SQLAlchemy
    ↓
PostgreSQL
"""
from sqlalchemy.orm import Session

from app.db.models import Customer

def create_customer(
    db : Session,
    name : str,
    email: str,
    phone: str | None,
    company: str | None,
    user_id: int,
) -> Customer:

    customer = Customer(
        name = name,
        email = email,
        phone = phone,
        company= company,
        created_by_user_id = user_id
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer