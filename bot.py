import os
import threading
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import base64

TOKEN = os.environ.get("BOT_TOKEN")
SERVER_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
PORT = int(os.environ.get("SERVER_PORT", 5000))

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")
if not SERVER_URL:
    raise ValueError("RAILWAY_PUBLIC_DOMAIN environment variable is not set!")

global_bot = Bot(token=TOKEN)
app = Flask(__name__)

# Настройка логгера
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отключаем детальные HTTP-запросы из логов
logging.getLogger("httpx").setLevel(logging.WARNING)


def log_and_notify(level, message, chat_id=None, topic_id=None):
    """
    Логирует сообщение и отправляет его в тот же чат или топик, где произошла ошибка.
    
    level: уровень логирования (logging.ERROR, logging.WARNING)
    message: текст ошибки/предупреждения
    chat_id: ID чата (если известен)
    topic_id: ID топика (если известен)
    """
    log_type = "error" if level == logging.ERROR else "warning"

    if level == logging.ERROR:
        logger.error(message)
    else:
        logger.warning(message)

    # Если chat_id неизвестен, логируем только в консоль
    if not chat_id:
        logger.warning("⚠️ Логирование в Telegram пропущено: chat_id не задан.")
        return

    log_label = "🔴 ERROR" if log_type == "error" else "🟡 WARNING"
    log_message = f"{log_label}\n📝 {message}"

    try:
        # Получаем текущий event loop
        loop = asyncio.get_event_loop()

        # Создаем экземпляр бота
        local_bot = Bot(token=TOKEN)

        # Если event loop уже запущен, используем ensure_future
        if loop.is_running():
            if topic_id:
                # Если topic_id есть, отправляем в топик
                future = asyncio.ensure_future(local_bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    text=log_message,
                    parse_mode=ParseMode.HTML
                ))
            else:
                # Если topic_id нет, отправляем просто в чат
                future = asyncio.ensure_future(local_bot.send_message(
                    chat_id=chat_id,
                    text=log_message,
                    parse_mode=ParseMode.HTML
                ))
            future.add_done_callback(lambda fut: logger.info(f"✅ Лог ({log_type.upper()}) отправлен в чат {chat_id}"))
        else:
            # Если event loop не работает, используем run_until_complete
            if topic_id:
                loop.run_until_complete(local_bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    text=log_message,
                    parse_mode=ParseMode.HTML
                ))
            else:
                loop.run_until_complete(local_bot.send_message(
                    chat_id=chat_id,
                    text=log_message,
                    parse_mode=ParseMode.HTML
                ))

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке лога ({log_type.upper()}) в Telegram: {str(e)}")



def format_json_as_html(data):
    """
    Преобразует JSON в HTML-формат для Telegram.
    Убирает пустые строки, None и форматирует вложенные структуры.
    """
    if not data:
        logger.info("⚠️ Пустой JSON передан в format_json_as_html()")
        return ""

    if "text" in data and isinstance(data["text"], str) and data["text"].strip():
        logger.info(f"📝 Форматируем текстовое сообщение: {len(data['text'])} символов")
        return data["text"].strip()

    formatted_text = ""
    
    # Рекурсивная обработка вложенных структур
    def process_value(key, value, depth=0):
        indent = "  " * depth  # Отступы для читаемости
        
        if value is None or value == "":
            return ""  # Пропускаем пустые значения
        
        if isinstance(value, dict):
            sub_text = f"<b>{key}:</b>\n"
            for sub_key, sub_value in value.items():
                processed = process_value(sub_key, sub_value, depth + 1)
                if processed:
                    sub_text += f"{indent}  <i>{sub_key}:</i> {processed}\n"
            return sub_text.strip()

        elif isinstance(value, list):
            list_items = [str(item).strip() for item in value if item]  # Убираем пустые
            return f"<b>{key}:</b> " + ", ".join(list_items)

        else:
            return f"<b>{key}:</b> {str(value).strip()}"

    for key, value in data.items():
        processed = process_value(key, value)
        if processed:
            formatted_text += processed + "\n"

    formatted_text = formatted_text.strip()

    if not formatted_text:
        logger.info("⚠️ JSON содержит только пустые значения!")
        return ""

    logger.info(f"✅ JSON успешно преобразован в HTML, длина: {len(formatted_text)} символов")
    return formatted_text

def encode_params(chat_id, topic_id=None):
    """
    Кодирует chat_id и topic_id в Base64.
    - Если topic_id указан, кодируем chat_id + topic_id (для отправки сообщений в топик).
    - Если topic_id НЕ указан, кодируем ТОЛЬКО chat_id (для редактирования, удаления, получения текста).
    """
    try:
        # Преобразуем chat_id и topic_id в строки (на случай, если они int)
        chat_id = str(chat_id).strip()
        topic_id = str(topic_id).strip() if topic_id is not None else None

        # Проверяем, является ли chat_id корректным числом
        if not chat_id.lstrip("-").isdigit():
            raise ValueError(f"Некорректный chat_id: {chat_id}")

        # Создаем строку для кодирования
        raw_string = f"{chat_id}:{topic_id}" if topic_id else chat_id
        encoded_string = base64.urlsafe_b64encode(raw_string.encode()).decode()

        logger.info(f"✅ Кодировано: chat_id={chat_id}, topic_id={topic_id if topic_id else 'None'} → {encoded_string}")
        return encoded_string

    except Exception as e:
        error_message = f"❌ Ошибка кодирования: chat_id={chat_id}, topic_id={topic_id if topic_id else 'None'} → {str(e)}"
        log_and_notify(logging.ERROR, error_message, chat_id, topic_id)
        return None


def decode_params(encoded_string):
    """
    Декодирует Base64 в chat_id и topic_id.
    - Если код содержит ДВА параметра (chat_id:topic_id), то возвращает оба.
    - Если ОДИН параметр (chat_id), значит, topic_id не передавался.
    - В случае ошибки логирует проблему и возвращает (None, None).
    """
    if not encoded_string:
        log_and_notify(logging.WARNING, "⚠️ Пустая строка передана в decode_params()", chat_id, topic_id)
        return None, None

    try:
        # Проверяем, является ли строка корректным Base64
        padded_encoded = encoded_string + "=" * (-len(encoded_string) % 4)  # Делаем длину кратной 4
        decoded = base64.urlsafe_b64decode(padded_encoded).decode().strip()

        if ":" in decoded:
            chat_id, topic_id = decoded.split(":", 1)  # Ограничиваем split на 2 части
        else:
            chat_id, topic_id = decoded, None  # Если topic_id нет

        # Проверяем, является ли chat_id корректным числом (Telegram chat_id всегда число)
        if not chat_id.lstrip("-").isdigit():
            raise ValueError(f"Некорректный chat_id: {chat_id}")

        logger.info(f"✅ Декодирован chat_id={chat_id}, topic_id={topic_id if topic_id else 'None'}")
        return chat_id, topic_id

    except Exception as e:
        error_message = f"❌ Ошибка декодирования Base64 ({encoded_string}): {str(e)}"
        log_and_notify(logging.ERROR, error_message, chat_id, topic_id)
        return None, None



@app.route('/post/<encoded_params>', methods=['POST'])
def post_to_chat(encoded_params):
    """
    Отправляет сообщение в указанный чат или топик.
    """
    # Игнорируем GET-запросы
    if request.method == "GET":
        logger.info(f"⚠️ Игнорируем GET-запрос на /post/{encoded_params}")
        return jsonify({"error": "Method Not Allowed"}), 405
    
    # Декодируем chat_id и topic_id
    chat_id, topic_id = decode_params(encoded_params)
    if not chat_id:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})", chat_id, topic_id)
        return jsonify({"error": "Invalid parameters"}), 400

    # Получаем JSON-данные
    data = request.get_json()
    if not data:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка отправки: пустой JSON (chat_id={chat_id})", chat_id, topic_id)
        return jsonify({"error": "Invalid JSON"}), 400

    message = format_json_as_html(data)

    # Определяем, куда отправлять (General или топик)
    thread_id = None
    if topic_id and topic_id.lower() != "general":
        if topic_id.isdigit():
            thread_id = int(topic_id)
        else:
            log_and_notify(logging.WARNING, f"⚠️ Некорректный topic_id '{topic_id}' (chat_id={chat_id})", chat_id, topic_id)
            return jsonify({"error": "Invalid topic_id"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        local_bot = Bot(token=TOKEN)

        if thread_id is None:
            # Отправка в General
            sent_message = loop.run_until_complete(
                local_bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
            )
            logger.info(f"✅ Сообщение {sent_message.message_id} отправлено в General-чат {chat_id}")
        else:
            # Отправка в топик
            sent_message = loop.run_until_complete(
                local_bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML, message_thread_id=thread_id)
            )
            logger.info(f"✅ Сообщение {sent_message.message_id} отправлено в топик {thread_id} (чат {chat_id})")

        return jsonify({
            "success": "Message sent",
            "message_id": sent_message.message_id,
            "chat_id": chat_id,
            "thread_id": thread_id if thread_id else None
        })

    except Exception as e:
        log_and_notify(logging.ERROR, f"❌ Ошибка при отправке сообщения в чат {chat_id}: {str(e)}", chat_id, topic_id)
        return jsonify({"error": str(e)}), 500

    finally:
        loop.close()


@app.route('/edit/<encoded_params>/<message_id>', methods=['POST'])
def edit_message(encoded_params, message_id):
    """
    Редактирует сообщение в указанном чате или топике.
    """
    # Игнорируем GET-запросы
    if request.method == "GET":
        logger.info(f"⚠️ Игнорируем GET-запрос на /edit/{encoded_params}/{message_id}")
        return jsonify({"error": "Method Not Allowed"}), 405

    # Декодируем chat_id (topic_id не используется)
    chat_id, _ = decode_params(encoded_params)
    if not chat_id:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})", chat_id, None)
        return jsonify({"error": "Invalid parameters"}), 400

    # Проверяем message_id
    if not message_id.isdigit():
        log_and_notify(logging.WARNING, f"⚠️ Некорректный message_id '{message_id}' (chat_id={chat_id})", chat_id, None)
        return jsonify({"error": "Invalid message_id"}), 400

    # Получаем JSON-данные
    data = request.get_json()
    if not data or "text" not in data:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка редактирования: отсутствует 'text' (message_id={message_id}, chat_id={chat_id})", chat_id, None)
        return jsonify({"error": "Invalid JSON, 'text' is required"}), 400

    new_message = format_json_as_html(data)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        local_bot = Bot(token=TOKEN)

        loop.run_until_complete(
            local_bot.edit_message_text(
                chat_id=chat_id,
                message_id=int(message_id),
                text=new_message,
                parse_mode=ParseMode.HTML
            )
        )
        logger.info(f"✅ Сообщение {message_id} отредактировано в чате {chat_id}")
        return jsonify({"success": "Message edited", "message_id": message_id})

    except Exception as e:
        log_and_notify(logging.ERROR, f"❌ Ошибка при редактировании сообщения {message_id} в чате {chat_id}: {str(e)}", chat_id, None)
        return jsonify({"error": str(e)}), 500

    finally:
        loop.close()


@app.route('/delete/<encoded_params>/<message_id>', methods=['POST'])
def delete_message(encoded_params, message_id):
    """
    Удаляет сообщение в указанном чате.
    """
    # Игнорируем GET-запросы
    if request.method == "GET":
        logger.info(f"⚠️ Игнорируем GET-запрос на /delete/{encoded_params}/{message_id}")
        return jsonify({"error": "Method Not Allowed"}), 405

    # Декодируем chat_id (topic_id не используется)
    chat_id, _ = decode_params(encoded_params)
    if not chat_id:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})", chat_id, None)
        return jsonify({"error": "Invalid parameters"}), 400

    # Проверяем message_id
    if not message_id.isdigit():
        log_and_notify(logging.WARNING, f"⚠️ Некорректный message_id '{message_id}' (chat_id={chat_id})", chat_id, None)
        return jsonify({"error": "Invalid message_id"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        local_bot = Bot(token=TOKEN)

        loop.run_until_complete(
            local_bot.delete_message(
                chat_id=chat_id,
                message_id=int(message_id)
            )
        )
        logger.info(f"✅ Сообщение {message_id} удалено в чате {chat_id}")
        return jsonify({"success": f"Message {message_id} deleted"})

    except Exception as e:
        error_message = str(e)
        if "message to delete not found" in error_message:
            log_and_notify(logging.WARNING, f"⚠️ Сообщение {message_id} уже удалено или не найдено в чате {chat_id}.", chat_id, None)
            return jsonify({"warning": f"Message {message_id} already deleted or not found"}), 200
        elif "Message can't be deleted" in error_message:
            log_and_notify(logging.ERROR, f"⚠️ Сообщение {message_id} не может быть удалено в чате {chat_id}.\nБыло опубликовано более 48 часов назад.\nУдалите вручную!", chat_id, None)
            return jsonify({"error": f"Message {message_id} can't be deleted"}), 200
        else:
            log_and_notify(logging.ERROR, f"❌ Ошибка при удалении сообщения {message_id} в чате {chat_id}: {error_message}", chat_id, None)
            return jsonify({"error": error_message}), 500

    finally:
        loop.close()


@app.route('/get/<encoded_params>/<message_id>', methods=['GET'])
def get_message_text(encoded_params, message_id):
    """
    Получает текст сообщения из Telegram по message_id.
    """
    # Декодируем chat_id (topic_id не используется)
    chat_id, _ = decode_params(encoded_params)
    if not chat_id:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})", chat_id, None)
        return jsonify({"error": "Invalid parameters"}), 400

    # Проверяем message_id
    if not message_id.isdigit():
        log_and_notify(logging.WARNING, f"⚠️ Некорректный message_id '{message_id}' (chat_id={chat_id})", chat_id, None)
        return jsonify({"error": "Invalid message_id"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        local_bot = Bot(token=TOKEN)

        # Попытка получить информацию о чате (Telegram API не позволяет напрямую получать текст сообщения)
        chat = loop.run_until_complete(local_bot.get_chat(chat_id))

        if not chat:
            log_and_notify(logging.WARNING, f"⚠️ Чат {chat_id} не найден.", chat_id, None)
            return jsonify({"error": "Chat not found"}), 404

        # Здесь нужно использовать правильный API метод, forward_message не подходит
        message_text = f"⚠️ Получение сообщения {message_id} невозможно через API."  
        log_and_notify(logging.WARNING, f"⚠️ API Telegram не позволяет получить текст сообщения {message_id}.", chat_id, None)

        return jsonify({"text": message_text})

    except Exception as e:
        error_message = str(e)
        if "message to get not found" in error_message:
            log_and_notify(logging.WARNING, f"⚠️ Сообщение {message_id} не найдено в чате {chat_id}", chat_id, None)
            return jsonify({"error": "Message not found"}), 404
        else:
            log_and_notify(logging.ERROR, f"❌ Ошибка при получении текста сообщения {message_id} в чате {chat_id}: {error_message}", chat_id, None)
            return jsonify({"error": error_message}), 500

    finally:
        loop.close()


@app.route('/log/<log_type>/<encoded_chat>', methods=['POST'])
def log_message(log_type, encoded_chat):
    """
    Получает логи от Google Apps Script или других сервисов и отправляет их в нужный чат/топик.
    - Если лог пришел из топика → он отправляется в этот же топик.
    - Если топика нет → отправляем просто в чат.
    """
    # Игнорируем GET-запросы
    if request.method == "GET":
        logger.info(f"⚠️ Игнорируем GET-запрос на /log/{log_type}/{encoded_chat}")
        return jsonify({"error": "Method Not Allowed"}), 405

    # Декодируем chat_id и topic_id (если он есть)
    chat_id, topic_id = decode_params(encoded_chat)
    if not chat_id:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка декодирования chat_id ({encoded_chat})", chat_id, topic_id)
        return jsonify({"error": "Invalid parameters"}), 400

    # Получаем JSON-данные
    data = request.get_json()
    if not data or "message" not in data:
        log_and_notify(logging.WARNING, f"⚠️ Ошибка логирования: пустой JSON (chat_id={chat_id})", chat_id, topic_id)
        return jsonify({"error": "Invalid JSON, 'message' is required"}), 400

    log_text = format_json_as_html(data)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        local_bot = Bot(token=TOKEN)

        # Если лог пришел из топика, отправляем его обратно в этот же топик
        log_label = "🔴 ERROR" if log_type.lower() == "error" else "🟡 WARNING"
        log_message_text = f"{log_label}\n📝 {log_text}"

        if topic_id:
            sent_message = loop.run_until_complete(
                local_bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    text=log_message_text,
                    parse_mode=ParseMode.HTML
                )
            )
            logger.info(f"✅ Лог ({log_type.upper()}) отправлен в тот же топик {topic_id} (чат {chat_id})")
        else:
            sent_message = loop.run_until_complete(
                local_bot.send_message(
                    chat_id=chat_id,
                    text=log_message_text,
                    parse_mode=ParseMode.HTML
                )
            )
            logger.info(f"✅ Лог ({log_type.upper()}) отправлен в чат {chat_id}")

        return jsonify({"success": "Log sent", "message_id": sent_message.message_id})

    except Exception as e:
        log_and_notify(logging.ERROR, f"❌ Ошибка при отправке лога ({log_type.upper()}) в чат {chat_id}: {str(e)}", chat_id, topic_id)
        return jsonify({"error": str(e)}), 500

    finally:
        loop.close()


async def start(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает доступные команды.
    """
    if not update.message:
        return  # Предотвращаем ошибку, если сообщение отсутствует (например, callback-запрос)

    user = update.effective_user
    chat_id = str(update.message.chat_id)
    thread_id = update.message.message_thread_id  # Может быть None

    try:
        await update.message.reply_text(
            "👋 Привет! Вот доступные команды:\n\n"
            "📌 <b>Основные команды:</b>\n"
            "🔹 /commands - команды для работы с сообщениями\n"
            "🔹 /logging_commands - команды для логирования\n",
            parse_mode=ParseMode.HTML
        )
        logger.info(f"📢 Пользователь @{user.username} вызвал /start")
    except Exception as e:
        log_and_notify(logging.ERROR, f"❌ Ошибка в start: {str(e)}", chat_id, thread_id)


async def commands(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет ссылки для работы с сообщениями.
    """
    if not update.message:
        return  # Предотвращаем ошибку, если сообщение отсутствует (например, callback-запрос)

    user = update.effective_user
    chat_id = str(update.message.chat_id)
    thread_id = update.message.message_thread_id
    username = f"@{user.username}" if user.username else f"{user.first_name} {user.last_name or ''}".strip()

    encoded_general = encode_params(chat_id, "general")
    encoded_topic = encode_params(chat_id, str(thread_id)) if thread_id else None
    encoded_chat = encode_params(chat_id)
    
    try:
        if encoded_topic:
            await update.message.reply_text(
                f"📩 Отправить в топик: \n{SERVER_URL}/post/{encoded_topic}\n"
                f"✏️ Редактировать сообщение: \n{SERVER_URL}/edit/{encoded_chat}/<message_id>\n"
                f"📄 Получить текст сообщения: \n{SERVER_URL}/get/{encoded_chat}/<message_id>\n"
            )
            logger.info(f"📢 Пользователь {username} запросил ссылки для топика {thread_id} в чате {chat_id}")
        else:
            await update.message.reply_text(
                f"📩 Отправить в общий чат: \n{SERVER_URL}/post/{encoded_general}\n"
                f"✏️ Редактировать: \n{SERVER_URL}/edit/{encoded_chat}/<message_id>\n"
                f"🗑 Удалить сообщение: \n{SERVER_URL}/delete/{encoded_chat}/<message_id>\n"
                f"📄 Получить текст сообщения: \n{SERVER_URL}/get/{encoded_chat}/<message_id>\n"
            )
            logger.info(f"📢 Пользователь {username} запросил ссылки для General-чата {chat_id}")
    except Exception as e:
        log_and_notify(logging.ERROR, f"❌ Ошибка в сommands: {str(e)}", chat_id, thread_id)

async def logging_commands(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет ссылки для логирования ошибок и предупреждений.
    Если вызвано в топике, логирование будет в этот же топик.
    Если вызвано в общем чате, логирование будет в сам чат.
    """
    if not update.message:
        return

    user = update.effective_user
    chat_id = str(update.message.chat_id)
    thread_id = update.message.message_thread_id  # Определяем, в топике ли сообщение
    username = f"@{user.username}" if user.username else f"{user.full_name or 'Без имени'}"

    # Кодируем chat_id и topic_id (если есть)
    if thread_id:
        encoded_logging_chat = encode_params(chat_id, str(thread_id))  # Кодируем с topic_id
    else:
        encoded_logging_chat = encode_params(chat_id)  # Кодируем только chat_id

    try:
        # Формируем ссылки для логирования
        await update.message.reply_text(
            f"📌 <b>Логирование ошибок и предупреждений:</b>\n\n"
            f"🔴 <b>Отправить ERROR-лог:</b>\n"
            f"{SERVER_URL}/log/error/{encoded_logging_chat}\n\n"
            f"🟡 <b>Отправить WARNING-лог:</b>\n"
            f"{SERVER_URL}/log/warning/{encoded_logging_chat}\n\n"
            f"📢 Логи будут отправляться {'в этот топик' if thread_id else 'в этот чат'}.",
            parse_mode=ParseMode.HTML
        )


        logger.info(f"📢 Пользователь {username} запросил ссылки для логирования в {'топике ' + str(thread_id) if thread_id else 'General-чате'} (чат {chat_id})")
    except Exception as e:
        log_and_notify(logging.ERROR, f"❌ Ошибка в logging_commands: {str(e)}", chat_id, thread_id)


def run_flask():
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("commands", commands))
    application.add_handler(CommandHandler("logging_commands", logging_commands))
    application.add_handler(CommandHandler("start", start))
    application.run_polling()
