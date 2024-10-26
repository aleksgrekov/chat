# MyChat

MyChat — это веб-приложение для обмена сообщениями, построенное с использованием FastAPI, WebSocket и SQLAlchemy.
Приложение поддерживает создание чатов между пользователями, а также взаимодействует с Telegram-ботом для оповещений о
новых сообщениях.

## Функциональность

- Регистрация и авторизация пользователей
- Создание чатов между пользователями
- Обмен сообщениями в реальном времени с помощью WebSocket
- Telegram-оповещения о новых сообщениях

## Установка и запуск

1. Клонируйте репозиторий:

   git clone git@github.com:aleksgrekov/chat.git
   cd chat


2. Настройте файл Docker Compose. Убедитесь, что переменные среды (например, DATABASE_USER, DATABASE_PASSWORD,
   BOT_TOKEN) соответствуют вашим настройкам.

3. Запустите Docker Compose:

   docker-compose up --build

4. Приложение будет доступно по адресу [http://localhost:8000](http://localhost:8000).

### Основные эндпоинты

- `GET /mychat/chats/{username}`: Получение всех чатов пользователя
- `GET /mychat/chats/{username}/{chat_id}`: Просмотр чата с пользователем по chat_id
- `POST /mychat/new_chat`: Создание нового чата между пользователями
- WebSocket: /ws/chat для подключения к чату и получения сообщений в реальном времени

### Структура проекта

- `application/` — исходный код FastAPI приложения
- `bot/` — код Telegram-бота для оповещений
- `db/` — папка для хранения данных Postgres
- `Dockerfile` — конфигурация Docker для сборки приложения
- `docker-compose.yml` — конфигурация Docker Compose для развертывания всего приложения

### Переменные среды

DATABASE_USER Имя пользователя для базы данных
DATABASE_PASSWORD Пароль для базы данных
DATABASE_HOST Хост базы данных (в Docker обычно postgres)
DATABASE_PORT Порт базы данных (по умолчанию 5432)
DATABASE_NAME Название базы данных
BOT_TOKEN Токен Telegram-бота для отправки уведомлений
MYCHAT_URL URL приложения для отправки уведомлений

### Документация

http://localhost:8000/docs
