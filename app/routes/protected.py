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