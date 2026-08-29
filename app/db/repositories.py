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


def get_customer(
        db: Session,
        customer_id : int,
        user_id: int,       
) -> Customer | None:
    return (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.created_by_user_id == user_id,       
        )
        .first()
    )

def get_customers(
    db: Session,
    user_id: int,
) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(Customer.created_by_user_id == user_id)
        .order_by(Customer.id)
        .all()
    )

def update_customer(
        db: Session,
        customer_id: int,
        user_id: int,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None
) -> Customer | None:
    customer = get_customer(
        db=db,
        customer_id=customer_id,
        user_id=user_id,
    )

    if customer is None:
        return None
    if name is not None:
        customer.name = name
    if email is not None: 
        customer.email = email
    if phone is not None:
        customer.phone = phone
    if company is not None:
        customer.company = company

    db.delete(Customer)
    db.commit()

    return customer

def delete_customer(
    db: Session,
    customer_id : int,
    user_id: int,
) -> bool:
    customer = get_customer(
        db = db, 
        customer_id=customer_id,
        user_id=user_id
    )

    if customer is None:
        return False

    db.delete(customer)
    db.commit()

    return True