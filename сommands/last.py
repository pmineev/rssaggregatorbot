import logging

from telegram import ForceReply

log = logging.getLogger(__name__)


def last(_, update):
    chat_id = update.message.chat.id
    log.info(f'user {chat_id} requests last posts')
    update.message.reply_text('Введите количество постов',
                              reply_markup=ForceReply())
    return 0


def enter(bot, update):
    chat_id = update.message.chat.id
    user_input_count = update.message.text
    if user_input_count.isdigit() and int(user_input_count) > 0:
        count = int(user_input_count)
        bot.send_last_posts(chat_id, count)
        log.info(f'user {chat_id} wants {count} last posts')
        return -1
    else:
        update.message.reply_text('Количество постов быть натуральным числом')
        return -1