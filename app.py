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

@app.route('/login/', methods=['GET', 'POST'])
@app.route('/login', methods=['POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        if username and password:
            query = query_db('SELECT user_id, password_salt FROM users WHERE username = ?', username, one=True)
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

@app.route('/register/', methods=['POST'])
@app.route('/register', methods=['POST'])
def register():
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    email = flask.request.form.get('email')
    longitude = flask.request.form.get('longitude')
    latitude = flask.request.form.get('latitude')
    print(flask.request.form, username, password, email, longitude, latitude)
    if not all([username, password, email, longitude is not None, latitude is not None]):
        flask.flash('Missing required fields', 'error')
    elif [ c for c in username if c not in config.username_allowed_chars ]:
        flask.flash('Your username contains characters that aren\'t allowed', 'error')
    else:
        user_check = query_db('SELECT 1 FROM users WHERE username = ?', username)
        if user_check:
            flask.flash('Username taken', 'error')
        else:
            # register the user!!!!!
            query_db('INSERT INTO users (username, password_salt, email, longitude, latitude, join_date, karma) VALUES (?, ?, ?, ?, ?, date(), 0)',
                username, passcheck.generate_password_hash(password), email, longitude, latitude
            )
            flask.flash('Sucessfully registered as {}! Please log in'.format(username), 'success')
            return flask.redirect(flask.url_for('login') + '?directlogin')
    return flask.redirect(flask.url_for('login'))

@app.route('/logout/', methods=['GET'])
def logout():
    flask.session.pop('username', None)
    flask.session.pop('user_id', None)
    return flask.redirect(flask.url_for('index'))

@app.route('/user/')
@app.route('/user/<int:user_id>/')
def user(user_id = None):
    if user_id is None:
        if 'user_id' in flask.session and flask.session['user_id']:
            return flask.redirect(flask.url_for('user', user_id=int(flask.session['user_id'])))
        else:
            return flask.abort(404)
    else:
        favors_posted = query_db('SELECT title, cost, content FROM favors WHERE creator_id = ? ORDER BY creation_date DESC', flask.session['user_id'])
        favors_cmpltd = query_db('SELECT title, cost, content FROM favors WHERE worker_id = ? AND state = 2 ORDER BY deadline DESC', flask.session['user_id'])

        user_info = query_db('SELECT join_date, karma FROM users WHERE user_id = ?', user_id, one=True)
        return str({
            'user_id': flask.session['user_id'],
            'username': flask.session['username'],
            'join': user_info['join_date'],
            'kermer': user_info['karma'],
            'posts': favors_posted,
            'compd': favors_cmpltd
        })

@app.route('/requestfavor/', methods=['GET', 'POST'])
def create_favor():
    if 'user_id' not in flask.session:
        flask.flash('You must be logged in to request a favor', 'error')
        return flask.redirect(flask.url_for('login'))

    if flask.request.method == 'GET':
        return flask.render_template('createfavor.html')
    elif flask.request.method == 'POST':
        title = flask.request.form.get('title')
        content = flask.request.form.get('content')
        location_desc = flask.request.form.get('location_description')
        requirements = flask.request.form.get('requirements')
        deadline = flask.request.form.get('deadline')
        cost = flask.request.form.get('cost')
        payment = flask.request.form.get('payment')
        latitude = flask.request.form.get('latitude')
        longitude = flask.request.form.get('longitude')
        if not all([title, content, location_desc, requirements, deadline, cost, payment, latitude, longitude]):
            flask.flash('Missing required fields')
            return flask.redirect(flask.url_for('create_favor'))
        query_db('INSERT INTO favors(creator_id, title, content, location_description, requirements, deadline, cost, payment, latitude, longitude, state, worker_id, creation_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, date())',
            session['user_id'], title, content, location_desc, requirements, deadline, cost, payment, latitude, longitude
        )
        favor_id = query_db('SELECT last_insert_rowid()', one=True).values()[0]
        return flask.redirect(flask.url_for('favor', favor_id=favor_id))

@app.route('/favor/<int:favor_id>/')
def get_favor(favor_id):
    favor = query_db('SELECT * FROM favors WHERE favor_id = ?', favor_id, one=True)
    return str(favor)

@app.route('/about/')
def about():
    return flask.render_template('about.html')

if __name__ == '__main__':
    app.run(debug = config.debug)