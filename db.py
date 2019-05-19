import logging
import time
from os import environ

import psycopg2
from psycopg2.extras import NamedTupleCursor

import config
import sourceparsers

log = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(environ['DATABASE_URL'])
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.nt_cur = self.conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)

    def _create_sources(self):
        self.cur.execute('''CREATE TABLE sources (
                                source VARCHAR(20) PRIMARY KEY,
                                last_parsed_date INT DEFAULT 0)''')

        for source in (sourceparsers.sources.keys()):
            self.cur.execute('''INSERT INTO sources (source, last_parsed_date) VALUES
                                (%s, 0)''', (source,))
        self.conn.commit()

    def _create_posts(self):
        self.cur.execute('''CREATE TABLE posts (
                                id SERIAL PRIMARY KEY,
                                title TEXT,
                                link TEXT,
                                img_link TEXT,
                                summary TEXT,
                                date INTEGER,
                                source VARCHAR(20) REFERENCES sources)''')

    def _create_users(self):
        self.cur.execute('''CREATE TABLE users (
                                chat_id INTEGER PRIMARY KEY,
                                update_interval INTEGER,
                                last_updated_date INTEGER)''')

    def _create_users_sources(self):
        self.cur.execute('''CREATE TABLE users_sources (
                                chat_id INTEGER
                                    REFERENCES users
                                    ON DELETE CASCADE,
                                source VARCHAR(20) REFERENCES sources,
                                UNIQUE (chat_id, source))''')

    def _delete_posts(self):
        self.cur.execute("DROP TABLE IF EXISTS posts")
        self.conn.commit()

    def _delete_sources(self):
        self.cur.execute("DROP TABLE IF EXISTS sources")
        self.conn.commit()

    def _delete_users(self):
        self.cur.execute("DROP TABLE IF EXISTS users")
        self.conn.commit()

    def _delete_users_sources(self):
        self.cur.execute("DROP TABLE IF EXISTS users_sources")
        self.conn.commit()

    def create(self):
        self._create_sources()
        self._create_posts()
        self._create_users()
        self._create_users_sources()

    def delete(self):
        self._delete_users_sources()
        self._delete_users()
        self._delete_posts()
        self._delete_sources()

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
                self.cur.execute('''INSERT INTO posts (title, link, img_link, summary, date, source)
                                    VALUES
                                    (%(title)s, %(link)s, %(img_link)s, %(summary)s, %(date)s, %(source)s)''',
                                 post)
            except Exception as e:
                print(e, post)

    def add_user(self, chat_id):
        self.cur.execute('''INSERT INTO users
                            VALUES (%s, %s, %s)
                            ON CONFLICT (chat_id) DO NOTHING''',
                         (chat_id, config.DEFAULT_UPDATE_INTERVAL, int(time.time())))

    def delete_user(self, chat_id):
        self.cur.execute('''DELETE FROM users
                            WHERE chat_id = %s''', (chat_id,))
        self.cur.execute('''DELETE FROM users_sources
                            WHERE chat_id = %s''', (chat_id,))

    def get_users(self):
        self.nt_cur.execute('''SELECT *
                            FROM users''')
        return self.nt_cur.fetchall()

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
        self.nt_cur.execute('''SELECT title, link, img_link, summary, date
                            FROM posts AS p
                            JOIN users_sources as us
                                ON p.source = us.source
                            JOIN users AS u
                                ON u.chat_id = us.chat_id
                            WHERE u.chat_id = %s
                            ORDER BY date DESC
                            FETCH FIRST %s ROWS ONLY''', (chat_id, count))
        return self.nt_cur.fetchall()

    def get_new_posts(self, chat_id):
        self.nt_cur.execute('''SELECT title, link, img_link, summary, date
                               FROM posts AS p
                               JOIN users AS u
                                   ON p.date > u.last_updated_date
                               JOIN users_sources as us
                                   ON u.chat_id = us.chat_id
                                       AND p.source = us.source
                               WHERE u.chat_id = %s
                               ORDER BY date''', (chat_id,))
        return self.nt_cur.fetchall()

    def set_last_updated_date(self, chat_id, date):
        self.cur.execute('''UPDATE users
                            SET last_updated_date = %s
                            WHERE chat_id = %s''', (date, chat_id))
        self.conn.commit()
