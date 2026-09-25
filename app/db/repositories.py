"""Database repository layer for customer and business resources.

The repository interacts directly with SQLAlchemy and provides data access
for both API routers and agent tools while maintaining user-ownership isolation.
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Appointment, Customer, Order, SupportTicket


# ============================================================================
# Customer Repositories
# ============================================================================

def create_customer(
    db: Session,
    name: str,
    email: str,
    phone: str | None,
    company: str | None,
    user_id: int,
) -> Customer:
    customer = Customer(
        name=name,
        email=email,
        phone=phone,
        company=company,
        created_by_user_id=user_id,
    )
    try:
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise


def get_customer(
    db: Session,
    customer_id: int,
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
    company: str | None = None,
) -> Customer | None:
    customer = get_customer(db=db, customer_id=customer_id, user_id=user_id)
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

    try:
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise


def delete_customer(
    db: Session,
    customer_id: int,
    user_id: int,
) -> bool:
    customer = get_customer(db=db, customer_id=customer_id, user_id=user_id)
    if customer is None:
        return False

    try:
        db.delete(customer)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


# ============================================================================
# Appointment Repositories
# ============================================================================

def create_appointment(
    db: Session,
    user_id: int,
    customer_id: int,
    starts_at: datetime,
    duration_minutes: int = 30,
    notes: str | None = None,
    status: str = "scheduled",
) -> Appointment:
    customer = get_customer(db, customer_id=customer_id, user_id=user_id)
    if customer is None:
        raise ValueError("Customer not found.")

    if duration_minutes < 1:
        raise ValueError("duration_minutes must be greater than zero.")

    appointment = Appointment(
        customer_id=customer_id,
        created_by_user_id=user_id,
        starts_at=starts_at,
        duration_minutes=duration_minutes,
        notes=notes,
        status=status,
    )
    try:
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise


def get_appointment(
    db: Session,
    appointment_id: int,
    user_id: int,
) -> Appointment | None:
    return (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.created_by_user_id == user_id,
        )
        .first()
    )


def get_appointments(
    db: Session,
    user_id: int,
    status: str | None = None,
    customer_id: int | None = None,
) -> list[Appointment]:
    query = db.query(Appointment).filter(Appointment.created_by_user_id == user_id)
    if status is not None:
        query = query.filter(Appointment.status == status)
    if customer_id is not None:
        query = query.filter(Appointment.customer_id == customer_id)
    return query.order_by(Appointment.starts_at.asc()).all()


def update_appointment(
    db: Session,
    appointment_id: int,
    user_id: int,
    starts_at: datetime | None = None,
    duration_minutes: int | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> Appointment | None:
    appointment = get_appointment(db, appointment_id=appointment_id, user_id=user_id)
    if appointment is None:
        return None

    if starts_at is not None:
        appointment.starts_at = starts_at
    if duration_minutes is not None:
        if duration_minutes < 1:
            raise ValueError("duration_minutes must be greater than zero.")
        appointment.duration_minutes = duration_minutes
    if status is not None:
        appointment.status = status
    if notes is not None:
        appointment.notes = notes

    try:
        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise


def cancel_appointment(
    db: Session,
    appointment_id: int,
    user_id: int,
) -> Appointment | None:
    return update_appointment(db, appointment_id=appointment_id, user_id=user_id, status="cancelled")


def delete_appointment(
    db: Session,
    appointment_id: int,
    user_id: int,
) -> bool:
    appointment = get_appointment(db, appointment_id=appointment_id, user_id=user_id)
    if appointment is None:
        return False

    try:
        db.delete(appointment)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


# ============================================================================
# Order Repositories
# ============================================================================

def create_order(
    db: Session,
    user_id: int,
    customer_id: int,
    order_number: str,
    description: str,
    total_amount: float | Decimal = 0.0,
    status: str = "pending",
) -> Order:
    customer = get_customer(db, customer_id=customer_id, user_id=user_id)
    if customer is None:
        raise ValueError("Customer not found.")

    if float(total_amount) < 0:
        raise ValueError("total_amount cannot be negative.")

    order = Order(
        customer_id=customer_id,
        created_by_user_id=user_id,
        order_number=order_number,
        description=description,
        total_amount=total_amount,
        status=status,
    )
    try:
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise


def get_order(
    db: Session,
    order_id: int,
    user_id: int,
) -> Order | None:
    return (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.created_by_user_id == user_id,
        )
        .first()
    )


def get_orders(
    db: Session,
    user_id: int,
    status: str | None = None,
    customer_id: int | None = None,
) -> list[Order]:
    query = db.query(Order).filter(Order.created_by_user_id == user_id)
    if status is not None:
        query = query.filter(Order.status == status)
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)
    return query.order_by(Order.created_at.desc()).all()


def update_order(
    db: Session,
    order_id: int,
    user_id: int,
    description: str | None = None,
    total_amount: float | Decimal | None = None,
    status: str | None = None,
) -> Order | None:
    order = get_order(db, order_id=order_id, user_id=user_id)
    if order is None:
        return None

    if description is not None:
        order.description = description
    if total_amount is not None:
        if float(total_amount) < 0:
            raise ValueError("total_amount cannot be negative.")
        order.total_amount = total_amount
    if status is not None:
        order.status = status

    try:
        db.commit()
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise


def delete_order(
    db: Session,
    order_id: int,
    user_id: int,
) -> bool:
    order = get_order(db, order_id=order_id, user_id=user_id)
    if order is None:
        return False

    try:
        db.delete(order)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


# ============================================================================
# Support Ticket Repositories
# ============================================================================

def create_support_ticket(
    db: Session,
    user_id: int,
    customer_id: int,
    subject: str,
    description: str,
    priority: str = "normal",
    status: str = "open",
) -> SupportTicket:
    customer = get_customer(db, customer_id=customer_id, user_id=user_id)
    if customer is None:
        raise ValueError("Customer not found.")

    ticket = SupportTicket(
        customer_id=customer_id,
        created_by_user_id=user_id,
        subject=subject,
        description=description,
        priority=priority,
        status=status,
    )
    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        raise


def get_support_ticket(
    db: Session,
    ticket_id: int,
    user_id: int,
) -> SupportTicket | None:
    return (
        db.query(SupportTicket)
        .filter(
            SupportTicket.id == ticket_id,
            SupportTicket.created_by_user_id == user_id,
        )
        .first()
    )


def get_support_tickets(
    db: Session,
    user_id: int,
    status: str | None = None,
    priority: str | None = None,
    customer_id: int | None = None,
) -> list[SupportTicket]:
    query = db.query(SupportTicket).filter(SupportTicket.created_by_user_id == user_id)
    if status is not None:
        query = query.filter(SupportTicket.status == status)
    if priority is not None:
        query = query.filter(SupportTicket.priority == priority)
    if customer_id is not None:
        query = query.filter(SupportTicket.customer_id == customer_id)
    return query.order_by(SupportTicket.updated_at.desc()).all()


def update_support_ticket(
    db: Session,
    ticket_id: int,
    user_id: int,
    subject: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    status: str | None = None,
) -> SupportTicket | None:
    ticket = get_support_ticket(db, ticket_id=ticket_id, user_id=user_id)
    if ticket is None:
        return None

    if subject is not None:
        ticket.subject = subject
    if description is not None:
        ticket.description = description
    if priority is not None:
        ticket.priority = priority
    if status is not None:
        ticket.status = status

    try:
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        raise


def delete_support_ticket(
    db: Session,
    ticket_id: int,
    user_id: int,
) -> bool:
    ticket = get_support_ticket(db, ticket_id=ticket_id, user_id=user_id)
    if ticket is None:
        return False

    try:
        db.delete(ticket)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise