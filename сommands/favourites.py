import logging

from telegram.parsemode import ParseMode

from keyboard_markups import favourites_keyboard

log = logging.getLogger(__name__)


def button(bot, update):
    query = update.callback_query
    answer = query.data
    message = query.message
    chat_id = message.chat_id
    post_text = message.text or message.caption
    post_text = post_text[post_text.find('\n') + 1:post_text.rfind('\n')]
    post_id = bot.database.get_post_id(post_text)
    if answer == 'favourites_add':
        bot.database.add_to_favourites(chat_id, post_id)
        log.info(f'{chat_id} added to favourites {post_id}')
    else:
        bot.database.delete_from_favourites(chat_id, post_id)
        log.info(f'{chat_id} removed from favourites {post_id}')

    if message.text:
        bot.edit_message_text(text=message.text_markdown,
                              chat_id=chat_id,
                              message_id=query.message.message_id,
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=favourites_keyboard(answer == 'favourites_add'))
    else:
        bot.edit_message_caption(caption=message.caption_markdown,
                                 chat_id=chat_id,
                                 message_id=query.message.message_id,
                                 parse_mode=ParseMode.MARKDOWN,
                                 reply_markup=favourites_keyboard(answer == 'favourites_add'))


def favourites(bot, update):
    chat_id = update.message.chat.id
    bot.send_favourite_posts(chat_id)
