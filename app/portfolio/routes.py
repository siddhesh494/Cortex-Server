"""Unauthenticated routes for the portfolio about-me chatbot."""

from fastapi import APIRouter, status

from app.core.exceptions import PortfolioSessionNotFoundException
from app.core.response import ApiResponse
from app.portfolio.schemas import PortfolioAskRequest
from app.portfolio.service import PortfolioService

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)

portfolio_service = PortfolioService()


@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask_about_me(body: PortfolioAskRequest):
    """
    Public endpoint — no JWT required.

    Called from the portfolio site to answer questions about the owner.
    Pass sessionId to continue a conversation (expires after 30 minutes idle).
    """
    if not body.message.strip():
        return ApiResponse.error(
            message="message is required.",
            status_code=400,
            data={"error": "message is required."},
        )

    try:
        data = await portfolio_service.ask(body)
    except PortfolioSessionNotFoundException as exc:
        return ApiResponse.error(
            message=exc.message,
            status_code=404,
            data={"error": exc.message},
        )

    return ApiResponse.success(
        data=data.model_dump(),
        message="Success",
    )


@router.get("/health", status_code=status.HTTP_200_OK)
async def portfolio_health():
    return ApiResponse.success(
        data={"status": "ok"},
        message="Portfolio API is running.",
    )
