from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.database import mongodb
from app.routes.auth import router as auth_router
from app.routes.protected import router as protected_router
from app.core.handlers import register_exception_handlers
from app.middleware.logging import LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):

    await mongodb.connect()

    yield

    await mongodb.close()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

register_exception_handlers(app)

app.add_middleware(
    LoggingMiddleware
)

app.include_router(auth_router)
app.include_router(protected_router)

@app.get("/")
async def home():

    return {
        "success": True,
        "message": "Backend Running"
    }