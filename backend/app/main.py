"""Wafaa AI Concierge - FastAPI Application.

Multi-tenant AI chatbot platform with RAG-powered responses.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.multi_tenant import TenantContext


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    logger.info("application_startup", env=settings.app_env)
    yield
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title="Wafaa AI Concierge",
    description="Multi-tenant AI chatbot platform with RAG-powered responses",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    """Middleware to manage tenant context per request.

    Ensures tenant context is cleared after each request.
    """
    try:
        response = await call_next(request)
        return response
    finally:
        TenantContext.clear()


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware to log requests.

    Logs request start and completion with timing.
    """
    start_time = datetime.utcnow()

    response = await call_next(request)

    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    logger.info(
        "request_complete",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )

    return response


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status with timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.app_env,
    }


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions.

    Args:
        request: Incoming request.
        exc: Exception that was raised.

    Returns:
        JSON error response.
    """
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.is_development else None,
        },
    )
