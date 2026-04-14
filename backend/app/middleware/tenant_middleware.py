from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Extracts the tenant (organization) from the X-Tenant-ID header
    and attaches it to request.state for multi-tenancy support.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = request.headers.get("X-Tenant-ID")
        request.state.tenant_id = tenant_id
        return await call_next(request)
