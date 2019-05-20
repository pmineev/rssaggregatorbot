import logging
import time

from jobs.check_interval import check_interval

log = logging.getLogger(__name__)


def button(bot, update):
    query = update.callback_query
    answer = query.data
    chat_id = query.message.chat_id
    if answer == 'resume_yes':
        log.info(f'{chat_id} agreed')
        bot.send_new_posts(bot, update)
    else:
        log.info(f'{chat_id} refused')
        bot.database.set_last_updated_date(chat_id, int(time.time()))

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)


def resume(bot, update, job_queue):
    chat_id = update.message.chat.id
    job = job_queue.get_jobs_by_name(f'{chat_id}_sender')
    if job:
        user = bot.database.get_user(chat_id)
        job[0].enabled = True
        log.info(f'user {chat_id} has resumed sending')
        check_interval(bot, user, 'resume')
    else:
        log.warning(f'user {chat_id} tried to pause before adding')