from fastapi import APIRouter

from app.api.v1 import facilities, health, map, routes

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(map.router, prefix="/map", tags=["map"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["facilities"])
