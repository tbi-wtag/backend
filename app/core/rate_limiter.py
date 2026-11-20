from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logger import logger


class RateLimiter:
    def __init__(self):
        try:
            self._limiter = Limiter(
                key_func=self.get_real_ip,
                enabled=settings.app.rate_limiter_enable,
                headers_enabled=True,
                storage_uri=settings.redis.url,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize rate limiter",
                extra={
                    "action": "Rate limiter initialization error",
                    "exception": repr(e),
                    "status": "Failed",
                },
            )
            raise RuntimeError("Failed to initialize rate limiter") from e

    @property
    def limiter(self) -> Limiter:
        return self._limiter

    @staticmethod
    def get_real_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return get_remote_address(request)

    def register_rate_limiter(self, app: FastAPI) -> None:
        try:
            app.state.limiter = self._limiter
            app.add_exception_handler(
                RateLimitExceeded, self.handle_rate_limit_exceeded  # type: ignore
            )
            logger.info("Rate limiter initialized successfully")
        except Exception as e:
            logger.error(
                "Rate limiter setup failed",
                extra={
                    "action": "Rate limiter initialization error",
                    "exception": repr(e),
                    "status": "Failed",
                },
            )
            raise RuntimeError("Failed to initialize rate limiter") from e

    @staticmethod
    async def handle_rate_limit_exceeded(
        request: Request, exc: RateLimitExceeded
    ) -> Response:
        client_ip = RateLimiter.get_real_ip(request)

        logger.warning(
            "Rate limit exceeded",
            extra={
                "action": "Rate limit exceeded",
                "client_ip": client_ip,
                "limit_details": exc.detail,
            },
        )

        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Rate limit exceeded: {exc.detail}. Please try again later."
            },
        )

        if hasattr(request.state, "view_rate_limit"):
            response = request.app.state.limiter._inject_headers(
                response, request.state.view_rate_limit
            )

        return response


rate_limiter = RateLimiter()
limiter = rate_limiter.limiter
