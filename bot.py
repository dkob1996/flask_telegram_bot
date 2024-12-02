import telebot

TOKEN = "7844253183:AAEYCdClT8GPhYm6q3-pjKwB_rBIVM8zjG8"
bot = telebot.TeleBot(TOKEN, parse_mode=None)

bot.send_message(chat_id="@ВАШ_ЮЗЕРНЕЙМ_КАНАЛА", text="Привет из бота!")

bot.polling(none_stop=True)


# python3 -m venv myenv
# source myenv/bin/activate  # Активировать виртуальное окружение
# pip install pyTelegramBotAPI