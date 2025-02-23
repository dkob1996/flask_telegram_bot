# Flask Telegram Bot

### Table of Contents
- [Project Description](#a-project-description)
- [Functionality](#b-functionality)
- [Used Libraries](#c-used-libraries)
- [Creating a Bot in BotFather](#d-creating-a-bot-in-botfather)
- [Deployment on RailwayApp](#e-deployment-on-railwayapp)
- Extra: [Readme on Russian language](https://github.com/dkob1996/flask_telegram_bot/blob/main/readme_ru.md)

## A. Project Description

This bot is designed to work with messages in Telegram and also for logging errors and warnings.<br> 
It supports sending, editing, deleting, and retrieving messages in chats and topics.<br> 
The bot also allows sending logs of errors and warnings, which makes it useful for integration with other services and automation of workflows.

## B. Functionality

1. Sending messages to chats and topics.

2. Editing messages by `message_id`.

3. Deleting messages by `message_id`.

4. Retrieving message text by `message_id`.

5. Logging errors and warnings in chats and topics.

6. Commands for easy use of the bot:

* `/start` – show available commands.

* `/commands` – links for working with messages.

* `/logging_commands` – links for logging.

### Function Usage Examples

#### Sending a Message

Request (POST):
```json
POST {SERVER_URL}/post/{encoded_chat}
Content-Type: application/json

{
  "text": "Hello, world!"
}
```
#### Editing a Message

Request (POST):
```json
POST {SERVER_URL}/edit/{encoded_chat}/{message_id}
Content-Type: application/json

{
  "text": "Updated message text"
}
```

#### Deleting a Message

Request (POST):
```json
POST {SERVER_URL}/delete/{encoded_chat}/{message_id}
```

#### Retrieving Message Text

Request (GET):
```json
POST {SERVER_URL}/delete/{encoded_chat}/{message_id}
```

#### Logging an Error

Request (POST):
```json
POST {SERVER_URL}/log/error/{encoded_chat}
Content-Type: application/json

{
  "message": "Error in data processing"
}
```

#### Logging a Warning

Request (POST):
```json
POST {SERVER_URL}/log/warning/{encoded_chat}
Content-Type: application/json

{
  "message": "Warning: potential error"
}
```
## C. Used Libraries

The project uses the following libraries:

* `Flask==2.2.5` – web server for handling HTTP requests.

* `python-telegram-bot==20.3` – interaction with the Telegram API.

The `requirements.txt` file contains the list of required libraries:
```json
Flask==2.2.5
python-telegram-bot==20.3
```

### Using virtualenv

It is recommended to use a virtual environment to install dependencies:
* Windows
```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```
* Mac / Linux
```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

## D. Creating a Bot in BotFather

1. Open Telegram and find `@BotFather`.

2. Send the command `/newbot`.

3. Provide the bot's name and username.

4. Get the API token (BOT_TOKEN) – save it as you'll need it later.

## E. Deployment on railway.app

### Preparing the Project

1. Create an account on `railway.app`.

2. Create a new project.

3. Connect the repository with the bot's code.

### Getting the Server Name

1. Go to your deployment.

2. Navigate to the `Settings` tab.

3. In the `Networking` section:

* Find `Public Networking`.

* Choose to generate the address.

### Setting Up Environment Variables

1. Set the following environment variables:

* `BOT_TOKEN` – the bot's API token from BotFather.

* `SERVER_PORT` – the port for Flask to run on (default is 5000).

2. The domain variable will be created automatically:

* `RAILWAY_PUBLIC_DOMAIN` – the domain Railway will assign to your application.

### Procfile

The `Procfile` is used to run the bot on Railway:
```makefile
web: python bot.py
```

### Deploying the Project

1. Push the code to the repository.

2. Railway will automatically deploy the app.

3. Check the bot's logs in the Railway Dashboard.

Your bot is now ready to work!