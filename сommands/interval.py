import logging

from telegram import ForceReply

log = logging.getLogger(__name__)


def change(bot, update):
    chat_id = update.message.chat.id
    log.info(f'user {chat_id} changing interval')
    update.message.reply_text('Введите новый интервал обновления (в секундах)'
                              '\nТекущий: {}'.format(bot.database.get_update_interval(chat_id)),
                              reply_markup=ForceReply())
    return 0


def enter(bot, update, job_queue):
    # TODO интервал не меняется после ввода
    chat_id = update.message.chat.id
    user_input_interval = update.message.text
    if user_input_interval.isdigit():
        interval = int(user_input_interval)
        bot.database.set_update_interval(chat_id, interval)
        print(list((j.name, j.interval) for j in job_queue.jobs()))
        job, = job_queue.get_jobs_by_name('{}_sender'.format(chat_id))
        job.interval = interval
        update.message.reply_text(f'Новый интервал: {interval}')
        log.info(f'user {chat_id} changed interval to {interval}')
        return -1
    else:
        update.message.reply_text('Интервал должен быть натуральным числом')


def cancel(bot, update):
    update.message.reply_text('Ввод интервала отменен')
    log.info(f'user {update.message.chat_id} calcelled changing interval')
    return -1
