# Defining what enters and leaves ouur API

from pydantic import BaseModel, EmailStr,Field
from typing import Optional

# Creating the UserCreate schema to validate the data that is sent to the API when creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)

class UserResponse(BaseModel):
    "This doesnt contain password hash because we dont want to send it back to the user"
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool

    model_config = {
        "from_attributes": True,
    }

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    