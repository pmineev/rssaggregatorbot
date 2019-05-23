import logging
import time
from os import environ

import telegram
from telegram.ext import MessageQueue
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram.ext.messagequeue import queuedmessage
from telegram.utils.request import Request

import db
import jobs.restore_senders as restore
import rss_utils
import sourceparsers
import сommands.choose as sources
import сommands.favourites as favourites
import сommands.interval as interval
import сommands.last as last
import сommands.pause as pause
import сommands.resume as resume
import сommands.start as start
import сommands.stop as stop
from keyboard_markups import favourites_keyboard

log = logging.getLogger(__name__)


class RssBot(telegram.bot.Bot):
    def __init__(self):
        request = Request(con_pool_size=8,
                          proxy_url=None if 'HEROKU' in environ else environ['PROXY_URL'])
        super().__init__(token=environ['TOKEN'], request=request)
        log.info('Bot started')

        self._is_messages_queued_default = True
        self._msg_queue = MessageQueue(all_burst_limit=2, all_time_limit_ms=2000)

        self.updater = Updater(bot=self)
        self.dispatcher = self.updater.dispatcher

        self.database = db.Database()

        self._add_handlers()

        self._run_threads()

        self.updater.start_polling()

    def _add_handlers(self):
        restore.restore_senders(self, self.updater.job_queue)

        self.dispatcher.add_handler(CommandHandler('stop', stop.stop, pass_job_queue=True))
        self.dispatcher.add_handler(CommandHandler('pause', pause.pause, pass_job_queue=True))
        self.dispatcher.add_handler(CommandHandler('resume', resume.resume, pass_job_queue=True))
        self.dispatcher.add_handler(CommandHandler('favourites', favourites.favourites))

        self.dispatcher.add_handler(CallbackQueryHandler(restore.button, pattern='^restore', pass_job_queue=True))
        self.dispatcher.add_handler(CallbackQueryHandler(resume.button, pattern='^resume'))
        self.dispatcher.add_handler(CallbackQueryHandler(favourites.button, pattern='^favourites'))

        self._start()
        self._change_interval()
        self._choose_sources()
        self._last()

    def _run_threads(self):
        threads = []
        for name, parser in sourceparsers.sources.items():
            threads.append(rss_utils.ParseThread(parser, self.database, name=name))
            log.info('created {} thread'.format(name))
        for t in threads:
            t.start()

    def _start(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler('start', start.start, pass_job_queue=True)],
            states={
                0: [CallbackQueryHandler(start.button, pattern='^start')],
                1: [CallbackQueryHandler(sources.button, pattern='^source')]
                },
            fallbacks=[])
        self.dispatcher.add_handler(handler)

    def _change_interval(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler('interval', interval.change)],
            states={
                0: [MessageHandler(Filters.text, interval.enter, pass_job_queue=True)]
                },
            fallbacks=[CommandHandler('cancel', interval.cancel)])
        self.dispatcher.add_handler(handler)

    def _choose_sources(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler('choose', sources.choose)],
            states={
                0: [CallbackQueryHandler(sources.button, pattern='^source')]
                },
            fallbacks=[CallbackQueryHandler(sources.cancel, pattern='_source_cancel')])
        self.dispatcher.add_handler(handler)

    def _last(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler('last', last.last)],
            states={
                0: [MessageHandler(Filters.all, last.enter)]
                },
            fallbacks=[])
        self.dispatcher.add_handler(handler)

    @queuedmessage
    def send_message(self, *args, **kwargs):
        super().send_message(*args, **kwargs)

    @queuedmessage
    def send_photo(self, *args, **kwargs):
        super().send_photo(*args, **kwargs)

    def send_posts(self, chat_id, posts):
        log.info(f'Sending {len(posts)} posts to {chat_id}')
        favourites_map = [self.database.is_in_favourites(chat_id, post.id) for post in posts]
        for post, is_fav in zip(posts, favourites_map):
            text = '{}\n{}'.format(post.title, post.link)
            if post.img_link and len(text) < 200:
                self.send_photo(chat_id=chat_id,
                                photo=post.img_link,
                                caption=f'{post.title}\n{post.link}',
                                reply_markup=favourites_keyboard(is_fav))
            else:
                self.send_message(chat_id=chat_id,
                                  text=f'{post.summary}\n{post.link}')

    def send_new_posts(self, _, job):
        chat_id = job.context
        log.info(f'Sending new posts to {chat_id}')
        posts = self.database.get_new_posts(chat_id)
        print(len(posts))
        if posts:
            self.send_posts(chat_id, posts)
            self.database.set_last_updated_date(chat_id, int(time.time()))

    def send_last_posts(self, chat_id, count):
        log.info(f'Sending last posts to {chat_id}')
        posts = self.database.get_last_posts(chat_id, count)
        if posts:
            self.send_posts(chat_id, posts)

    def send_favourite_posts(self, chat_id):
        log.info(f'Sending favourite posts to {chat_id}')
        posts = self.database.get_favourite_posts(chat_id)
        if posts:
            self.send_posts(chat_id, posts)
        else:
            self.send_message(text='В избранном пусто')

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
