from datetime import timedelta

from app.config import settings


ACCESS_TOKEN_EXPIRE = timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)