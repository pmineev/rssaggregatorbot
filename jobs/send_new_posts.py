import logging
import time

log = logging.getLogger(__name__)


def send_new_posts(bot, job):
    chat_id = job.context
    log.info(f'Sending new posts to {chat_id}')
    posts = bot.database.get_new_posts(chat_id)
    if posts:
        bot.send_posts(chat_id, posts)
        bot.database.set_last_updated_date(chat_id, int(time.time()))
