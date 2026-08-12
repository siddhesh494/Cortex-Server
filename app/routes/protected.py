import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from app.core.exceptions import (
    ChatNotFoundException,
    DocumentAlreadyUploadedException,
    EmptyDocumentException,
    RagIndexingException,
    UnsupportedFileTypeException,
)
from app.core.response import ApiResponse
from app.dependencies.auth import get_current_user
from app.rag.extractors import supported_extensions
from app.schemas.chat import ChatRequestSchema, UploadedDocument
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/protected",
    tags=["Protected"]
)

chat_service = ChatService()

_MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB


@router.get("/")
async def protected_route(
    current_user=Depends(get_current_user),
):
    return ApiResponse.success(
        data={
            "userId": str(current_user["_id"])
        },
        message="Authenticated successfully."
    )


@router.get("/chat/history")
async def chat_history(
    current_user=Depends(get_current_user),
):
    history = await chat_service.get_chat_history(
        user_id=str(current_user["_id"]),
    )

    return ApiResponse.success(
        data=[
            item.model_dump(mode="json")
            for item in history
        ],
        message="Chat history fetched successfully.",
    )


@router.get("/chat/{chat_id}")
async def get_chat(
    chat_id: str,
    current_user=Depends(get_current_user),
):
    chat = await chat_service.get_chat_by_id(
        user_id=str(current_user["_id"]),
        chat_session_id=chat_id,
    )

    return ApiResponse.success(
        data=chat.model_dump(mode="json"),
        message="Chat fetched successfully.",
    )


@router.post("/chat")
async def chat(
    body: ChatRequestSchema,
    current_user=Depends(get_current_user),
):
    if not (body.message or "").strip():
        return ApiResponse.error(
            message="message is required.",
            status_code=400,
            data={"error": "message is required."},
        )

    data = await chat_service.chat(
        user_id=str(current_user["_id"]),
        body=body,
    )

    return ApiResponse.success(
        data=data,
        message="Success"
    )


@router.post("/chat/stream")
async def chat_stream(
    message: str = Form(""),
    chatSessionId: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user=Depends(get_current_user),
):
    user_id = str(current_user["_id"])
    cleaned_session_id = (chatSessionId or "").strip() or None
    cleaned_message = (message or "").strip()

    uploaded: UploadedDocument | None = None
    if file is not None and file.filename:
        uploaded = await _read_upload(file)

    if not cleaned_message and uploaded is None:
        return ApiResponse.error(
            message="Provide a message and/or a PDF/TXT file.",
            status_code=400,
            data={"error": "Provide a message and/or a PDF/TXT file."},
        )

    if uploaded is not None:
        try:
            await chat_service.assert_document_allowed(
                user_id=user_id,
                chat_session_id=cleaned_session_id,
            )
        except DocumentAlreadyUploadedException as exc:
            return ApiResponse.error(
                message=exc.message,
                status_code=400,
                data={"error": exc.message},
            )
        except ChatNotFoundException as exc:
            return ApiResponse.error(
                message=exc.message,
                status_code=404,
                data={"error": exc.message},
            )

    body = ChatRequestSchema(
        message=cleaned_message,
        chatSessionId=cleaned_session_id,
    )

    async def event_generator():
        try:
            async for event in chat_service.chat_stream(
                user_id=user_id,
                body=body,
                document=uploaded,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except ChatNotFoundException:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Chat not found'})}\n\n"
        except DocumentAlreadyUploadedException as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': exc.message})}\n\n"
        except UnsupportedFileTypeException as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': exc.message})}\n\n"
        except EmptyDocumentException as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': exc.message})}\n\n"
        except RagIndexingException as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': exc.message})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _read_upload(file: UploadFile) -> UploadedDocument:
    filename = file.filename or "upload.bin"
    extension = Path(filename).suffix.lower()

    if extension not in supported_extensions():
        raise UnsupportedFileTypeException(filename)

    content = await file.read()
    if not content:
        raise EmptyDocumentException()

    if len(content) > _MAX_UPLOAD_BYTES:
        raise RagIndexingException(
            "Uploaded file is too large. Maximum size is 15 MB."
        )

    return UploadedDocument(filename=filename, content=content)
