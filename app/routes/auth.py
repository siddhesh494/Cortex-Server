from fastapi import APIRouter, status

from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.core.response import ApiResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

auth_service = AuthService()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
async def register(body: RegisterRequest):

    data = await auth_service.register(body)

    return ApiResponse.success(
        data=data,
        message="User registered successfully.",
        status_code=201
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK
)
async def login(body: LoginRequest):

    data = await auth_service.login(body)

    return ApiResponse.success(
        data=data,
        message="Login successful."
    )