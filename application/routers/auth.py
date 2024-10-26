from typing import Dict

from fastapi import APIRouter, Request, status, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import UserRepository
from database.init import create_session
from schemas import LoginData, UserRegistrationSchema

router = APIRouter(
    prefix="/mychat",
    tags=["Auth"],
)
templates = Jinja2Templates(directory="templates")


async def render_template(request: Request, template_name: str):
    return templates.TemplateResponse(request=request, name=template_name)


@router.get('/auth', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def authentication(request: Request):
    return await render_template(
        request=request, template_name="auth.html"
    )


@router.get('/registration', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def registration(request: Request):
    return await render_template(
        request=request, template_name="registration.html"
    )


@router.post('/check_data', status_code=status.HTTP_200_OK)
async def check_user_data(data: LoginData, db: AsyncSession = Depends(create_session)):
    user = await UserRepository.check_user(username=data.username, password=data.password, session=db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "No user with these username or password"})
    return


@router.post('/new_user', response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def add_user(user_data: UserRegistrationSchema, db: AsyncSession = Depends(create_session)):
    try:
        await UserRepository.add_user(data=user_data, session=db)
        return {
            "message":
                f'The user {user_data.username} has been successfully added'
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"msg": str(exc)})
