from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from database.init import create_tables, delete_tables, session2
from database.models import Message, Chat, User
from database.repositories import UserRepository

from routers.chats import router as chat_router
from routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(fast_api: FastAPI):
    await delete_tables()
    print("База очищена")
    await create_tables()

    async with session2:
        objs = [
            User(username='aleksgrekov', password=UserRepository.hash_password('d3664645D')),
            User(username='innarodinskaia', password='234', first_name='Inna', last_name='Grekova'),
            User(username='chegachega', first_name='Денис', password=UserRepository.hash_password('d3664645D')),
            User(username='mckensy', first_name='Саша', password=UserRepository.hash_password('d3664645D')),
            Chat(users=[1, 2]),
            Chat(users=[1, 3]),
            Message(user=1, chat=1, message='Привет!'),
            Message(user=2, chat=1, message='Привет!'),
        ]
        session2.add_all(objs)
        await session2.commit()
    print("База готова к работе")
    yield
    print("Выключение")


app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)
app.include_router(auth_router)

if __name__ == '__main__':
    uvicorn.run("main:app", port=8000, host='127.0.0.1')
