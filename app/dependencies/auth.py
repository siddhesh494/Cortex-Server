from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.core.exceptions import UnauthorizedException
security = HTTPBearer(auto_error=False)

user_repository = UserRepository()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Validates JWT token and returns the authenticated user.
    """

    if credentials is None:
        raise UnauthorizedException()

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException()

    user_id = payload.get("sub")

    if not user_id:
        raise UnauthorizedException()

    user = await user_repository.find_by_id(user_id)

    if user is None:
        raise UnauthorizedException()

    return user