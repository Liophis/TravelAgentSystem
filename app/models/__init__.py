"""Models package - Pydantic 请求/响应模型"""

from app.models.poi import POISchema, POIListResponse
from app.models.user import UserSchema, UserListResponse
from app.models.diary import TravelDiarySchema, TravelDiaryListResponse
from app.models.facility import FacilitySchema, FacilityListResponse

__all__ = [
    "POISchema",
    "POIListResponse",
    "UserSchema",
    "UserListResponse",
    "TravelDiarySchema",
    "TravelDiaryListResponse",
    "FacilitySchema",
    "FacilityListResponse",
]
