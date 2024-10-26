import re
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, ConfigDict


def validate_password(password):
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one digit.")
    return password


class LoginData(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Username must be between 3 and 30 characters."
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Password must be between 6 and 100 characters.")

    def model_post_init(self, __context):
        validate_password(self.password)


class UserRegistrationSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Username of the new user")
    password: str = Field(..., min_length=6, max_length=128, description="Password for the user account")
    first_name: str | None = Field(None, max_length=50, description="First name of the user")
    last_name: str | None = Field(None, max_length=50, description="Last name of the user")
    telegram: str | None = Field(None, description="Telegram handle of the user")

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        validate_password(self.password)


class UserSchema(BaseModel):
    id: int
    username: str
    first_name: str | None
    last_name: str | None
    telegram: str | None
    telegram_chat_id: int | None
    notice: bool

    model_config = ConfigDict(from_attributes=True)


class ChatSchema(BaseModel):
    id: int
    users: List[int | UserSchema]

    model_config = ConfigDict(from_attributes=True)


class MessageSchema(BaseModel):
    message: str
    datetime: datetime
    user: int | UserSchema

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    success: bool
    chat_id: int = None
    message: str = None


class NoticeData(BaseModel):
    username: str
    telegram: str
    notice: bool

class TelegramData(BaseModel):
    username: str
    chat_id: int
