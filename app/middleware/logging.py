import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        start = time.time()

        logger.info(
            f"Incoming Request : {request.method} {request.url.path}"
        )

        response = await call_next(request)

        end = time.time()

        logger.info(
            f"Completed : {response.status_code} ({round(end-start,3)} sec)"
        )

        return response