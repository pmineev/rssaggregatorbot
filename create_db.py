from db import Database
from delete_db import DeleteDatabase
from sourceparsers import sources


class CreateDatabase(DeleteDatabase, Database):
    def _create_sources(self):
        self.cur.execute('''CREATE TABLE sources (
                                source VARCHAR(20) PRIMARY KEY,
                                last_parsed_date INT DEFAULT 0)''')

        for source in (sources.keys()):
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
                                source VARCHAR(20) REFERENCES sources,
                                category VARCHAR(20))''')

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

    def _create_users_categories(self):
        self.cur.execute('''CREATE TABLE users_categories (
                                chat_id INTEGER
                                    REFERENCES users
                                    ON DELETE CASCADE,
                                category VARCHAR(20),
                                UNIQUE (chat_id, category))''')

    def _create_favourites(self):
        self.cur.execute('''CREATE TABLE favourites (
                                chat_id INTEGER
                                    REFERENCES users
                                    ON DELETE CASCADE,
                                post_id INTEGER
                                    REFERENCES posts(id),
                                UNIQUE (chat_id, post_id))''')

    def _create_responses(self):
        self.cur.execute('''CREATE TABLE responses (
                                chat_id INTEGER
                                    REFERENCES users
                                    ON DELETE CASCADE,
                                text TEXT,
                                date INTEGER)''')

    def create(self):
        self._create_sources()
        self._create_posts()
        self._create_users()
        self._create_users_sources()
        self._create_users_categories()
        self._create_favourites()
        self._create_responses()


d = CreateDatabase()
d.delete()
d.create()
