from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.core.response import ApiResponse
from app.schemas.chat import ChatRequestSchema
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/protected",
    tags=["Protected"]
)

chat_service = ChatService()

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

    data = await chat_service.chat(
        user_id=str(current_user["_id"]),
        body=body,
    )

    return ApiResponse.success(
        data=data,
        message="Success"
    )