from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas import UserRead

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserRead:
    # Dummy validation for example purposes
    if token != "secrettoken":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return UserRead(id=1, username="alice", email="alice@example.com", is_active=True)