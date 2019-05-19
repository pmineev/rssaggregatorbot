import logging
import time

import telegram
from telegram.ext import MessageQueue
from telegram.ext.messagequeue import queuedmessage

import db
import rss_utils
import sourceparsers

log = logging.getLogger(__name__)


# TODO управление количеством сообщений в минуту


class RssBot(telegram.bot.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        log.info('Bot started')
        self._is_messages_queued_default = True
        self._msg_queue = MessageQueue(all_burst_limit=2, all_time_limit_ms=2000)

        self.database = db.Database()

        threads = []
        for name, parser in sourceparsers.sources.items():
            threads.append(rss_utils.ParseThread(parser, self.database, name=name))
            log.info('created {} thread'.format(name))

        for t in threads:
            t.start()

    @queuedmessage
    def send_message(self, *args, **kwargs):
        super().send_message(*args, **kwargs)

    @queuedmessage
    def send_photo(self, *args, **kwargs):
        super().send_photo(*args, **kwargs)

    def send_posts(self, chat_id, posts):
        log.info(f'Sending {len(posts)} posts to {chat_id}')
        for post in posts:
            text = '{}\n{}'.format(post.title, post.link)
            if post.img_link and len(text) < 200:
                self.send_photo(chat_id=chat_id,
                                photo=post.img_link,
                                caption=f'{post.title}\n{post.link}')
            else:
                self.send_message(chat_id=chat_id,
                                  text=f'{post.summary}\n{post.link}')

    def send_new_posts(self, job):
        chat_id = job.context
        log.info(f'Sending new posts to {chat_id}')
        posts = self.database.get_new_posts(chat_id)
        if posts:
            self.send_posts(chat_id, posts)
            self.database.set_last_updated_date(chat_id, int(time.time()))

    def send_last_posts(self, chat_id):
        log.info(f'Sending last posts to {chat_id}')
        posts = self.database.get_last_posts(chat_id)
        if posts:
            self.send_posts(chat_id, posts)


# TODO завести класс PostEntity для пересылки сообщений в базу и из базы

#     def get_sorted_users(self):
#         users_sources = self.database.get_users_sources()
#         sorted_users = {}
#         for user_source in users_sources:
#             sorted_users.setdefault(user_source[1], []).append(user_source[0])
#         return sorted_users
#
#     def get_new_posts(self, sources):
#         sorted_posts = {}
#         for source in sources:
#             posts = self.database.get_new_posts_by_source(source)
#             if posts:
#                 sorted_posts[source] = posts
#         return sorted_posts
#
#     def mark_as_sent_by_source(self, sources):
#         self.database.mark_as_sent_by_source(sources)
#
#
# def send_new_messages(bot, job):
#     sorted_users = bot.get_sorted_users()
#     posts = bot.get_new_posts(sorted_users.keys())
#     log.info('Sending {} posts'.format(sum(len(posts[s]) for s in posts)))
#     if posts:
#         for source in posts:
#             for chat_id in sorted_users[source]:
#                 log.info('Sending {} messages from {} to {}'.format(len(posts[source]), source, chat_id))
#                 for post in posts[source]:
#                     if post['img_link'] and len('{}\n{}'.format(post['title'], post['link'])) < 200:
#                         bot.send_photo(chat_id=chat_id,
#                                        photo=post['img_link'],
#                                        caption='{}\n{}'.format(post['title'], post['link']))
#                     else:
#                         bot.send_message(chat_id=chat_id,
#                                          text='{}\n{}'.format(post['title'], post['link']))
#             bot.mark_as_sent_by_source(source)
