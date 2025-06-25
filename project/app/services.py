"""
Service layer implements business logic and data access abstraction.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import User, Item
from app.schemas import UserCreate, ItemCreate, UserRead, ItemRead

class UserService:
    """Handles user-related operations."""
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_in: UserCreate) -> UserRead:
        # Example: hashing password, saving user
        # user = User(**user_in.dict())
        # self.db.add(user); self.db.commit(); self.db.refresh(user)
        return UserRead(id=1, username=user_in.username, email=user_in.email, is_active=True)

    def get(self, user_id: int) -> Optional[UserRead]:
        # Example: retrieve from DB
        return UserRead(id=user_id, username="alice", email="alice@example.com", is_active=True)

class ItemService:
    """Handles item-related operations."""
    def __init__(self, db: Session):
        self.db = db

    def create(self, owner_id: int, item_in: ItemCreate) -> ItemRead:
        # Similar DB operations
        return ItemRead(id=1, owner_id=owner_id, name=item_in.name, description=item_in.description)

    def list(self, skip: int = 0, limit: int = 10) -> List[ItemRead]:
        return [ItemRead(id=i, owner_id=1, name=f"Item {i}", description=None)
                for i in range(skip, skip + limit)]