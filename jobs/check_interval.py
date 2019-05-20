import logging
import time

from keyboard_markups import yesno_keyboard

log = logging.getLogger(__name__)


def check_interval(bot, user, data):
    current_time = time.time()
    next_update_date = user.last_updated_date + user.update_interval
    if next_update_date > current_time:
        return True
    else:
        bot.send_message(chat_id=user.chat_id,
                         text='Бот не работал продолжительное время. Хотите получить неотправленные сообщения?',
                         reply_markup=yesno_keyboard(data))
        return False
