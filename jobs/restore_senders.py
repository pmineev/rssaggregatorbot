import logging
import time

import config
from keyboard_markups import yesno_keyboard

log = logging.getLogger(__name__)


def button(bot, update, job_queue):
    query = update.callback_query
    answer = query.data
    chat_id = query.message.chat_id
    if answer == 'restore_yes':
        log.info(f'{chat_id} agreed')
        job_queue.run_repeating(bot.send_new_posts,
                                interval=config.DEFAULT_UPDATE_INTERVAL,
                                first=0,
                                context=chat_id,
                                name=f'{chat_id}_sender')
    else:
        log.info(f'{chat_id} refused')
        job_queue.run_repeating(bot.send_new_posts,
                                interval=config.DEFAULT_UPDATE_INTERVAL,
                                context=chat_id,
                                name=f'{chat_id}_sender')

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)


def restore_senders(bot, job_queue):
    log.info('Restoring senders')
    current_time = time.time()
    users = bot.database.get_users()
    for user in users:
        log.info(f'Restoring sender for {user.chat_id}')
        next_update_date = user.last_updated_date + user.update_interval
        if next_update_date > current_time:
            job_queue.run_repeating(bot.send_new_posts,
                                    interval=config.DEFAULT_UPDATE_INTERVAL,
                                    first=next_update_date - current_time,
                                    context=user.chat_id,
                                    name=f'{user.chat_id}_sender')
        else:
            bot.send_message(chat_id=user.chat_id,
                             text='Бот не работал продолжительное время. Хотите получить неотправленные сообщения?',
                             reply_markup=yesno_keyboard('restore'))
