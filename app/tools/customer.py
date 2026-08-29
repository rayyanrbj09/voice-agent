from sqlalchemy.orm import Session
from app.db.models import Customer

def search_customer(
        db: Session,
        user_id: int,
        query: str,
) -> list[Customer] :
    """
    Search customers belonging to the authenticated users

    The tool searches by:
    - customer name
    - email
    - phone
    - company
    """

    search = f"%{query}%"

    return (db.query(Customer)
            .filter(
                Customer.created_by_user_id == user_id,
                (
                    Customer.name.ilike(search)
                    |Customer.email.ilike(search)
                    |Customer.phone.ilike(search)
                    | Customer.company.ilike(search)
                ),
            )
            .order_by(Customer.id)
            .all()
            )


