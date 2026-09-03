from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customers: Mapped[list["Customer"]] = relationship(
        "Customer",
        back_populates="created_by",
        )

class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("created_by_user_id", "email", name="uq_customers_owner_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    company: Mapped[ str | None] = mapped_column(String(150), nullable=True)

    created_by_user_id : Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    created_by : Mapped["User"] = relationship(
        "User",
        back_populates="customers"
    )
