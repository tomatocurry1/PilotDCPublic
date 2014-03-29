import sqlite3
import contextlib

import config

def init_db():
    with contextlib.closing(sqlite3.connect(config.database)) as db:
        with open('schema.sql') as schema:
            db.cursor().executescript(schema.read())
        db.commit()

if __name__ == '__main__':
    init_db()