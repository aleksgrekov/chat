import bcrypt
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Chat, Message
from schemas import UserRegistrationSchema, ChatSchema, UserSchema, MessageSchema


class UserRepository:
    @classmethod
    def hash_password(cls, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @classmethod
    def compare_passwords(cls, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    # @classmethod
    # def hash_password(cls, password: str) -> str:
    #     md5_hash = hashlib.md5()
    #     md5_hash.update(password.encode('utf-8'))
    #     return md5_hash.hexdigest()
    #
    # @classmethod
    # def compare_passwords(cls, password: str, hashed_password: str) -> bool:
    #     hashed_input = cls.hash_password(password)
    #     return hashed_input == hashed_password

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
        # async with session:
        #     try:
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        user = result.scalars().one_or_none()
        return user is not None and UserRepository.compare_passwords(password, user.password)

    @classmethod
    async def get_user_by_username(cls, username: str, session: AsyncSession) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    async def get_user_by_id(cls, user_id: int, session: AsyncSession) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    async def validate_user_data(cls, user_id: int, session: AsyncSession) -> Optional[UserSchema]:
        user = await UserRepository.get_user_by_id(user_id, session)
        return UserSchema.model_validate(user) if user else None


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
        query = select(Message).where(Message.chat == chat_id)
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
            await session.commit()
