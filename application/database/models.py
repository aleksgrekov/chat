from datetime import datetime
from typing import List

from sqlalchemy import String, ForeignKey, ARRAY, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from database.init import Model


class User(Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50))
    telegram: Mapped[str | None]
    telegram_chat_id: Mapped[int | None]
    notice: Mapped[bool] = mapped_column(default=False)

    user_messages = relationship(
        'Message',
        backref=backref('user_data',
                        cascade='all',
                        lazy='joined')
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, name={self.username}, password={self.password}, "
            f"first_name={self.first_name}, last_name={self.last_name}, telegram={self.telegram})>"
        )


class Message(Model):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    chat: Mapped[int] = mapped_column(ForeignKey('chats.id'), nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    datetime: Mapped['datetime'] = mapped_column(default=datetime.now())  # timezone.utc

    def __repr__(self) -> str:
        return (f"<Message(id={self.id}, user={self.user}, chat={self.chat},"
                f"message={self.message}, datetime={self.datetime})>")


class Chat(Model):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    users: Mapped[List[int]] = mapped_column(ARRAY(Integer), nullable=False, unique=True)

    chat_messages = relationship('Message', backref='user_chats')

    def __repr__(self):
        return f"<Chat(id={self.id}, users={self.users})>"
