from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque
from contextlib import AsyncExitStack, asynccontextmanager
from threading import Lock

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from fastmcp.utilities.logging import get_logger


logger = get_logger(__name__)

READ_ONLY_OPERATION_IDS = {
    "list_documentations",
    "list_documentation_sections",
    "get_section_content",
    "get_documentation_tree",
    "search_documentation",
}

MCP_TOOL_NAMES = {operation_id: operation_id for operation_id in READ_ONLY_OPERATION_IDS}


class MCPBearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str):
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next) -> Response:
        # Allow CORS preflight through; auth is enforced on actual MCP calls.
        if request.method == "OPTIONS":
            return await call_next(request)

        header = request.headers.get("authorization", "")
        if not header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = header[len("Bearer ") :].strip()
        if not token or not secrets.compare_digest(token, self._token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int, window_seconds: int):
        super().__init__(app)
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        client_id = request.client.host if request.client else "unknown"
        now = time.monotonic()
        earliest = now - self._window_seconds

        with self._lock:
            bucket = self._requests[client_id]
            while bucket and bucket[0] <= earliest:
                bucket.popleft()
            if len(bucket) >= self._max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )
            bucket.append(now)

        return await call_next(request)


class MCPRequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "mcp_request method=%s path=%s status=%s duration_ms=%.2f has_auth=%s",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                bool(request.headers.get("authorization")),
            )


def _map_route_to_mcp(route, current_type: MCPType) -> MCPType:
    if route.operation_id in READ_ONLY_OPERATION_IDS:
        return MCPType.TOOL
    return MCPType.EXCLUDE


def create_mcp_server(app: FastAPI) -> FastMCP:
    return FastMCP.from_fastapi(
        app=app,
        name=f"{settings.app_name}-mcp",
        route_map_fn=_map_route_to_mcp,
        mcp_names=MCP_TOOL_NAMES,
    )


def create_mcp_http_app(app: FastAPI):
    server = create_mcp_server(app)
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id"],
        ),
        Middleware(MCPRequestLoggingMiddleware),
        Middleware(
            InMemoryRateLimitMiddleware,
            max_requests=settings.mcp_rate_limit_max_requests,
            window_seconds=settings.mcp_rate_limit_window_seconds,
        ),
        Middleware(MCPBearerAuthMiddleware, token=settings.mcp_server_token),
    ]
    return server.http_app(
        path="/mcp",
        middleware=middleware,
        transport="streamable-http",
        stateless_http=True,
        json_response=True,
    )


def mount_mcp_server(app: FastAPI) -> None:
    mcp_http_app = create_mcp_http_app(app)
    existing_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def combined_lifespan(parent_app):
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(existing_lifespan(parent_app))
            await stack.enter_async_context(mcp_http_app.lifespan(mcp_http_app))
            yield

    app.router.lifespan_context = combined_lifespan
    # Mount at root so the MCP app owns /mcp directly and clients that target
    # /mcp (without trailing slash) do not get stuck on redirect handling.
    app.mount("/", mcp_http_app)
