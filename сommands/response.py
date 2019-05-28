import logging
import time

from telegram import ForceReply

log = logging.getLogger(__name__)


def response(_, update):
    chat_id = update.message.chat.id
    log.info(f'user {chat_id} wants to say something!')
    update.message.reply_text('Что вы хотите сказать?',
                              reply_markup=ForceReply())
    return 0


def enter(bot, update):
    chat_id = update.message.chat.id
    user_input_text = update.message.text
    log.info(f'user {chat_id} says: {user_input_text}')
    bot.database.add_response(chat_id, user_input_text, time.time())
    update.message.reply_text('Спасибо за отзыв')

    return -1
