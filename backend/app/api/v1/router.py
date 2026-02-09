"""API v1 router - aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.channels import router as channels_router
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.webhooks.instagram import router as instagram_webhook_router
from app.api.v1.webhooks.whatsapp import router as whatsapp_webhook_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(channels_router, prefix="/channels", tags=["channels"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

# Webhook routes (public, no auth - protected by signature verification)
api_router.include_router(
    whatsapp_webhook_router, prefix="/webhooks/whatsapp", tags=["webhooks"]
)
api_router.include_router(
    instagram_webhook_router, prefix="/webhooks/instagram", tags=["webhooks"]
)
