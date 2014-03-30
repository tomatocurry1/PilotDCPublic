#!/usr/bin/env python3

import datetime
import flask
from flask.ext.bcrypt import Bcrypt as bcrypt
import math
import pprint
import sqlite3
import time

import config

app = flask.Flask(__name__)
app.secret_key = config.secret
passcheck = bcrypt(app)

def distance_on_unit_sphere(lat1, long1, lat2, long2):
    # http://www.johndcook.com/python_longitude_latitude.html
    degrees_to_radians = math.pi/180.0
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
    cos = math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) + math.cos(phi1) * math.cos(phi2)
    arc = math.acos(cos)

    # Remember to multiply arc by the radius of the earth
    # in your favorite set of units to get length.
    return arc * 3963.1676 # in miles

def timestamp_format(timestamp, fmt='%I:%m %p, %m/%d/%Y'):
    print(timestamp)
    return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)

app.jinja_env.filters['timestamp_format'] = timestamp_format

def query_db(query, *args, one=False):
    cur = flask.g.db.execute(query, args)
    flask.g.db.commit()
    rv = [dict((cur.description[idx][0], value) for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

@app.before_request
def before_request():
    flask.g.db = sqlite3.connect(config.database)
    flask.g.db.create_function('coordinate_distance', 4, distance_on_unit_sphere)
    prune_old_favors()

def prune_old_favors():
    # expire old favors
    print(query_db('SELECT * FROM favors'))
    query_db('UPDATE favors SET state = 3 WHERE state <= 1 AND ? > deadline', int(time.time()))

@app.teardown_request
def teardown_request(ex):
    if hasattr(flask.g, 'db'):
        flask.g.db.close()

@app.route('/')
def index():
    return flask.render_template('index.html')

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
            query_db('INSERT INTO users (username, password_salt, email, longitude, latitude, join_date, karma) VALUES (?, ?, ?, ?, ?, ?, 0)',
                username, passcheck.generate_password_hash(password), email, longitude, latitude, int(time.time())
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
        user_info = query_db('SELECT username, longitude, latitude, join_date, karma FROM users WHERE user_id = ?', user_id, one=True)
        if not user_info:
            return flask.abort(404)

        favors_ongoing = query_db('SELECT title, cost, payment, username, content, favor_id, user_id, state FROM favors JOIN users ON favors.creator_id = users.user_id WHERE state = 1 AND worker_id = ? ORDER BY deadline DESC', user_id)
        favors_posted = query_db('SELECT title, cost, payment, username, content, favor_id, user_id, state FROM favors JOIN users ON favors.creator_id = users.user_id WHERE creator_id = ? ORDER BY creation_date DESC', user_id)
        favors_cmpltd = query_db('SELECT title, cost, payment, username, content, favor_id, user_id, state FROM favors JOIN users ON favors.creator_id = users.user_id WHERE worker_id = ? AND state = 2 ORDER BY deadline DESC', user_id)

        return flask.render_template('usertemplate.html', ongoing_favors=favors_ongoing, posted_favors=favors_posted, completed_favors=favors_cmpltd, **user_info)

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
        location_desc = flask.request.form.get('location_desc')
        requirements = flask.request.form.get('requirements')
        deadline_date = flask.request.form.get('deadline-date')
        deadline_time = flask.request.form.get('deadline-time')
        deadline = -1
        try:
            print('TIMMMMMMMEEEE', deadline_date + ' ' + deadline_time)
            deadline = int(time.mktime(time.strptime(deadline_date + ' ' + deadline_time, '%Y-%m-%d %H:%M')))
        except:
            pass
        if deadline < 0:
            flask.flash('Invalid date/time', 'error')
            return flask.redirect(flask.url_for('create_favor'))
        print(deadline_date, deadline_time)
        cost = flask.request.form.get('cost')
        payment = flask.request.form.get('payment')
        latitude = flask.request.form.get('latitude')
        longitude = flask.request.form.get('longitude')
        print(title, content, location_desc, requirements, deadline_date, deadline_time, cost is not None, payment is not None, latitude, longitude)
        if not all([title, content, location_desc, requirements, deadline_date, deadline_time, cost is not None, payment is not None, latitude, longitude]):
            flask.flash('Missing required fields', 'error')
            return flask.redirect(flask.url_for('create_favor'))
        query_db('INSERT INTO favors(creator_id, title, content, location_description, requirements, deadline, cost, payment, latitude, longitude, state, worker_id, creation_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)',
            flask.session['user_id'],
            title,
            content,
            location_desc,
            requirements,
            deadline,
            cost,
            payment,
            latitude,
            longitude,
            int(time.time())
        )
        favor_id = query_db('SELECT last_insert_rowid()', one=True)['last_insert_rowid()']
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))

@app.route('/find/')
def find_tasks():
    q = query_db('SELECT * FROM favors JOIN users ON favors.creator_id = users.user_id WHERE state = 0 AND creator_id != ? ORDER BY coordinate_distance(users.latitude, users.longitude, favors.latitude, favors.longitude)', flask.session['user_id'])
    #return pprint.pformat(q)
    return flask.render_template('findfavors.html', blocks=q)

@app.route('/favor/<int:favor_id>/')
def get_favor(favor_id):
    favor = query_db('SELECT * FROM favors WHERE favor_id = ?', favor_id, one=True)
    if not favor:
        return flask.abort(404)
    return flask.render_template('favor.html', **favor)

@app.route('/workon/<int:favor_id>', methods=['POST'])
def claim_task(favor_id):
    if 'user_id' not in flask.session:
        flask.flash('You must be logged in to work on a favor', 'error')
        return flask.redirect(flask.url_for('login'))
    favor = query_db('SELECT * FROM favors WHERE favor_id = ?', favor_id, one=True)
    if favor['creator_id'] == flask.session['user_id']:
        flask.flash('You can\'t work on your own favor!', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    elif favor['state'] == 1:
        flask.flash('That favor is already being worked on', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    elif favor['state'] == 2:
        flask.flash('That favor is already completed', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    elif favor['state'] == 3:
        flask.flash('This favor has expired', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    query_db('UPDATE favors SET state = 1, worker_id = ? WHERE favor_id = ?', flask.session['user_id'], favor_id)
    return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))

@app.route('/markcompleted/<int:favor_id>', methods=['POST'])
def mark_completed(favor_id):
    if 'user_id' not in flask.session:
        flask.flash('You must be logged in to mark a favor completed', 'error')
        return flask.redirect(flask.url_for('login'))
    favor = query_db('SELECT * FROM favors WHERE favor_id = ?', favor_id, one=True)
    if favor['creator_id'] != flask.session['user_id']:
        flask.flash('You can\'t mark someone else\'s favor completed!', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    elif favor['state'] == 0:
        flask.flash('This favor can\'t be marked as completed because it hasn\'t been started', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    elif favor['state'] == 2:
        flask.flash('This favor has already been marked completed', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    elif favor['state'] == 3:
        flask.flash('This favor has expired', 'error')
        return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))
    query_db('UPDATE favors SET state = 2 WHERE favor_id = ?', favor_id)
    return flask.redirect(flask.url_for('get_favor', favor_id=favor_id))

@app.route('/about/')
def about():
    return flask.render_template('about.html')

if __name__ == '__main__':
    app.run(debug = config.debug)