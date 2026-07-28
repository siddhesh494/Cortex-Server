from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.response import ApiResponse

from app.core.exceptions import (
    ChatNotFoundException,
    InvalidCredentialsException,
    UnauthorizedException,
    UserAlreadyExistsException,
)


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(UserAlreadyExistsException)
    async def user_exists_handler(
        request: Request,
        exc: UserAlreadyExistsException,
    ):

        return ApiResponse.error(
            message=exc.message,
            status_code=409
        )

    @app.exception_handler(InvalidCredentialsException)
    async def invalid_credentials_handler(
        request: Request,
        exc: InvalidCredentialsException,
    ):

        return ApiResponse.error(
            message=exc.message,
            status_code=401
        )

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(
        request: Request,
        exc: UnauthorizedException,
    ):

        return ApiResponse.error(
            message=exc.message,
            status_code=401
        )

    @app.exception_handler(ChatNotFoundException)
    async def chat_not_found_handler(
        request: Request,
        exc: ChatNotFoundException,
    ):

        return ApiResponse.error(
            message=exc.message,
            status_code=404
        )