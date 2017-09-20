#!/usr/bin/env python3

import os
import functools
import sqlite3
import subprocess
import requests
from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, url_for, flash, render_template, abort, Response, g, make_response, jsonify, session
from config import *


def setup_user(username, keys):
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'setup_user.bash')
    p = subprocess.Popen(['sudo', script_path, username],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         universal_newlines=True)
    out, err = p.communicate(keys)
    if p.returncode != 0:
        return 'STDOUT: \n{}\nSTDERR: {}\n'.format(out, err)
    return None


app = Flask(__name__, static_url_path=WEBROOT + '/static')
app.secret_key = FLASK_SECRET_KEY


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        conn = sqlite3.connect(DB_NAME)
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS keys (
            jaccount TEXT UNIQUE,
            stuid TEXT UNIQUE,
            keys TEXT
        );
        CREATE TABLE IF NOT EXISTS members (
            stuid TEXT UNIQUE,
            name TEXT
        );
        ''')
        conn.row_factory = sqlite3.Row
        db = g._database = conn
    return db


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('请登入', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function


def logout_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' in session:
            flash('请登出', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function


@app.route(WEBROOT)
def homepage():
    user = session.get('user', None)

    cur = get_db().cursor()
    sql = '''SELECT keys.jaccount AS jaccount, members.stuid AS stuid, members.name AS name
    FROM keys, members
    WHERE keys.stuid = members.stuid
    ORDER BY members.stuid DESC'''
    cur.execute(sql)
    known_users = cur.fetchall()
    return render_template('homepage.html', user=user, known_users=known_users)


@app.route(WEBROOT + '/help')
def help():
    return render_template('help.html')


@app.route(WEBROOT + '/ssh-key')
@login_required
def get_ssh_key():
    jaccount = session['user']['jaccount']
    stuid = session['user']['stuid']

    cur = get_db().cursor()
    cur.execute('SELECT * FROM members WHERE stuid=?', (stuid, ))
    row = cur.fetchone()
    if not row:
        flash('您不是ACM班的成员', 'error')
        return redirect(url_for('homepage'))

    cur.execute('SELECT keys FROM keys WHERE jaccount=?', (jaccount,))
    row = cur.fetchone()
    keys = row['keys'] if row else ''
    return render_template('ssh_key.html', user=session['user'], keys=keys)


@app.route(WEBROOT + '/save-ssh-key', methods=['POST'])
@login_required
def save_ssh_key():
    jaccount = session['user']['jaccount']
    stuid = session['user']['stuid']
    keys = request.form.get('keys', '')

    cur = get_db().cursor()
    cur.execute('SELECT * FROM members WHERE stuid=?', (stuid, ))
    row = cur.fetchone()
    if not row:
        flash('您不是ACM班的成员', 'error')
        return redirect(url_for('homepage'))

    cur = get_db().cursor()
    cur.execute('DELETE FROM keys WHERE jaccount=?', (jaccount,))
    cur.execute('INSERT INTO keys (jaccount, stuid, keys) VALUES (?, ?, ?)', (jaccount, stuid, keys))
    get_db().commit()

    err = setup_user(jaccount, keys)
    if err:
        flash('<pre>' + err + '</pre>', 'error')
    else:
        flash('保存成功', 'success')

    return redirect(url_for('get_ssh_key'))


@app.route(WEBROOT + '/login')
@logout_required
def login():
    return render_template('login.html')


@app.route(WEBROOT + '/login_oauth')
@logout_required
def login_oauth():
    redirect_uri = DOMAIN + url_for('login_oauth_callback')
    sjtu = OAuth2Session(CLIENT_ID, redirect_uri=redirect_uri, scope='basic essential profile')
    authorization_url, state = sjtu.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route(WEBROOT + '/login_oauth_callback')
@logout_required
def login_oauth_callback():
    code = request.args.get('code', None)
    state = session.get('oauth_state', None)
    if not code:
        flash('login_oauth_callback: no code', 'error')
        return redirect(url_for('homepage'))
    if not state:
        flash('login_oauth_callback: no oauth_state', 'error')
        return redirect(url_for('homepage'))

    redirect_uri = DOMAIN + url_for('login_oauth_callback')
    sjtu = OAuth2Session(CLIENT_ID, state=state, redirect_uri=redirect_uri)
    token = sjtu.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, code=code)
    session['oauth_token'] = token

    res = sjtu.get(PROFILE_URL).json()
    res = res['entities'][0]
    user = {'jaccount': res['account'],
            'name': res['name'],
            'stuid': res['code'],}
    session['user'] = user
    return redirect(url_for('get_ssh_key'))


@app.route(WEBROOT + '/logout_oauth')
@login_required
def logout_oauth():
    redirect_uri = DOMAIN + url_for('logout')
    url = '{}?client_id={}&redirect_uri={}'.format(LOGOUT_URL, CLIENT_ID, redirect_uri)
    return redirect(url)


@app.route(WEBROOT + '/logout')
@login_required
def logout():
    session.clear()
    flash('已登出', 'success')
    return redirect(url_for('homepage'))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5869, debug=True)
