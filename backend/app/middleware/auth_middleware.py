from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_token
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Attaches the decoded user_id to request.state for downstream access."""

    EXCLUDE_PATHS = {"/health", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/docs", "/api/v1/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
                request.state.user_id = payload.get("sub")
            except ValueError:
                request.state.user_id = None
        else:
            request.state.user_id = None

        return await call_next(request)
