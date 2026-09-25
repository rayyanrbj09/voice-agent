from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    customer_id: int
    order_number: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1)
    total_amount: float = Field(default=0.0, ge=0.0)
    status: str = Field(default="pending", max_length=20)


class OrderUpdate(BaseModel):
    description: str | None = None
    total_amount: float | None = Field(default=None, ge=0.0)
    status: str | None = Field(default=None, max_length=20)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    created_by_user_id: int
    description: str
    total_amount: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
