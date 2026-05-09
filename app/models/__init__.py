"""Models package - Pydantic 请求/响应模型"""

from app.models.chat import ChatMessageSchema, TripChatRequest, TripChatResponse
from app.models.poi import POISchema, POIListResponse

__all__ = [
    "ChatMessageSchema",
    "TripChatRequest",
    "TripChatResponse",
    "POISchema",
    "POIListResponse",
]
