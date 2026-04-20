from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = {"from_attributes": True}
