from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.core.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
)

class AuthService:

    def __init__(self):
        self.user_repository = UserRepository()

    async def register(self, body: RegisterRequest):
        existing_user = await self.user_repository.find_by_email(
            body.email
        )

        if existing_user:
            raise UserAlreadyExistsException()

        now = datetime.now(timezone.utc)

        user = {
            "name": body.name,
            "email": body.email,
            "password": hash_password(body.password),
            "created_at": now,
            "updated_at": now
        }

        user_id = await self.user_repository.create(user)

        token = create_access_token(
            {
                "sub": user_id,
                "email": body.email
            }
        )

        return {
            "id": user_id,
            "name": body.name,
            "email": body.email,
            "token": token
        }

    async def login(self, body: LoginRequest):

        user = await self.user_repository.find_by_email(
            body.email
        )

        if not user:
            raise InvalidCredentialsException()

        if not verify_password(
            body.password,
            user["password"]
        ):
            raise InvalidCredentialsException()

        token = create_access_token(
            {
                "sub": str(user["_id"]),
                "email": user["email"]
            }
        )

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "token": token
        }