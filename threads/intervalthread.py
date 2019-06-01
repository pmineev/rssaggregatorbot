import logging
import threading
import time

import config

log = logging.getLogger(__name__)


class IntervalThread(threading.Thread):
    def __init__(self, threads, database, **kwargs):
        super().__init__(**kwargs)
        self._threads = threads
        self._database = database

    def recalculate_interval(self, thread):
        count = self._database.get_last_posts_count(thread.name,
                                                    time.time() - config.INTERVAL_THREAD_SLEEP_TIME)
        new_sleep_time = int(config.MIN_NEW_POSTS_COUNT / count * config.INTERVAL_THREAD_SLEEP_TIME)
        thread.sleep_time = new_sleep_time
        log.info(f'{thread.name} sleep time recalculated to {new_sleep_time}')

    def run(self):
        while True:
            time.sleep(config.INTERVAL_THREAD_SLEEP_TIME)
            for t in self._threads:
                self.recalculate_interval(t)
