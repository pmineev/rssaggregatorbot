import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from sourceparsers import sources

log = logging.getLogger(__name__)


def choose_sources_keyboard(user_sources):
    icons = ['✔' if source in user_sources else '❌' for source in sources]
    keyboard = [[InlineKeyboardButton(f'{icon} {source}',
                                      callback_data=f'source_{source}')]
                for icon, source in zip(icons, sources)]
    keyboard.append([InlineKeyboardButton('Готово', callback_data='_source_cancel')])
    return InlineKeyboardMarkup(keyboard)


def yesno_keyboard(data):
    keyboard = [[InlineKeyboardButton(f'{text}', callback_data=f'{data}_{text_en}')]
                for text, text_en in (('Да', 'yes'), ('Нет', 'no'))]
    return InlineKeyboardMarkup(keyboard)