# Flask Telegram Bot

### Оглавление
- [Описание проекта](#a-описание-проекта)
- [Функционал](#b-функционал)
- [Использованные библиотеки](#c-использованные-библиотеки)
- [Создание бота в BotFather](#d-создание-бота-в-botfather)
- [Развертывание на RailwayApp](#e-развертывание-на-railwayapp)
- Дополнительно: [Readme на английском языке](https://github.com/dkob1996/flask_telegram_bot/blob/main/README.md)


![Project logo](https://github.com/dkob1996/flask_telegram_bot/blob/main/images/logo.png)


## A. Описание проекта

Этот бот предназначен для работы с сообщениями в Telegram, а также для логирования ошибок и предупреждений.<br> 
Он поддерживает отправку, редактирование, удаление и получение сообщений в чатах и топиках.<br> 
Бот также позволяет отправлять логи ошибок и предупреждений, что делает его полезным для интеграции с другими сервисами и автоматизации рабочих процессов.

## B. Функционал

1. Отправка сообщений в чаты и топики.

2. Редактирование сообщений по `message_id`.

3. Удаление сообщений по `message_id`.

4. Получение текста сообщения по `message_id`.

5. Логирование ошибок и предупреждений в чаты и топики.

6. Команды для удобного использования бота:

* `/start` – показать доступные команды.

* `/commands` – ссылки для работы с сообщениями.

* `/logging_commands` – ссылки для логирования.

### Примеры использования функций

#### Отправка сообщения

Запрос (POST):
```json
POST {SERVER_URL}/post/{encoded_chat}
Content-Type: application/json

{
  "text": "Привет, мир!"
}
```
#### Редактирование сообщения

Запрос (POST):
```json
POST {SERVER_URL}/edit/{encoded_chat}/{message_id}
Content-Type: application/json

{
  "text": "Обновленный текст сообщения"
}
```

#### Удаление сообщения

Запрос (POST):
```json
POST {SERVER_URL}/delete/{encoded_chat}/{message_id}
```

#### Получение текста сообщения

Запрос (GET):
```json
POST {SERVER_URL}/delete/{encoded_chat}/{message_id}
```

#### Логирование ошибки

Запрос (POST):
```json
POST {SERVER_URL}/log/error/{encoded_chat}
Content-Type: application/json

{
  "message": "Ошибка в обработке данных"
}
```

#### Логирование предупреждения

Запрос (POST):
```json
POST {SERVER_URL}/log/warning/{encoded_chat}
Content-Type: application/json

{
  "message": "Внимание: возможная ошибка"
}
```
## C. Использованные библиотеки

Проект использует следующие библиотеки:

* `Flask==2.2.5` – веб-сервер для обработки HTTP-запросов.

* `python-telegram-bot==20.3` – взаимодействие с Telegram API.

Файл `requirements.txt` содержит список необходимых библиотек:
```json
Flask==2.2.5
python-telegram-bot==20.3
```

### Использование virtualenv

Рекомендуется использовать виртуальное окружение для установки зависимостей:
* Windows
```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```
* Mac / Linux
```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

## D. Создание бота в BotFather

1. Откройте Telegram и найдите `@BotFather`.

2. Отправьте команду `/newbot`.

3. Укажите имя бота и его username.

4. Получите токен API (BOT_TOKEN) – сохраните его, он понадобится позже.

## E. Развертывание на railway.app

### Подготовка проекта

1. Создайте аккаунт на `railway.app`.

2. Создайте новый проект.

3. Подключите репозиторий с кодом бота.

### Получение имени сервера

1. Зайдите в ваше развертывание

2. Перейдите во вкладку `Settings`

3. В разделе `Networking`

* Найдите `Public Networking`

* Выберете сгенерировать адрес

### Настройка переменных окружения

1. Задайте следующие переменные окружения:

* `BOT_TOKEN` – API-токен бота из BotFather.

* `SERVER_PORT` – порт для работы Flask (по умолчанию 5000).

2. Переменная домена будет создана автоматически:

* `RAILWAY_PUBLIC_DOMAIN` – домен, который Railway выдаст для вашего приложения.

### Procfile

Файл Procfile используется для запуска бота на Railway:
```makefile
web: python bot.py
```

### Деплой проекта

1. Запушьте код в репозиторий.

2. Railway автоматически развернет приложение.

3. Проверьте логи работы бота в Railway Dashboard.

Теперь ваш бот готов к работе!
