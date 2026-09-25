from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    customer_id: int
    starts_at: datetime
    duration_minutes: int = Field(default=30, ge=1)
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    starts_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    status: str | None = None
    notes: str | None = None


class AppointmentResponse(BaseModel):
    id: int
    customer_id: int
    created_by_user_id: int
    starts_at: datetime
    duration_minutes: int
    status: str
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
