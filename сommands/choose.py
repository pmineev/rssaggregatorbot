import logging

from keyboard_markups import choose_sources_keyboard

log = logging.getLogger(__name__)


def choose(bot, update):
    message = update.message or update.callback_query.message
    chat_id = message.chat.id
    log.info('user {} is choosing sources now'.format(chat_id))
    sources = bot.database.get_sources(chat_id)
    message.reply_text('Выберите источники:',
                       reply_markup=choose_sources_keyboard(sources))
    return 0


def button(bot, update):
    query = update.callback_query
    source = query.data.replace('source_', '')
    print(__name__, source)
    chat_id = query.message.chat_id
    user_sources = bot.database.get_sources(chat_id)
    # TODO пользователь может попытаться выбрать источники до команды /start
    if source in user_sources:
        bot.database.delete_source(chat_id, source)
        user_sources.remove(source)
        log.info(f'user {chat_id} unsubscribed from {source}')
    else:
        bot.database.add_source(chat_id, source)
        user_sources.append(source)
        log.info(f'user {chat_id} subscribed to {source}')

    bot.edit_message_text(text='Выберите источники:',
                          chat_id=chat_id,
                          message_id=query.message.message_id,
                          reply_markup=choose_sources_keyboard(user_sources))
    return 0


def cancel(bot, update):
    message = update.callback_query.message
    bot.delete_message(chat_id=message.chat_id,
                       message_id=message.message_id)
    log.info(f'user {message.chat.id} calcelled choosing sources')
    return -1
