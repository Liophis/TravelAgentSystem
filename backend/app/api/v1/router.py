from fastapi import APIRouter

from app.api.v1 import admin, aigc, destinations, diaries, facilities, foods, health, indoor, map, recommendations, routes, search, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(aigc.router, prefix="/aigc", tags=["aigc"])
api_router.include_router(destinations.router, prefix="/destinations", tags=["destinations"])
api_router.include_router(diaries.router, prefix="/diaries", tags=["diaries"])
api_router.include_router(foods.router, prefix="/foods", tags=["foods"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(map.router, prefix="/map", tags=["map"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["facilities"])
api_router.include_router(indoor.router, prefix="/indoor", tags=["indoor"])
