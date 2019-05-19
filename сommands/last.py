import logging

log = logging.getLogger(__name__)


def last(bot, update):
    chat_id = update.message.chat.id
    bot.send_last_posts(chat_id)
