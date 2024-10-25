from datetime import datetime
from json import loads
from typing import Dict, Any

from fastapi import APIRouter, Request, status, Depends, Path, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ChatRepository, MessageRepository
from database.init import create_session  # session
from schemas import ChatResponse

router = APIRouter(
    prefix="/mychat",
    tags=["Chat"],
)
templates = Jinja2Templates(directory="templates")


async def render_template(request: Request, template_name: str, context: dict):
    return templates.TemplateResponse(request=request, name=template_name, context=context)


@router.get('/chats/{username}', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def chats(
        request: Request,
        username: str = Path(..., title="username of the registered user"),
        db: AsyncSession = Depends(create_session)
):
    my_chats = await ChatRepository.get_users_chats(username=username, session=db)
    return await render_template(
        request,
        "chats.html",
        {"chats": my_chats, "current_username": username})
    # return templates.TemplateResponse(
    #     "chats.html",
    #     {"request": request, "chats": my_chats, "current_username": username}
    # )


@router.get('/chats/{username}/{chat_id}', response_class=HTMLResponse)
async def chat_with_user(
        request: Request,
        username: str = Path(..., title="Username of the registered user"),
        chat_id: int = Path(..., title="Chat ID"),
        db: AsyncSession = Depends(create_session)
):
    messages = await MessageRepository.get_chat_messages(chat_id=chat_id, session=db)
    return await render_template(
        request,
        "chat_with_user.html",
        {
            "messages": messages,
            "username": username,
            "chat_id": chat_id
        }
    )
    # return templates.TemplateResponse(
    #     "chat_with_user.html",
    #     {
    #         "request": request,
    #         "messages": messages,
    #         "username": username,
    #         "chat_id": chat_id
    #     }
    # )


@router.post('/new_chat', status_code=status.HTTP_201_CREATED, response_model=ChatResponse)
async def add_new_chat(
        current_user: str = Body(..., title="Username of the current user"),
        target_user: str = Body(..., title="Username of the target user"),
        db: AsyncSession = Depends(create_session)
):
    try:
        chat_id = await ChatRepository.add_new_chat(cur_user=current_user, target_user=target_user, session=db)
        if chat_id:
            return ChatResponse(success=True, chat_id=chat_id)
        return ChatResponse(success=False, message="User doesn't exist")
    except ValueError as exc:
        return ChatResponse(success=False, message=str(exc))


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket,
                             db: AsyncSession = Depends(create_session)):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            data_dict = loads(data)
            data_dict['datetime'] = datetime.fromisoformat(data_dict.get('datetime')[:-1])
            await MessageRepository.save_message(db, data_dict)
            await websocket.send_text(data)
    except WebSocketDisconnect:
        print(f"Пользователь отключился от WebSocket")
    except Exception as e:
        print(f"An error occurred: {e}")
