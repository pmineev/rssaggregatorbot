import logging

from keyboard_markups import choose_categories_keyboard

log = logging.getLogger(__name__)


def category(bot, update):
    message = update.message
    chat_id = message.chat.id
    log.info('user {} is choosing categories now'.format(chat_id))
    categories = bot.database.get_categories()
    user_categories = bot.database.get_categories(chat_id)
    message.reply_text('Выберите категории:',
                       reply_markup=choose_categories_keyboard(categories, user_categories))
    return 0


def button(bot, update):
    query = update.callback_query
    category = query.data.replace('categories_', '')
    chat_id = query.message.chat_id
    categories = bot.database.get_categories()
    user_categories = bot.database.get_categories(chat_id)
    # TODO пользователь может попытаться выбрать источники до команды /start
    if category in user_categories:
        bot.database.delete_category(chat_id, category)
        user_categories.remove(category)
        log.info(f'user {chat_id} deleted category {category}')
    else:
        bot.database.add_category(chat_id, category)
        user_categories.append(category)
        log.info(f'user {chat_id} added category {category}')

    bot.edit_message_text(text=query.message.text,
                          chat_id=chat_id,
                          message_id=query.message.message_id,
                          reply_markup=choose_categories_keyboard(categories, user_categories))
    return 0


def cancel(bot, update):
    message = update.callback_query.message
    bot.delete_message(chat_id=message.chat_id,
                       message_id=message.message_id)
    log.info(f'user {message.chat.id} calcelled choosing categories')
    return -1
