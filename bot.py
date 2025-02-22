import os
import threading
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
#from telegram.utils.request import Request

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

# Создаём Request с увеличенным пулом соединений и настраиваемыми таймаутами
#req = Request(con_pool_size=20, read_timeout=10, connect_timeout=10)
#bot = Bot(token=TOKEN, request=req)
bot = Bot(token=TOKEN)
app = Flask(__name__)

@app.route('/post/<topic_id>', methods=['POST'])
def post_to_topic(topic_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    message = f"<b>New Data:</b>\n<pre>{data}</pre>"
    try:
        # Создаем новый цикл событий для каждого запроса
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if topic_id == "general":
            loop.run_until_complete(
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
            )
            loop.close()
            return jsonify({"success": "Message sent to general chat"})
        else:
            try:
                thread_id = int(topic_id)
            except ValueError:
                loop.close()
                return jsonify({"error": "topic_id must be an integer or 'general'"}), 400

            loop.run_until_complete(
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    message_thread_id=thread_id
                )
            )
            loop.close()
            return jsonify({"success": "Message sent to topic", "topic_id": thread_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.message_thread_id:
        thread_id = update.message.message_thread_id
        await update.message.reply_text(f"Ссылка для отправки в ТОПИК: {SERVER_URL}/post/{thread_id}")
    else:
        await update.message.reply_text(f"Ссылка для отправки в общий чат: {SERVER_URL}/post/general")

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

