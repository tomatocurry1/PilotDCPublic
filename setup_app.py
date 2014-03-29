import contextlib
import os
import subprocess
import sqlite3

import config

def init_db():
    if os.path.exists(config.database):
        print('Database already exists, skipping rebuild.......')
    else:
        with contextlib.closing(sqlite3.connect(config.database)) as db:
            with open('schema.sql') as schema:
                db.cursor().executescript(schema.read())
            db.commit()

def convert_flask_bcrypt():
    subprocess.call(['2to3', '-w', 'venv/lib/python3.3/site-packages/flaskext/bcrypt.py'])

if __name__ == '__main__':
    init_db()
    convert_flask_bcrypt()