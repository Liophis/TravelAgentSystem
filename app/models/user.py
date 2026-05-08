from pydantic import BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    """User Schema for API requests/responses"""
    id: int | None = None
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr
    interests: str | None = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Response for user list"""
    total: int
    items: list[UserSchema]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = {"from_attributes": True}
