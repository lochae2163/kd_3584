from pydantic import BaseModel


class UserLogin(BaseModel):
    """Login credentials."""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"