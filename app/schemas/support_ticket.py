from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SupportTicketCreate(BaseModel):
    customer_id: int
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    priority: str = Field(default="normal", max_length=20)


class SupportTicketUpdate(BaseModel):
    subject: str | None = Field(default=None, max_length=200)
    description: str | None = None
    priority: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, max_length=20)


class SupportTicketResponse(BaseModel):
    id: int
    customer_id: int
    created_by_user_id: int
    subject: str
    description: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
