from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Appointment, Customer

MINIMUM_DURATION_MINUTES = 1


def _parse_starts_at(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("starts_at must be an ISO-8601 datetime.") from exc


def book_appointment(
    db: Session,
    user_id: int,
    customer_id: int,
    starts_at: str,
    duration_minutes: int = 30,
    notes: str | None = None,
) -> Appointment:
    if duration_minutes < MINIMUM_DURATION_MINUTES:
        raise ValueError("duration_minutes must be greater than zero.")
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.created_by_user_id == user_id).one_or_none()
    if customer is None:
        raise ValueError("Customer not found.")
    appointment = Appointment(
        customer_id=customer_id,
        created_by_user_id=user_id,
        starts_at=_parse_starts_at(starts_at),
        duration_minutes=duration_minutes,
        notes=notes,
    )
    try:
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise


def list_appointments(db: Session, user_id: int, status: str | None = None) -> list[Appointment]:
    query = db.query(Appointment).filter(Appointment.created_by_user_id == user_id)
    if status:
        query = query.filter(Appointment.status == status)
    return query.order_by(Appointment.starts_at).all()


def cancel_appointment(db: Session, user_id: int, appointment_id: int) -> Appointment:
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.created_by_user_id == user_id,
    ).one_or_none()
    if appointment is None:
        raise ValueError("Appointment not found.")
    appointment.status = "cancelled"
    try:
        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise
