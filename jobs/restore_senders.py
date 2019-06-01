import logging
import time

import config
from jobs.check_interval import check_interval
from jobs.send_new_posts import send_new_posts

log = logging.getLogger(__name__)


def button(bot, update, job_queue):
    query = update.callback_query
    answer = query.data
    chat_id = query.message.chat_id
    if answer == 'restore_yes':
        log.info(f'{chat_id} agreed')
        job_queue.run_repeating(send_new_posts,
                                interval=config.DEFAULT_UPDATE_INTERVAL,
                                first=0,
                                context=chat_id,
                                name=f'{chat_id}_sender')
    else:
        log.info(f'{chat_id} refused')
        job_queue.run_repeating(send_new_posts,
                                interval=config.DEFAULT_UPDATE_INTERVAL,
                                context=chat_id,
                                name=f'{chat_id}_sender')
        bot.database.set_last_updated_date(chat_id, time.time())

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)


def restore_senders(bot, job_queue):
    log.info('Restoring senders')
    current_time = time.time()
    users = bot.database.get_users()
    for user in users:
        log.info(f'Restoring sender for {user.chat_id}')
        if check_interval(bot, user, 'restore'):
            job_queue.run_repeating(send_new_posts,
                                    interval=config.DEFAULT_UPDATE_INTERVAL,
                                    first=user.last_updated_date + user.update_interval - current_time,
                                    context=user.chat_id,
                                    name=f'{user.chat_id}_sender')