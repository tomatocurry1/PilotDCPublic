#!/usr/bin/env python3

import flask
from flask.ext.bcrypt import Bcrypt as bcrypt
import sqlite3

import .config

app = Flask(__name__)
app.secret_key = config.secret
passcheck = bcrypt(app)

def query_db(query, *args, one=False):
    cur = g.db.execute(query, args)
    g.db.commit()
    rv = [dict((cur.description[idx][0], value) for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

@app.before_request
def before_request():
    g.db = sqlite3.connect(config.database)

@app.teardown_request
def teardown_request(ex):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run(debug = config.debug)