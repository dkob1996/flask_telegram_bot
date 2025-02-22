import os
import threading
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

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

@app.route('/post/<chat_id>/<topic_id>', methods=['POST'])
def post_to_chat(chat_id, topic_id):
    """
    Отправляет сообщение в указанный чат или топик.
    """
    data = request.get_json()
    if not data:
        logger.warning(f"⚠️ Ошибка отправки: пустой JSON (chat_id={chat_id})")
        return jsonify({"error": "Invalid JSON"}), 400

    message = format_json_as_html(data)
    thread_id = None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        local_bot = Bot(token=TOKEN)

        # Определяем, отправка идёт в топик или General
        if topic_id.lower() == "general":
            sent_message = loop.run_until_complete(
                local_bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
            )
            logger.info(f"✅ Сообщение {sent_message.message_id} отправлено в General-чат {chat_id}")
        else:
            try:
                thread_id = int(topic_id)
            except ValueError:
                logger.warning(f"⚠️ Ошибка: topic_id '{topic_id}' не является числом (chat_id={chat_id})")
                return jsonify({"error": "topic_id must be an integer or 'general'"}), 400

            sent_message = loop.run_until_complete(
                local_bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    message_thread_id=thread_id
                )
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



@app.route('/edit/<chat_id>/<message_id>', methods=['POST'])
def edit_message(chat_id, message_id):
    """
    Редактирует сообщение в указанном чате или топике.
    """
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


@app.route('/delete/<chat_id>/<message_id>', methods=['POST'])
def delete_message(chat_id, message_id):
    """
    Удаляет сообщение в указанном чате.
    """
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

@app.route('/get/<chat_id>/<message_id>', methods=['GET'])
def get_message_text(chat_id, message_id):
    """
    Получает текст сообщения из Telegram по message_id.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        local_bot = Bot(token=TOKEN)
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
    """
    user = update.effective_user
    chat_id = update.message.chat_id
    username = f"@{user.username}" if user.username else f"{user.first_name} {user.last_name or ''}".strip()

    if update.message and update.message.message_thread_id:
        thread_id = update.message.message_thread_id
        await update.message.reply_text(
            f"Ссылка для отправки в ТОПИК: {SERVER_URL}/post/{chat_id}/{thread_id}\n"
            f"Редактировать: {SERVER_URL}/edit/{chat_id}/<message_id>\n"
            f"Удалить сообщение: {SERVER_URL}/delete/{chat_id}/<message_id>\n"
            f"Получить текст сообщения: {SERVER_URL}/get/{chat_id}/<message_id>\n"
        )
        logger.info(f"📢 Пользователь {username} запросил ссылки для топика {thread_id} в чате {chat_id}")
    else:
        await update.message.reply_text(
            f"Ссылка для отправки в общий чат: {SERVER_URL}/post/{chat_id}/general\n"
            f"Редактировать: {SERVER_URL}/edit/{chat_id}/<message_id>\n"
            f"Удалить сообщение: {SERVER_URL}/delete/{chat_id}/<message_id>\n"
            f"Получить текст сообщения: {SERVER_URL}/get/{chat_id}/<message_id>\n"
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
