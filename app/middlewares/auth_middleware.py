from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.dependencies import get_current_user_for_middleware, check_user_privileges
from app.core.logger import logger
from app.middlewares.context import current_user_context, request_context

class AuthenticationMiddleware(BaseHTTPMiddleware):

    public_endpoints: set[tuple[str,str]] = {
        ("GET",""),
        ("GET", "/docs"),
        ("GET", "/redoc"),
        ("GET", "/openapi.json"),
        ("POST", "/api/v1/auth/register"),
        ("POST", "/api/v1/auth/login"),
    }

    def _is_public_endpoint(self, api_path: str, method: str) -> bool:
        normalized_path = api_path.rstrip("/")
        return (method, normalized_path) in self.public_endpoints

    async def dispatch(self, request: Request, call_next):
        api_path = request.url.path
        method = request.method
        user_session = None

        try:
            request_context.set(
                {
                    "method": method,
                    "url_path": api_path,
                    "client_host": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("User-Agent", ""),
                    "query_params": dict(request.query_params),

                }
            )

            if method == "OPTIONS":
                return await call_next(request)

            if self._is_public_endpoint(api_path, method):
                return await call_next(request)

            user_session = await get_current_user_for_middleware(request)

            current_user_context.set(
                {
                    "user_id" : str(user_session.user_id),
                    "session_id":str(user_session.session_id),
                    "email": user_session.email,
                    "role": user_session.role

                }
            )

            check_user_privileges(user_session.role ,api_path, method)

            request.state.user = user_session
            response = await call_next(request)
            return response
        
        except HTTPException as exc:
            user_email = user_session.email if user_session else "unknown"
            logger.warning(f"Authentication failed for user {user_email} on {method} {api_path}: {exc.detail}",
                            extra = {
                                "method": method,
                                "path": api_path,
                                "client_host": request.client.host if request.client else "unknown",
                                "user_agent": request.headers.get("User-Agent", ""),
                        },
                        )
            return JSONResponse(status_code = exc.status_code, content = {"detail": exc.detail}, headers = exc.headers or {})
        
        except Exception as exc:
            user_email = user_session.email if user_session else "unknown"
            logger.error(f"Unexpected error in authentication middleware for user {user_email}: {str(exc)}",
                        extra = { 
                                "method": method,
                                "path": api_path,
                                "client_host": request.client.host if request.client else "unknown",
                                "user_agent": request.headers.get("User-Agent", ""),
                        },
                        exc_info = True
                        )
            return JSONResponse(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, content = {"detail": "An unexpected server error occurred during authentication"})
            

