#!/usr/bin/env python3

import flask
from flask.ext.bcrypt import Bcrypt as bcrypt
import sqlite3

import config

app = flask.Flask(__name__)
app.secret_key = config.secret
passcheck = bcrypt(app)

def query_db(query, *args, one=False):
    cur = flask.g.db.execute(query, args)
    flask.g.db.commit()
    rv = [dict((cur.description[idx][0], value) for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

@app.before_request
def before_request():
    flask.g.db = sqlite3.connect(config.database)

@app.teardown_request
def teardown_request(ex):
    if hasattr(flask.g, 'db'):
        flask.g.db.close()

@app.route('/')
def index():
    return 'hello world'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        if user and password:
            query = query_db('SELECT user_id, password_salt FROM users WHERE username = ?', user, one=True)
            if not query:
                flask.flash('Invalid username', 'error')
            else:
                try:
                    if query and passcheck.check_password_hash(query['password_salt'], password):
                        flask.session['username'] = username
                        flask.session['user_id'] = query['user_id']
                        return flask.redirect(flask.url_for('index'))
                    else:
                        flask.flash('Invalid password', 'error')
                except:
                    flask.flash('Password validation error', 'error')
        else:
            flask.flash('Invalid username or password (empty?)', 'error')
    return flask.render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    email = flask.request.form.get('email')
    longitude = flask.request.form.get('longitude')
    latitude = flask.request.form.get('latitude')
    if not all([username, password, email, longitude, latitude]):
        flask.flash('Missing required fields', 'error')
    elif [ c for c in username if c not in config.username_allowed_characters ]:
        flask.flash('Your username contains characters that aren\'t allowed', 'error')
    else:
        user_check = query_db('SELECT 1 FROM users WHERE username = ?', username)
        if user_check:
            flask.flash('Username taken', 'error')
        else:
            # register the user!!!!!
            query_db('INSERT INTO users (username, password_salt, email, longitude, latitude, join_date, karma) VALUES (?, ?, ?, ?, ?, date(), 0)', [
                username, passcheck.generate_password_hash(password), email, longitude, latitude
            ])
            flask.flash('Sucessfully registered as {}! Please log in'.format(username), 'success')
    return flask.redirect(flask.url_for('login'))


@app.route('/users')
@app.route('/user/<int:user_id>')
def user(user_id = None):
    if user_id is None:
        if 'user_id' in flask.session and flask.session['user_id'].isnumeric():
            return flask.redirect(flask.url_for('user', user_id=int(flask.session['user_id'])))
        else:
            return flask.abort(404)
    else:
        return 'hi user {}'.format(user_id)

if __name__ == '__main__':
    app.run(debug = config.debug)