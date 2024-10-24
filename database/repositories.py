import hashlib
from json import loads
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Chat, Message
from schemas import UserRegistrationSchema, ChatSchema, UserSchema, MessageSchema


class UserRepository:
    @classmethod
    def hash_password(cls, password: str) -> str:
        md5_hash = hashlib.md5()
        md5_hash.update(password.encode('utf-8'))
        return md5_hash.hexdigest()

    @classmethod
    def compare_passwords(cls, password: str, hashed_password: str) -> bool:
        hashed_input = cls.hash_password(password)
        return hashed_input == hashed_password

    @classmethod
    async def add_user(cls, data: UserRegistrationSchema, session: AsyncSession) -> None:
        async with session:
            user_dict = data.model_dump()
            user_dict["password"] = cls.hash_password(user_dict.get("password"))
            user = User(**user_dict)
            session.add(user)
            await session.commit()

    @classmethod
    async def check_user(cls, username: str, password: str, session: AsyncSession) -> bool:
        async with session:
            try:
                query = select(User).where(User.username == username)

                result = await session.execute(query)
                user_models = result.scalars().one()
                return cls.compare_passwords(password, user_models.password)
            except NoResultFound:
                return False

    @classmethod
    async def get_user_by_username(cls, username: str, session: AsyncSession):
        async with session:
            query = select(User).where(User.username == username)

            result = await session.execute(query)
            user_model = result.scalars().one_or_none()
            return user_model

    @classmethod
    async def get_user_by_id(cls, user_id: int, session: AsyncSession):
        async with session:
            query = select(User).where(User.id == user_id)

            result = await session.execute(query)
            user_model = result.scalars().one_or_none()
            return user_model

    @classmethod
    async def validate_user_data(cls, user_id, session):
        user = await UserRepository.get_user_by_id(user_id, session)
        user_schema = UserSchema.model_validate(user)
        return user_schema


class ChatRepository:
    @classmethod
    async def get_users_chats(cls, username, session: AsyncSession) -> List[ChatSchema | None] | None:
        async with session:
            user_data = await UserRepository.get_user_by_username(username, session)
            if not user_data:
                return None

            query = select(Chat).filter(Chat.users.any(user_data.id))
            request = await session.execute(query)
            result = request.scalars().all()

            chat_schema = [await cls.validate_chats_data(chat, user_data.id, session) for chat in result]

        return chat_schema

    @classmethod
    async def validate_chats_data(cls, chat_model, username_id, session):
        chat_schema = ChatSchema.model_validate(chat_model)

        new_users_field = [
            await UserRepository.validate_user_data(user_id, session)
            for user_id in chat_schema.users
            if user_id != username_id
        ]
        chat_schema.users = new_users_field
        return chat_schema


class MessageRepository:
    @classmethod
    async def get_chat_messages(cls, chat_id: int, user: str, session: AsyncSession):
        query = select(Message).where(Message.chat == chat_id)
        request = await session.execute(query)
        result = request.scalars().all()

        messages = [await MessageRepository.validate_message_data(mes) for mes in result]
        return messages

    @classmethod
    async def validate_message_data(cls, mes: Message):
        message = MessageSchema.model_validate(mes)
        message.user = UserSchema.model_validate(mes.user_data)
        return message

    @classmethod
    async def save_message(cls, session: AsyncSession, data: dict):
        async with session:
            user = await UserRepository.get_user_by_username(data.get('user'), session)
            data['user'] = user.id
            message = Message(**data)
            session.add(message)
            await session.commit()
