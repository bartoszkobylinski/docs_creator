from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas import ItemCreate, ItemRead
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=ItemRead)
def create_item(item: ItemCreate, user=Depends(get_current_user)):
    """Create an item owned by the authenticated user."""
    return ItemRead(id=1, owner_id=user.id, name=item.name, description=item.description)

@router.get("/", response_model=List[ItemRead])
def read_items(skip: int = 0, limit: int = 10):
    """Retrieve a list of items with pagination."""
    return [ItemRead(id=i, owner_id=1, name=f"Item {i}", description=None)
            for i in range(skip, skip + limit)]