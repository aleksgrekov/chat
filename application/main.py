from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.init import create_tables, delete_tables

from routers.chats import router as chat_router
from routers.auth import router as auth_router
from routers.notice_to_tg import router as notice_router


@asynccontextmanager
async def lifespan(fast_api: FastAPI):
    # await delete_tables()
    print("База очищена")
    await create_tables()
    print("База готова к работе")
    yield
    print("Выключение")


app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(notice_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
