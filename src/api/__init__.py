from fastapi import APIRouter

from .routers.organizations_router import router as organizations_router

api_router = APIRouter(prefix="/v1")

api_router.include_router(organizations_router)
