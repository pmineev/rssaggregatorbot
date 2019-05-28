import logging
import time
from os import environ

import psycopg2
from psycopg2.extras import NamedTupleCursor

import config

log = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(environ['DATABASE_URL'])
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.nt_cur = self.conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

    def get_last_parsed_date(self, source):
        self.cur.execute('''SELECT last_parsed_date
                            FROM sources
                            WHERE source = %s''', (source,))
        return self.cur.fetchone()[0]

    def set_last_parsed_date(self, date, source):
        self.cur.execute('''UPDATE sources
                            SET last_parsed_date = %s
                            WHERE source = %s''', (date, source))

    def add_posts(self, posts, source):
        log.info('Adding {} {} posts to database'.format(len(posts), source))
        for post in posts:
            post.update({'source': source})
            try:
                self.cur.execute('''INSERT INTO posts (title, link, img_link, summary, date, source, category)
                                    VALUES (%(title)s, %(link)s, %(img_link)s, %(summary)s,
                                            %(date)s, %(source)s, %(category)s)''',
                                 post)
            except Exception as e:
                print(e, post)

    def add_user(self, chat_id):
        self.cur.execute('''INSERT INTO users
                            VALUES (%s, %s, %s)
                            ON CONFLICT (chat_id) DO NOTHING''',
                         (chat_id, config.DEFAULT_UPDATE_INTERVAL, int(time.time())))
        self.cur.execute('''INSERT INTO users_categories
                            VALUES (%s, %s)''', (chat_id, None))

    def delete_user(self, chat_id):
        self.cur.execute('''DELETE FROM users
                            WHERE chat_id = %s''', (chat_id,))
        self.cur.execute('''DELETE FROM users_sources
                            WHERE chat_id = %s''', (chat_id,))
        self.cur.execute('''DELETE FROM users_categories
                            WHERE chat_id = %s''', (chat_id,))
        self.cur.execute('''DELETE FROM favourites
                            WHERE chat_id = %s''', (chat_id,))

    def get_users(self):
        self.nt_cur.execute('''SELECT *
                            FROM users''')
        return self.nt_cur.fetchall()

    def get_user(self, chat_id):
        self.nt_cur.execute('''SELECT *
                            FROM users
                            WHERE chat_id = %s''', (chat_id,))
        return self.nt_cur.fetchone()

    def add_source(self, chat_id, source):
        self.cur.execute('''INSERT INTO users_sources
                            VALUES (%s, %s)''', (chat_id, source))

    def delete_source(self, chat_id, source):
        self.cur.execute('''DELETE FROM users_sources
                            WHERE chat_id = %s
                                AND source = %s''', (chat_id, source))

    def get_sources(self, chat_id):
        self.cur.execute('''SELECT source FROM users_sources
                            WHERE chat_id = %s''', (chat_id,))
        sources = self.cur.fetchall()
        return [source[0] for source in sources]

    def get_categories(self, chat_id=None):
        if chat_id:
            self.cur.execute('''SELECT DISTINCT category
                                FROM users_categories
                                WHERE chat_id = %s
                                    AND category NOTNULL''', (chat_id,))
        else:
            self.cur.execute('''SELECT DISTINCT category
                                FROM posts
                                WHERE category NOTNULL ''')

        categories = self.cur.fetchall()
        return [category[0] for category in categories]

    def add_category(self, chat_id, category):
        self.cur.execute('''INSERT INTO users_categories
                            VALUES (%s, %s)''', (chat_id, category))

    def delete_category(self, chat_id, category):
        self.cur.execute('''DELETE FROM users_categories
                            WHERE chat_id = %s
                                AND category = %s''', (chat_id, category))

    def set_update_interval(self, chat_id, interval):
        self.cur.execute('''UPDATE users
                            SET update_interval = %s
                            WHERE chat_id = %s''', (interval, chat_id))

    def get_update_interval(self, chat_id):
        self.cur.execute('''SELECT update_interval
                            FROM users
                            WHERE chat_id = %s''', (chat_id,))
        return self.cur.fetchone()[0]

    def get_last_posts(self, chat_id, count):
        self.nt_cur.execute('''SELECT id, title, link, img_link, summary, date, p.category
                            FROM posts AS p
                            JOIN users_sources as us
                                ON p.source = us.source
                            JOIN users AS u
                                ON u.chat_id = us.chat_id
                            JOIN users_categories AS uc
                                ON u.chat_id = uc.chat_id
                                    AND p.category = uc.category
                            WHERE u.chat_id = %s
                            ORDER BY date DESC
                            FETCH FIRST %s ROWS ONLY''', (chat_id, count))
        return self.nt_cur.fetchall()

    def get_new_posts(self, chat_id):
        self.nt_cur.execute('''SELECT id, title, link, img_link, summary, date, p.category
                               FROM posts AS p
                               JOIN users AS u
                                   ON p.date > u.last_updated_date
                               JOIN users_sources as us
                                   ON u.chat_id = us.chat_id
                                       AND p.source = us.source
                               JOIN users_categories AS uc
                                   ON u.chat_id = uc.chat_id
                                       AND p.category = uc.category
                               WHERE u.chat_id = %s
                               ORDER BY date''', (chat_id,))
        return self.nt_cur.fetchall()

    def set_last_updated_date(self, chat_id, date):
        self.cur.execute('''UPDATE users
                            SET last_updated_date = %s
                            WHERE chat_id = %s''', (date, chat_id))
        self.conn.commit()

    def get_favourite_posts(self, chat_id):
        self.nt_cur.execute('''SELECT id, title, link, img_link, summary, date
                               FROM posts AS p
                               JOIN favourites AS f
                                   ON p.id = f.post_id''', (chat_id,))
        return self.nt_cur.fetchall()

    def get_post_id(self, post_text):
        self.cur.execute('''SELECT id
                            FROM posts AS p
                            WHERE p.title LIKE %s || '%%' ''', (post_text,))
        return self.cur.fetchone()[0]

    def add_to_favourites(self, chat_id, post_id):
        self.cur.execute('''INSERT INTO favourites
                            VALUES (%s, %s)''', (chat_id, post_id))

    def delete_from_favourites(self, chat_id, post_id):
        self.cur.execute('''DELETE FROM favourites
                            WHERE chat_id = %s
                                AND post_id = %s''', (chat_id, post_id))

    def is_in_favourites(self, chat_id, post_id):
        self.cur.execute('''SELECT COUNT(*) > 0
                            FROM favourites
                            WHERE chat_id = %s
                                AND post_id = %s''', (chat_id, post_id))
        return self.cur.fetchone()[0]
