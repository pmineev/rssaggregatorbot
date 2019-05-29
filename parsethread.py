import logging
import threading
import time

import config

log = logging.getLogger(__name__)


class ParseThread(threading.Thread):
    def __init__(self, get_feed, database, **kwargs):
        super().__init__(**kwargs)
        self.get_feed = get_feed
        self.database = database
        self.name = kwargs['name']
        self.last_posted = 0
        self.last_parsed = self.database.get_last_parsed_date(self.name)
        self.sleep_time = config.DEFAULT_THREAD_SLEEP_TIME

    def _set_last_parsed_date(self, posts):
        last_date = max([post['date'] for post in posts])
        self.database.set_last_parsed_date(last_date, self.name)

    def get_new_posts(self):
        feed_parsed = self.get_feed()
        if feed_parsed:
            log.info(f'{len(feed_parsed)} posts in {self.name} feed')

            self.last_posted = feed_parsed[0]['date']
            new_posts = [post for post in feed_parsed if
                         self.last_parsed < post['date'] <= self.last_posted]

            log.info(f'{len(new_posts)} new posts in {self.name} feed')
            if new_posts:
                self.database.add_posts(new_posts, self.name)
                self._set_last_parsed_date(new_posts)
                self.last_parsed = int(time.time())
        else:
            log.warning(f'{self.name} feed is empty')

    def run(self):
        while True:
            self.get_new_posts()
            time.sleep(self.sleep_time)
