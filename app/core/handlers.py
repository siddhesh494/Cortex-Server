from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.response import ApiResponse

from app.core.exceptions import (
    ChatNotFoundException,
    DocumentAlreadyUploadedException,
    EmptyDocumentException,
    InvalidCredentialsException,
    PortfolioSessionNotFoundException,
    RagIndexingException,
    UnauthorizedException,
    UnsupportedFileTypeException,
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

    @app.exception_handler(DocumentAlreadyUploadedException)
    async def document_already_uploaded_handler(
        request: Request,
        exc: DocumentAlreadyUploadedException,
    ):
        return ApiResponse.error(
            message=exc.message,
            status_code=400,
            data={"error": exc.message},
        )

    @app.exception_handler(UnsupportedFileTypeException)
    async def unsupported_file_type_handler(
        request: Request,
        exc: UnsupportedFileTypeException,
    ):
        return ApiResponse.error(
            message=exc.message,
            status_code=400,
            data={"error": exc.message},
        )

    @app.exception_handler(EmptyDocumentException)
    async def empty_document_handler(
        request: Request,
        exc: EmptyDocumentException,
    ):
        return ApiResponse.error(
            message=exc.message,
            status_code=400,
            data={"error": exc.message},
        )

    @app.exception_handler(RagIndexingException)
    async def rag_indexing_handler(
        request: Request,
        exc: RagIndexingException,
    ):
        return ApiResponse.error(
            message=exc.message,
            status_code=500,
            data={"error": exc.message},
        )

    @app.exception_handler(PortfolioSessionNotFoundException)
    async def portfolio_session_not_found_handler(
        request: Request,
        exc: PortfolioSessionNotFoundException,
    ):
        return ApiResponse.error(
            message=exc.message,
            status_code=404,
            data={"error": exc.message},
        )