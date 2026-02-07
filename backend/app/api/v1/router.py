"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, clients, knowledge, chat, webhooks, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(knowledge.router, prefix="/clients/{client_id}/knowledge", tags=["knowledge"])
api_router.include_router(chat.router, prefix="/clients/{client_id}/chat", tags=["chat"])
api_router.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
