from fastapi import APIRouter, HTTPException, status
from app.models.user import Token, UserLogin
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["Admin Auth"])


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Admin login endpoint.

    Request body:
    {
        "username": "your-admin-username",
        "password": "your-admin-password"
    }

    Returns JWT access token on successful authentication.
    """
    if not AuthService.verify_admin_credentials(
        credentials.username, 
        credentials.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = AuthService.create_access_token({"sub": credentials.username})
    return {"access_token": access_token, "token_type": "bearer"}