import os
import threading
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

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

# Глобальный бот используется только для Application (polling)
global_bot = Bot(token=TOKEN)
app = Flask(__name__)

def format_json_as_html(data):
    """
    Преобразует JSON в отформатированное HTML-сообщение для Telegram.
    """
    formatted_text = "<b>🔹 Новые данные:</b>\n"
    
    for key, value in data.items():
        if isinstance(value, dict):
            # Если значение - словарь, рекурсивно обрабатываем его
            formatted_text += f"<b>{key}:</b>\n"
            for sub_key, sub_value in value.items():
                formatted_text += f"  <i>{sub_key}:</i> {sub_value}\n"
        elif isinstance(value, list):
            # Если значение - список, отображаем элементы в строку
            formatted_text += f"<b>{key}:</b> " + ", ".join(str(item) for item in value) + "\n"
        else:
            # Обычные ключи-значения
            formatted_text += f"<b>{key}:</b> {value}\n"

    return formatted_text.strip()

@app.route('/post/<topic_id>', methods=['POST'])
def post_to_topic(topic_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    message = format_json_as_html(data)

    # Создаем новый event loop для этого запроса
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Создаем новый экземпляр бота, который использует новый цикл
        local_bot = Bot(token=TOKEN)
        if topic_id == "general":
            loop.run_until_complete(
                local_bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
            )
            return jsonify({"success": "Message sent to general chat"})
        else:
            try:
                thread_id = int(topic_id)
            except ValueError:
                return jsonify({"error": "topic_id must be an integer or 'general'"}), 400

            loop.run_until_complete(
                local_bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    message_thread_id=thread_id
                )
            )
            return jsonify({"success": "Message sent to topic", "topic_id": thread_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.message_thread_id:
        thread_id = update.message.message_thread_id
        await update.message.reply_text(
            f"Ссылка для отправки в ТОПИК: {SERVER_URL}/post/{thread_id}"
        )
    else:
        await update.message.reply_text(
            f"Ссылка для отправки в общий чат: {SERVER_URL}/post/general"
        )

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()
