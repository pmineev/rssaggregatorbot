from db import Database


class DeleteDatabase(Database):
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

    def delete(self):
        self._delete_users_sources()
        self._delete_users()
        self._delete_posts()
        self._delete_sources()