from sqlalchemy.orm import Session

from app.db.models import Customer, SupportTicket


def create_support_ticket(
	db: Session,
	user_id: int,
	customer_id: int,
	subject: str,
	description: str,
	priority: str = "normal",
) -> SupportTicket:
	customer = db.query(Customer).filter(Customer.id == customer_id, Customer.created_by_user_id == user_id).one_or_none()
	if customer is None:
		raise ValueError("Customer not found.")
	ticket = SupportTicket(
		customer_id=customer_id,
		created_by_user_id=user_id,
		subject=subject,
		description=description,
		priority=priority,
	)
	try:
		db.add(ticket)
		db.commit()
		db.refresh(ticket)
		return ticket
	except Exception:
		db.rollback()
		raise


def list_support_tickets(db: Session, user_id: int, status: str | None = None) -> list[SupportTicket]:
	query = db.query(SupportTicket).filter(SupportTicket.created_by_user_id == user_id)
	if status:
		query = query.filter(SupportTicket.status == status)
	return query.order_by(SupportTicket.updated_at.desc()).all()


def update_support_ticket(
	db: Session,
	user_id: int,
	ticket_id: int,
	status: str | None = None,
	priority: str | None = None,
) -> SupportTicket:
	ticket = db.query(SupportTicket).filter(
		SupportTicket.id == ticket_id,
		SupportTicket.created_by_user_id == user_id,
	).one_or_none()
	if ticket is None:
		raise ValueError("Support ticket not found.")
	if status is not None:
		ticket.status = status
	if priority is not None:
		ticket.priority = priority
	try:
		db.commit()
		db.refresh(ticket)
		return ticket
	except Exception:
		db.rollback()
		raise
