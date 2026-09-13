from sqlalchemy.orm import Session

from app.db.models import Customer, Order


def create_order(
	db: Session,
	user_id: int,
	customer_id: int,
	order_number: str,
	description: str,
	total_amount: float = 0,
	status: str = "pending",
) -> Order:
	customer = db.query(Customer).filter(Customer.id == customer_id, Customer.created_by_user_id == user_id).one_or_none()
	if customer is None:
		raise ValueError("Customer not found.")
	if total_amount < 0:
		raise ValueError("total_amount cannot be negative.")
	order = Order(
		customer_id=customer_id,
		created_by_user_id=user_id,
		order_number=order_number,
		description=description,
		total_amount=total_amount,
		status=status,
	)
	db.add(order)
	db.commit()
	db.refresh(order)
	return order


def list_orders(db: Session, user_id: int, status: str | None = None) -> list[Order]:
	query = db.query(Order).filter(Order.created_by_user_id == user_id)
	if status:
		query = query.filter(Order.status == status)
	return query.order_by(Order.created_at.desc()).all()
