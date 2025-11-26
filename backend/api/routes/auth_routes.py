from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    """
    Very simple auth stub – in a student project we can skip real security.
    """
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # TODO: replace with real auth (JWT + DB)
    fake_token = f"demo-token-for-{payload.username}"
    return LoginResponse(access_token=fake_token)
