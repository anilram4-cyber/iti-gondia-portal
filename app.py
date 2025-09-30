import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
import json
from io import BytesIO
import xlsxwriter

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DB_PATH = 'trainees.db'
USERS_FILE = 'users.json'

# ensure db exists
if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()

# load users
with open(USERS_FILE, 'r') as f:
    users = json.load(f)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for u in users:
            if u['username']==username and u['password']==password:
                session['user']=u
                return redirect(url_for('index'))
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('login'))

def @app.route('/', methods=['GET'])
@login_required
def index():
    ...
(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args,**kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated

@app.route('/', methods=['GET'])
@login_required
def index():
 @app.route('/', methods=['GET'])
@login_required
def index():
    conn = get_db()
    rows = conn.execute("SELECT * FROM trainees").fetchall()
    conn.close()
    # summary calculation …
    return render_template('index.html', rows=rows,
                           total=total, passed=passed, failed=failed,
                           apprenticeship=apprenticeship, employment=employment,
                           higher=higher, selfemp=selfemp)
   ...



