from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import UserCreate, UserRead
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    """Create a new user with username, email, and password."""
    # Pretend to save to DB
    return UserRead(id=2, username=user.username, email=user.email, is_active=True)

@router.post("/token")
def login(form_data: dict):
    """Generate an access token for the user."""
    # Dummy token
    return {"access_token": "secrettoken", "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserRead = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return current_user