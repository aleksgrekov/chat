from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.init import create_session
from database.repositories import UserRepository
from schemas import NoticeData, TelegramData

router = APIRouter(
    prefix="/mychat",
    tags=["Notice"],
)


@router.patch('/change_notice', status_code=status.HTTP_200_OK)
async def change_notice(user: NoticeData, db: AsyncSession = Depends(create_session)):
    await UserRepository.update_user_notice(user.username, user.telegram, user.notice, db)


@router.patch("/update_telegram_id", status_code=status.HTTP_200_OK)
async def update_telegram_id(data: TelegramData, db: AsyncSession = Depends(create_session)):
    await UserRepository.update_chat_id(data.username, data.chat_id, db)
