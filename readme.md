
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

- Для Windows
```bash
python -m venv myenv
myvenv\Scripts\activate
```

- Для Linux/MacOS
```bash
python3 -m venv myenv
source myenv/bin/activate
```

## 3. Установка необходимых библиотек

Для работы с Telegram-ботом и Flask, установите необходимые библиотеки с помощью pip:

- Способ 1. Через requirements.txt
```bash
pip install -r requirements.txt
```

- Способ 2. Вручную

1. Установка библиотеки для работы с Telegram:
```bash
pip install python-telegram-bot
```

2. Установка Flask для веб-сервера:
```bash
pip install flask
```

## 4. Размещение бота на хостинге

1. Я выбрал хостинг railway.app
2. Установил параметры окружения

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

