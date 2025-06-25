from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        orm_mode = True

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemRead(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True