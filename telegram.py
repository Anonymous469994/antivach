import telebot

#####################################################################

api_token = "BOTFATHERABULOH"
chat_id = "-4242424242424244"

#####################################################################


def escape_text_message(text):
    text = text.replace('<br>', '')
    return text


def send_text_message(message_text):
    #text = escape_text_message(message_text)
    bot = telebot.TeleBot(api_token)
    bot.send_message(chat_id, message_text)


def send_document(file_path):
    with open(file_path, 'rb') as f:
        bot = telebot.TeleBot(api_token)
        bot.send_document(chat_id=chat_id, data=f, disable_notification=True)


def send_media_group(files_list):
    bot = telebot.TeleBot(api_token)
    bot.send_media_group(chat_id=chat_id, media=files_list,
                         disable_notification=True)
