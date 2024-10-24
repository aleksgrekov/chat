from datetime import datetime
from json import loads, dumps

from fastapi import APIRouter, Request, status, Depends, Query, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ChatRepository, MessageRepository
from database.init import create_session  # session

router = APIRouter(
    prefix="/mychat",
    tags=["Chat"],
)
templates = Jinja2Templates(directory="templates")


@router.get('/chats/{username}', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def chats(
        request: Request,
        username: str = Path(
            ...,
            title="username of the registered user"),
        db: AsyncSession = Depends(create_session)
):
    my_chats = await ChatRepository.get_users_chats(username=username, session=db)

    return templates.TemplateResponse(
        "chats.html",
        {"request": request, "chats": my_chats, "current_username": username}
    )


@router.get('/chats/{username}/{chat_id}')
async def chat_with_user(
        request: Request,
        username: str = Path(
            ...,
            title="username of the registered user"),
        chat_id: int = Path(
            ...,
            title="chat id"
        ),
        db: AsyncSession = Depends(create_session)

):
    messages = await MessageRepository.get_chat_messages(chat_id=chat_id, user=username, session=db)
    # return {
    #         "messages": messages,
    #         "username": username
    #     }
    return templates.TemplateResponse(
        "chat_with_user.html",
        {
            "request": request,
            "messages": messages,
            "username": username,
            "chat_id": chat_id
        }
    )


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
