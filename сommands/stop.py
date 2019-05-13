import logging

log = logging.getLogger(__name__)


def stop(bot, update, job_queue):
    chat_id = update.message.chat.id
    bot.database.delete_user(chat_id)
    job = job_queue.get_jobs_by_name(f'{chat_id}_sender')
    if job:
        job[0].schedule_removal()
        log.info(f'user {chat_id} has left')
    else:
        log.warning(f'user {chat_id} tried to leave before adding')
