import logging
from os import environ

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram.utils.request import Request

import jobs.restore_senders as restore
import rssbot
import сommands.choose_sources as sources
import сommands.interval as interval
import сommands.start as start
import сommands.stop as stop
import сommands.last as last

logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='{asctime}|{levelname:<8}|{name:<10}|{message}',
                    datefmt='%H:%M:%S')

log = logging.getLogger(__name__)


def _start(dispatcher):
    handler = ConversationHandler(
        entry_points=[CommandHandler('start', start.start, pass_job_queue=True)],
        states={
            0: [CallbackQueryHandler(start.button, pattern='^start')],
            1: [CallbackQueryHandler(sources.button, pattern='^source')]
            },
        fallbacks=[])
    dispatcher.add_handler(handler)


def _change_interval(dispatcher):
    handler = ConversationHandler(
        entry_points=[CommandHandler('interval', interval.change)],
        states={
            0: [MessageHandler(Filters.text, interval.enter, pass_job_queue=True)]
            },
        fallbacks=[CommandHandler('cancel', interval.cancel)])
    dispatcher.add_handler(handler)


def _choose_sources(dispatcher):
    handler = ConversationHandler(
        entry_points=[CommandHandler('choose', sources.choose)],
        states={
            0: [CallbackQueryHandler(sources.button, pattern='^source')]
            },
        fallbacks=[CallbackQueryHandler(sources.cancel, pattern='_source_cancel')])
    dispatcher.add_handler(handler)


def _last(dispatcher):
    handler = ConversationHandler(
        entry_points=[CommandHandler('last', last.last)],
        states={
            0: [MessageHandler(Filters.all, last.enter)]
            },
        fallbacks=[])
    dispatcher.add_handler(handler)


def main():
    request = Request(con_pool_size=8, proxy_url=None if 'HEROKU' in environ else environ['PROXY_URL'])
    bot = rssbot.RssBot(token=environ['TOKEN'], request=request)
    updater = Updater(bot=bot)

    restore.restore_senders(bot, updater.job_queue)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('stop', stop.stop, pass_job_queue=True))
    dispatcher.add_handler(CallbackQueryHandler(restore.button, pattern='^restore', pass_job_queue=True))

    _start(dispatcher)
    _change_interval(dispatcher)
    _choose_sources(dispatcher)
    _last(dispatcher)

    updater.start_polling()


if __name__ == '__main__':
    main()
