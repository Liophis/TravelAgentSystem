from pydantic import BaseModel, Field


class ChatMessageSchema(BaseModel):
    role: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=1)


class TripChatRequest(BaseModel):
    message: str = Field(min_length=1)
    trip_plan: dict
    history: list[ChatMessageSchema] = Field(default_factory=list)


class TripChatResponse(BaseModel):
    success: bool
    reply: str
