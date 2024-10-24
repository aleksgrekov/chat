from typing import Dict

from fastapi import APIRouter, Request, status, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import UserRepository
from database.init import create_session  # session
from schemas import LoginData, UserRegistrationSchema

router = APIRouter(
    prefix="/mychat",
    tags=["Auth"],
)
templates = Jinja2Templates(directory="templates")


@router.get('/auth', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def authentication(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth.html"
    )


@router.get('/registration', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def registration(request: Request):
    return templates.TemplateResponse(
        request=request, name="registration.html"
    )


@router.post('/check_data', status_code=status.HTTP_200_OK)
async def check_user_data(data: LoginData, db: AsyncSession = Depends(create_session)):
    user = await UserRepository.check_user(username=data.username, password=data.password, session=db)

    if not user:
        raise HTTPException(
            status_code=404,
            detail={"msg": "No user with these username or password"})
    return


@router.post('/new_user', response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def add_user(user_data: UserRegistrationSchema, db: AsyncSession = Depends(create_session)):
    await UserRepository.add_user(data=user_data, session=db)
    return {
        "message":
            f'The user {user_data.username} has been successfully added'
    }
