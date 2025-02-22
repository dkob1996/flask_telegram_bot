import os
import threading
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SERVER_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
PORT = int(os.environ.get("SERVER_PORT", 5000))

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")
if not CHAT_ID:
    raise ValueError("CHAT_ID environment variable is not set!")
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

@app.route('/post/<topic_id>', methods=['POST'])
def post_to_topic(topic_id):
    """
    Отправляет сообщение в General или в топик.
    """
    data = request.get_json()
    if not data:
        logger.warning("⚠️ Ошибка отправки: пустой JSON")
        return jsonify({"error": "Invalid JSON"}), 400

    message = format_json_as_html(data)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        local_bot = Bot(token=TOKEN)
        thread_id = None

        if topic_id == "general":
            sent_message = loop.run_until_complete(
                local_bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
            )
            logger.info(f"✅ Сообщение {sent_message.message_id} отправлено в General-чат")
        else:
            try:
                thread_id = int(topic_id)
            except ValueError:
                logger.warning(f"⚠️ Ошибка отправки: topic_id '{topic_id}' не является числом")
                return jsonify({"error": "topic_id must be an integer or 'general'"}), 400

            sent_message = loop.run_until_complete(
                local_bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    message_thread_id=thread_id
                )
            )
            logger.info(f"✅ Сообщение {sent_message.message_id} отправлено в топик {thread_id}")

        return jsonify({
            "success": "Message sent",
            "message_id": sent_message.message_id,
            "thread_id": thread_id
        })

    except Exception as e:
        error_message = str(e)
        logger.error(f"❌ Ошибка при отправке сообщения: {error_message}")
        return jsonify({"error": error_message}), 500

    finally:
        loop.close()


@app.route('/edit/<message_id>', methods=['POST'])
def edit_message(message_id):
    """
    Редактирует сообщение в Telegram.
    """
    data = request.get_json()
    if not data or "text" not in data:
        logger.warning(f"⚠️ Ошибка редактирования: не передан 'text' (message_id={message_id})")
        return jsonify({"error": "Invalid JSON, 'text' is required"}), 400

    new_message = format_json_as_html(data)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        local_bot = Bot(token=TOKEN)
        loop.run_until_complete(
            local_bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=int(message_id),
                text=new_message,
                parse_mode=ParseMode.HTML
            )
        )
        logger.info(f"✅ Сообщение {message_id} успешно отредактировано.")
        return jsonify({"success": "Message edited", "message_id": message_id})

    except Exception as e:
        error_message = str(e)
        logger.error(f"❌ Ошибка при редактировании сообщения {message_id}: {error_message}")
        return jsonify({"error": error_message}), 500

    finally:
        loop.close()


@app.route('/delete/<message_id>', methods=['POST'])
def delete_message(message_id):
    """
    Удаляет сообщение из General-чата.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        local_bot = Bot(token=TOKEN)
        loop.run_until_complete(
            local_bot.delete_message(
                chat_id=CHAT_ID,
                message_id=int(message_id)
            )
        )
        logger.info(f"✅ Удалено сообщение {message_id} из General-чата")
        return jsonify({"success": f"Message {message_id} deleted"})
    
    except Exception as e:
        error_message = str(e)
        if "message to delete not found" in error_message:
            logger.warning(f"⚠️ Сообщение {message_id} уже удалено или не найдено.")
            return jsonify({"warning": f"Message {message_id} already deleted or not found"}), 200
        else:
            logger.error(f"❌ Ошибка при удалении сообщения {message_id}: {error_message}")
            return jsonify({"error": error_message}), 500
    finally:
        loop.close()

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет ссылки на отправку, редактирование и удаление сообщений.
    Удаление показываем только для General-чата.
    """
    if update.message and update.message.message_thread_id:
        thread_id = update.message.message_thread_id
        await update.message.reply_text(
            f"Ссылка для отправки в ТОПИК: {SERVER_URL}/post/{thread_id}\n"
            f"Редактировать: {SERVER_URL}/edit/<message_id>"
        )
        logger.info(f"📢 Пользователь {update.effective_user.id} запросил ссылки для топика {thread_id}")
    else:
        await update.message.reply_text(
            f"Ссылка для отправки в общий чат: {SERVER_URL}/post/general\n"
            f"Редактировать: {SERVER_URL}/edit/<message_id>\n"
            f"Удалить сообщение: {SERVER_URL}/delete/<message_id>"
        )
        logger.info(f"📢 Пользователь {update.effective_user.id} запросил ссылки для General-чата")


def run_flask():
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()
