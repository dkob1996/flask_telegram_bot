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


def format_json_as_html(data):
    """
    Преобразует JSON в HTML-формат для Telegram.
    """
    if not data:
        logger.warning("⚠️ Пустой JSON передан в format_json_as_html()")
        return ""

    if "text" in data:
        logger.info(f"📝 Форматируем текстовое сообщение: {len(data['text'])} символов")
        return data["text"]

    formatted_text = ""
    for key, value in data.items():
        if isinstance(value, dict):
            formatted_text += f"<b>{key}:</b>\n"
            for sub_key, sub_value in value.items():
                formatted_text += f"  <i>{sub_key}:</i> {sub_value}\n"
        elif isinstance(value, list):
            formatted_text += f"<b>{key}:</b> " + ", ".join(str(item) for item in value) + "\n"
        else:
            formatted_text += f"<b>{key}:</b> {value}\n"

    logger.info(f"✅ JSON успешно преобразован в HTML, длина: {len(formatted_text)} символов")
    return formatted_text.strip()

def encode_params(chat_id, topic_id):
    """
    Кодирует chat_id и topic_id в Base64.
    """
    raw_string = f"{chat_id}:{topic_id}"
    return base64.urlsafe_b64encode(raw_string.encode()).decode()

def decode_params(encoded_string):
    """
    Декодирует chat_id и topic_id из Base64.
    """
    try:
        decoded = base64.urlsafe_b64decode(encoded_string).decode()
        chat_id, topic_id = decoded.split(":")
        return chat_id, topic_id
    except Exception as e:
        logger.error(f"❌ Ошибка декодирования параметров: {str(e)}")
        return None, None

@app.route('/post/<encoded_params>', methods=['POST'])
def post_to_chat(encoded_params):
    """
    Отправляет сообщение в указанный чат или топик.
    """
    # Если Telegram делает GET-запрос, игнорируем его
    if request.method == "GET":
        logger.info(f"⚠️ Игнорируем GET-запрос на /post/{chat_id}/{topic_id}")
        return jsonify({"error": "Method Not Allowed"}), 405

    # Декодируем параметры
    chat_id, topic_id = decode_params(encoded_params)
    if not chat_id:
        logger.warning(f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})")
        return jsonify({"error": "Invalid parameters"}), 400

    data = request.get_json()
    if not data:
        logger.warning(f"⚠️ Ошибка отправки: пустой JSON (chat_id={chat_id})")
        return jsonify({"error": "Invalid JSON"}), 400

    message = format_json_as_html(data)
    thread_id = None if topic_id.lower() == "general" else int(topic_id)

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
        logger.error(f"❌ Ошибка при отправке сообщения в чат {chat_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        loop.close()


@app.route('/edit/<encoded_params>/<message_id>', methods=['POST'])
def edit_message(encoded_params, message_id):
    """
    Редактирует сообщение в указанном чате или топике.
    """
    # Если Telegram делает GET-запрос, игнорируем его
    if request.method == "GET":
        logger.info(f"⚠️ Игнорируем GET-запрос на /edit/{chat_id}/{message_id}")
        return jsonify({"error": "Method Not Allowed"}), 405

    # Декодируем chat_id и topic_id
    chat_id, _ = decode_params(encoded_params)
    if not chat_id:
        logger.warning(f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})")
        return jsonify({"error": "Invalid parameters"}), 400

    data = request.get_json()
    if not data or "text" not in data:
        logger.warning(f"⚠️ Ошибка редактирования: не передан 'text' (message_id={message_id}, chat_id={chat_id})")
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
        logger.error(f"❌ Ошибка при редактировании сообщения {message_id} в чате {chat_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()



@app.route('/delete/<encoded_params>/<message_id>', methods=['POST'])
def delete_message(encoded_params, message_id):
    """
    Удаляет сообщение в указанном чате.
    """
    # Декодируем chat_id и topic_id
    if request.method == "GET":
        logger.info(f"⚠️ Игнорируем GET-запрос на /delete/{chat_id}/{message_id}")
        return jsonify({"error": "Method Not Allowed"}), 405
    
    chat_id, _ = decode_params(encoded_params)
    if not chat_id:
        logger.warning(f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})")
        return jsonify({"error": "Invalid parameters"}), 400

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
        logger.error(f"❌ Ошибка при удалении сообщения {message_id} в чате {chat_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()


@app.route('/get/<encoded_params>/<message_id>', methods=['GET'])
def get_message_text(encoded_params, message_id):
    """
    Получает текст сообщения из Telegram по message_id.
    """
    # Декодируем chat_id и topic_id
    chat_id, _ = decode_params(encoded_params)
    if not chat_id:
        logger.warning(f"⚠️ Ошибка декодирования: некорректные параметры ({encoded_params})")
        return jsonify({"error": "Invalid parameters"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        local_bot = Bot(token=TOKEN)

        # Запрашиваем сообщение у Telegram
        updates = loop.run_until_complete(local_bot.get_updates())

        for update in updates:
            if update.message and update.message.chat_id == int(chat_id) and update.message.message_id == int(message_id):
                return jsonify({"text": update.message.text})

        logger.warning(f"⚠️ Сообщение {message_id} не найдено в чате {chat_id}")
        return jsonify({"error": "Message not found"}), 404

    except Exception as e:
        error_message = str(e)
        logger.error(f"❌ Ошибка при получении текста сообщения {message_id} в чате {chat_id}: {error_message}")
        return jsonify({"error": error_message}), 500

    finally:
        loop.close()


async def start(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет ссылки для отправки, редактирования, удаления и получения сообщений.
    Теперь chat_id и topic_id передаются в Base64.
    """
    user = update.effective_user
    chat_id = update.message.chat_id
    username = f"@{user.username}" if user.username else f"{user.first_name} {user.last_name or ''}".strip()

    # Кодируем chat_id и topic_id
    encoded_general = encode_params(chat_id, "general")
    encoded_topic = encode_params(chat_id, str(update.message.message_thread_id)) if update.message.message_thread_id else None

    if encoded_topic:
        await update.message.reply_text(
            f"📩 Отправить в топик: \n{SERVER_URL}/post/{encoded_topic}\n"
            f"✏️ Редактировать сообщение: \n{SERVER_URL}/edit/{encoded_topic}/<message_id>\n"
            f"📄 Получить текст сообщения: \n{SERVER_URL}/get/{encoded_topic}/<message_id>\n"
        )
        logger.info(f"📢 Пользователь {username} запросил ссылки для топика {update.message.message_thread_id} в чате {chat_id}")
    else:
        await update.message.reply_text(
            f"📩 Отправить в общий чат: \n{SERVER_URL}/post/{encoded_general}\n"
            f"✏️ Редактировать: \n{SERVER_URL}/edit/{encoded_general}/<message_id>\n"
            f"🗑 Удалить сообщение: \n{SERVER_URL}/delete/{encoded_general}/<message_id>\n"
            f"📄 Получить текст сообщения: \n{SERVER_URL}/get/{encoded_general}/<message_id>\n"
        )
        logger.info(f"📢 Пользователь {username} запросил ссылки для General-чата {chat_id}")





def run_flask():
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()
