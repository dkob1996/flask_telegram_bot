
# Инструкция по настройке Telegram-бота с Flask

## 1. Получение токена бота для Телеграма

Для того чтобы получить токен для бота, выполните следующие шаги:

1. Откройте **Telegram** и найдите пользователя [**@BotFather**](https://t.me/BotFather).
2. Напишите команду `/start` для начала общения с BotFather.
3. Создайте нового бота, выполнив команду `/newbot`.
4. Следуйте инструкциям, чтобы выбрать имя для бота и получить его **токен**.

Токен будет выслан вам в сообщении. Скопируйте его для дальнейшего использования.

## 2. Создание виртуального окружения

Чтобы изолировать зависимости проекта, создайте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/MacOS
venv\Scripts\activate     # Для Windows
```

## 3. Установка необходимых библиотек

Для работы с Telegram-ботом и Flask, установите необходимые библиотеки с помощью pip:

1. Установка библиотеки для работы с Telegram:
```bash
pip install python-telegram-bot
```

2. Установка Flask для веб-сервера:
```bash
pip install flask
```

3. Установка библиотеки для работы с YAML-файлами:
```bash
pip install pyyaml
```

## 4. Создание YAML файла конфигурации

Создайте файл config.yaml, чтобы хранить настройки бота.

1. Создайте файл config.yaml в корне проекта.
2. Заполните файл следующим образом:
```yaml
server_url: "адрес_сервера"
token: "токен_бота"
chat_id: "-100айди_канала"
```
* `server_url`: адрес вашего сервера (например, `http://localhost:5000`).
* `token`: токен вашего бота, полученный от BotFather.
* `chat_id`: ID вашего канала в Telegram, куда будут отправляться сообщения.

## 5. Запуск бота в Telegram-канале

Для того чтобы бот начал работать в вашем канале:

1. Добавьте бота в ваш Telegram-канал.
2. В любом из топиков или в общем чате канала отправьте команду:
```bash
/start@имя_вашего_бота
```

Бот отреагирует на команду и отправит ссылку для отправки JSON в нужный топик или в общий чат.

---
Теперь ваш бот готов к работе! 🎉

