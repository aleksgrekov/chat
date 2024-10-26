import asyncio
import os

import aiohttp
import bcrypt
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Chat, Message
from schemas import UserRegistrationSchema, ChatSchema, UserSchema, MessageSchema

URL = f'https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage'


class UserRepository:
    @classmethod
    def hash_password(cls, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @classmethod
    def compare_passwords(cls, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @classmethod
    async def add_user(cls, data: UserRegistrationSchema, session: AsyncSession) -> None:
        user_dict = data.model_dump()
        user_dict["password"] = cls.hash_password(user_dict.get("password"))
        user = User(**user_dict)
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise ValueError("User already exists")

    @classmethod
    async def check_user(cls, username: str, password: str, session: AsyncSession) -> bool:
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        user = result.scalars().one_or_none()
        return user is not None and UserRepository.compare_passwords(password, user.password)

    @classmethod
    async def get_user_by_username(cls, username: str, session: AsyncSession) -> Optional[UserSchema]:
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        user = result.scalars().one_or_none()
        return UserSchema.model_validate(user) if user else None

    @classmethod
    async def get_user_by_id(cls, user_id: int, session: AsyncSession) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    async def validate_user_data(cls, user_id: int, session: AsyncSession) -> Optional[UserSchema]:
        user = await UserRepository.get_user_by_id(user_id, session)
        return UserSchema.model_validate(user) if user else None

    @classmethod
    async def update_user_notice(cls, username: str, telegram: str, notice: bool, session: AsyncSession) -> None:
        query = update(User).where(User.username == username).values(telegram=telegram, notice=notice)
        await session.execute(query)
        await session.commit()

    @classmethod
    async def update_chat_id(cls, username: str, chat_id: int, session: AsyncSession) -> None:
        query = update(User).where(User.telegram == username).values(telegram_chat_id=chat_id)
        await session.execute(query)
        await session.commit()


class ChatRepository:
    @classmethod
    async def get_users_chats(cls, username: str, session: AsyncSession) -> Optional[List[ChatSchema]]:
        user_data = await UserRepository.get_user_by_username(username, session)
        if not user_data:
            return None

        query = select(Chat).filter(Chat.users.any(user_data.id))
        result = await session.execute(query)
        chats = result.scalars().all()

        return [await cls.validate_chats_data(chat, user_data.id, session) for chat in chats]

    @classmethod
    async def validate_chats_data(cls, chat_model: Chat, username_id: int, session: AsyncSession) -> ChatSchema:
        chat_schema = ChatSchema.model_validate(chat_model)
        chat_schema.users = [
            await UserRepository.validate_user_data(user_id, session)
            for user_id in chat_schema.users
            if user_id != username_id
        ]
        return chat_schema

    @classmethod
    async def get_chat_by_id(cls, chat_id: int, session: AsyncSession) -> Optional[Chat]:
        query = select(Chat).where(Chat.id == chat_id)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    async def send_messages_to_users(cls, user_ids: List[int], user: UserSchema, session: AsyncSession) -> None:
        tasks = [
            cls.send_notice_to_user_if_enabled(user_id, user, session)
            for user_id in user_ids if user_id != user.id
        ]
        await asyncio.gather(*tasks)

    @classmethod
    async def send_notice_to_user_if_enabled(cls, user_id: int, user: UserSchema, session: AsyncSession) -> None:
        target_user = await UserRepository.get_user_by_id(user_id, session)
        if target_user and target_user.notice:
            await cls.send_message_to_tg(target_user.telegram_chat_id, user)

    @classmethod
    async def send_message_to_tg(cls, tg: int, from_user: UserSchema):
        payload = {
            'chat_id': tg,
            'text': 'У вас новое сообщение от пользователя '
                    + (f'{from_user.first_name} {from_user.last_name}'
                       if from_user.first_name and from_user.last_name
                       else f'{from_user.username}')
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as client:
            await client.post(URL, json=payload)

    @classmethod
    async def send_notice_to_user(cls, chat_id: int, session: AsyncSession, username: str) -> None:
        user = await UserRepository.get_user_by_username(username, session)
        chat = await cls.get_chat_by_id(chat_id, session)
        if chat and user:
            await cls.send_messages_to_users(chat.users, user, session)

    @classmethod
    async def add_new_chat(cls, cur_user: str, target_user: str, session: AsyncSession) -> Optional[int]:
        cur_user_obj = await UserRepository.get_user_by_username(cur_user, session)
        target_user_obj = await UserRepository.get_user_by_username(target_user, session)

        if cur_user_obj and target_user_obj:

            new_chat = Chat(users=sorted([cur_user_obj.id, target_user_obj.id]))
            session.add(new_chat)
            try:
                await session.flush()
                await session.commit()
                return new_chat.id
            except IntegrityError:
                raise ValueError('Chat with this user already exists')
        return None


class MessageRepository:
    @classmethod
    async def get_chat_messages(cls, chat_id: int, session: AsyncSession) -> List[MessageSchema]:
        query = select(Message).where(Message.chat == chat_id).order_by(Message.datetime)
        result = await session.execute(query)
        messages = result.scalars().all()
        return [await MessageRepository.validate_message_data(message) for message in messages]

    @classmethod
    async def validate_message_data(cls, mes: Message) -> MessageSchema:
        message_schema = MessageSchema.model_validate(mes)
        message_schema.user = UserSchema.model_validate(mes.user_data)
        return message_schema

    @classmethod
    async def save_message(cls, session: AsyncSession, data: dict) -> None:
        user = await UserRepository.get_user_by_username(data.get('user'), session)
        if user:
            data['user'] = user.id
            message = Message(**data)
            session.add(message)
            await session.flush()
            await session.commit()
