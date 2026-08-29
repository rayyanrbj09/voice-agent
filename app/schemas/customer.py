""""
POST   /customers
GET    /customers
GET    /customers/{customer_id}
PATCH  /customers/{customer_id}
DELETE /customers/{customer_id}
Authorization : Bearer <JWT>
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

class CustomerCreate(BaseModel):
    name : str
    email : EmailStr | None = None
    phone : str | None = None
    company: str | None = None

class CustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone : str | None
    company: str | None
    created_by_user_id: int
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)

class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None