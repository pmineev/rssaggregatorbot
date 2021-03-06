import logging

import config
import сommands.sources as sources
from jobs.send_new_posts import send_new_posts
from keyboard_markups import yesno_keyboard

log = logging.getLogger(__name__)


def start(bot, update, job_queue):
    chat_id = update.message.chat.id
    bot.database.add_user(chat_id)
    log.info(f'new user {chat_id}')
    job_queue.run_repeating(send_new_posts,
                            interval=config.DEFAULT_UPDATE_INTERVAL,
                            context=chat_id,
                            name=f'{chat_id}_sender')
    update.message.reply_text('Добро пожаловать.\n'
                              'Хотите выбрать источники?',
                              reply_markup=yesno_keyboard('start'))
    return 0


def button(bot, update):
    query = update.callback_query
    answer = query.data
    chat_id = query.message.chat_id

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)

    if answer == 'start_yes':
        log.info(f'{chat_id} wants to choose sources')
        sources.choose(bot, update)
        return 1
    else:
        log.info(f'{chat_id} refuses to choose sources')
    return -1
