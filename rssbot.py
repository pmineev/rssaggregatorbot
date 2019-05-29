import logging
from os import environ

import telegram
from telegram.ext import MessageQueue
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram.ext.messagequeue import queuedmessage
from telegram.parsemode import ParseMode
from telegram.utils.request import Request

import config
import db
import jobs.restore_senders as restore
import сommands.categories as category
import сommands.choose as sources
import сommands.favourites as favourites
import сommands.interval as interval
import сommands.last as last
import сommands.pause as pause
import сommands.response as response
import сommands.resume as resume
import сommands.start as start
import сommands.stop as stop
from intervalthread import IntervalThread
from keyboard_markups import favourites_keyboard
from parsethread import ParseThread
from sourceparsers import sources as sources_dict

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
        self._categories()
        self._response()

    def _run_threads(self):
        self.parse_threads = [ParseThread(parser, self.database, name=name) for name, parser in sources_dict.items()]
        for t in self.parse_threads:
            log.info(f'created {t.name} thread')
            t.start()

        self._interval_thread = IntervalThread(self.parse_threads, self.database, name='_interval')
        log.info(f'created {t.name} thread')
        self._interval_thread.start()

    def _start(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler('start', start.start, pass_job_queue=True)],
            states={
                0: [CallbackQueryHandler(start.button, pattern='^start')],
                1: [CallbackQueryHandler(sources.button, pattern='^source')]
                },
            fallbacks=[CallbackQueryHandler(sources.cancel, pattern='_source_cancel')])
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
                1: [CallbackQueryHandler(sources.button, pattern='^source')]
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

    def _categories(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler('categories', category.category)],
            states={
                0: [CallbackQueryHandler(category.button, pattern='^categories')]
                },
            fallbacks=[CallbackQueryHandler(category.cancel, pattern='_categories_cancel')])
        self.dispatcher.add_handler(handler)

    def _response(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler('response', response.response)],
            states={
                0: [MessageHandler(Filters.text, response.enter)]
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
            text = f'*{post.category}*\n[{post.title}]({post.link})\n{post.summary}'
            if post.img_link:
                if len(text) > config.MAX_CAPTION_LENGTH:
                    text = text[:text.rfind('\n')]
                if len(text) > config.MAX_CAPTION_LENGTH:
                    text = f'*{post.category}*\n' \
                        f'[{post.title[:config.MAX_CAPTION_LENGTH - len(post.category) - len(post.link) - 15]}...]' \
                        f'({post.link})'
                self.send_photo(chat_id=chat_id,
                                photo=post.img_link,
                                caption=text,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=favourites_keyboard(is_fav))
            else:
                self.send_message(chat_id=chat_id,
                                  text=text,
                                  disable_web_page_preview=True,
                                  parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=favourites_keyboard(is_fav))

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
            self.send_message(chat_id=chat_id,
                              text='В избранном пусто')
