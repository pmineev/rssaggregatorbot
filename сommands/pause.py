import logging

log = logging.getLogger(__name__)


def pause(_, update, job_queue):
    chat_id = update.message.chat.id
    job = job_queue.get_jobs_by_name(f'{chat_id}_sender')
    if job:
        job[0].enabled = False
        update.message.reply_text('Отправка сообщений приостановлена')
        log.info(f'user {chat_id} has paused sending')
    else:
        log.warning(f'user {chat_id} tried to pause before adding')
