from datetime import datetime

import pytest

from app.db.models import Customer, User
from app.tools.appointments import book_appointment, cancel_appointment, list_appointments
from app.tools.orders import create_order, list_orders
from app.tools.support import create_support_ticket, list_support_tickets, update_support_ticket
from conftest import TestingSessionLocal


def create_user_and_customer(db, user_id: int, email: str, customer_email: str) -> Customer:
    user = User(id=user_id, email=email, hashed_password="hashed")
    db.add(user)
    db.flush()
    customer = Customer(
        name="Test Customer",
        email=customer_email,
        created_by_user_id=user_id,
    )
    db.add(customer)
    db.flush()
    return customer


def test_appointments_are_created_listed_cancelled_and_user_scoped():
    db = TestingSessionLocal()
    try:
        customer = create_user_and_customer(db, 1, "one@example.com", "customer-one@example.com")
        create_user_and_customer(db, 2, "two@example.com", "customer-two@example.com")
        db.commit()

        appointment = book_appointment(
            db=db,
            user_id=1,
            customer_id=customer.id,
            starts_at="2026-10-01T10:00:00",
            duration_minutes=45,
        )

        assert appointment.status == "scheduled"
        assert appointment.starts_at == datetime(2026, 10, 1, 10, 0)
        assert len(list_appointments(db, user_id=1)) == 1
        assert list_appointments(db, user_id=2) == []

        cancelled = cancel_appointment(db, user_id=1, appointment_id=appointment.id)
        assert cancelled.status == "cancelled"
    finally:
        db.close()


def test_orders_and_support_tickets_are_user_scoped():
    db = TestingSessionLocal()
    try:
        customer = create_user_and_customer(db, 1, "one@example.com", "customer-one@example.com")
        db.commit()

        order = create_order(
            db=db,
            user_id=1,
            customer_id=customer.id,
            order_number="ORD-1001",
            description="Replacement device",
            total_amount=99.50,
        )
        ticket = create_support_ticket(
            db=db,
            user_id=1,
            customer_id=customer.id,
            subject="Device is delayed",
            description="The delivery has not arrived.",
            priority="high",
        )

        assert list_orders(db, user_id=1)[0].order_number == order.order_number
        assert list_orders(db, user_id=2) == []
        assert list_support_tickets(db, user_id=1)[0].priority == "high"
        assert list_support_tickets(db, user_id=2) == []

        updated = update_support_ticket(db, user_id=1, ticket_id=ticket.id, status="resolved")
        assert updated.status == "resolved"
    finally:
        db.close()


def test_business_tools_validate_customer_and_input():
    db = TestingSessionLocal()
    try:
        with pytest.raises(ValueError, match="Customer not found"):
            book_appointment(db, 1, 999, "2026-10-01T10:00:00")

        customer = create_user_and_customer(db, 1, "one@example.com", "customer-one@example.com")
        db.commit()
        with pytest.raises(ValueError, match="greater than zero"):
            book_appointment(db, 1, customer.id, "2026-10-01T10:00:00", duration_minutes=0)
        with pytest.raises(ValueError, match="negative"):
            create_order(db, 1, customer.id, "ORD-1002", "Invalid", total_amount=-1)
    finally:
        db.close()