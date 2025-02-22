#import yaml
import os
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
import threading
'''
# Чтение конфигурации из YAML
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)
TOKEN = config["token"]
CHAT_ID = config["chat_id"]
SERVER_URL = config["server_url"]
PORT = config["server_port"]
'''
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SERVER_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
PORT = int(os.environ.get("SERVER_PORT", 5000))

print(TOKEN)
print(SERVER_URL)
print(PORT)

bot = Bot(token=TOKEN)
app = Flask(__name__)

# Храним ссылки на топики
topic_links = {}

@app.route('/post/<topic_id>', methods=['POST'])
def post_to_topic(topic_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    topic_id = int(topic_id)
    message = f"<b>New Data:</b>\n<pre>{data}</pre>"
    
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML, message_thread_id=topic_id)
        return jsonify({"success": "Message sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.message_thread_id:
        topic_id = update.message.message_thread_id
        topic_links[topic_id] = f"{SERVER_URL}/post/{topic_id}"
        await update.message.reply_text(f"Ссылка для отправки в ТОПИК: {SERVER_URL}/post/{topic_id}")
    else:
        topic_links["general"] = f"{SERVER_URL}/post/general"
        await update.message.reply_text(f"Ссылка для отправки в общий чат: {SERVER_URL}/post/general")

if __name__ == "__main__":
    def run_flask():
        app.run(host="0.0.0.0", port=PORT)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()