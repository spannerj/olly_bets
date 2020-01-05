# -*- coding: utf-8 -*-
import telegram
from tweepy import StreamListener
from app import config


def from_creator(status):
    if hasattr(status, 'retweeted_status'):
        return False
    elif status.in_reply_to_status_id is not None:
        return False
    elif status.in_reply_to_screen_name is not None:
        return False
    elif status.in_reply_to_user_id is not None:
        return False
    else:
        return True


def send_message(message):
    bot = telegram.Bot(token=config.TELEGRAM_BOT_API_KEY)
    bot.send_message(chat_id='-1001190331415', text=message,
                     parse_mode=telegram.ParseMode.MARKDOWN)  # LR Jack's Tips
    # bot.send_message(chat_id='-1001456379435', text=message,
    #                  parse_mode=telegram.ParseMode.MARKDOWN)  # Spanners Playground


class Listener(StreamListener):
    def on_status(self, status):
        if from_creator(status):
            try:
                message = status.user.name + ' - ' + status.text
                print(message)
                send_message(message)
                return True
            except BaseException as e:
                print("Error on_data %s" % str(e))
            return True
        return True

    def on_error(self, status):
        print(self)
        print('error with status code ' + str(status))
