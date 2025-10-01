from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key-iti'

DB_NAME = 'database.db'

# --- DB init
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trainees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            iti_name TEXT,
            trade TEXT,
            shift TEXT,
            unit TEXT,
            contact TEXT,
            email TEXT,
            apprenticeship TEXT,
            passing_year TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# --- Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == 'admin@iti.com' and password == 'admin':
            session['user'] = 'admin'
            flash('Login successful','success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials','danger')
            return redirect(url_for('login'))
    return render_template('login.html')

# --- Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out','info')
    return redirect(url_for('login'))

# --- Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('SELECT * FROM trainees', conn)
    conn.close()
    total = len(df)
    pass_count = len(df[df['status'].str.lower()=='pass']) if not df.empty else 0
    fail_count = len(df[df['status'].str.lower()=='fail']) if not df.empty else 0
    app_count = len(df[df['apprenticeship'].str.lower()=='yes']) if not df.empty else 0
    job_count = len(df[df['status'].str.lower()=='job']) if not df.empty else 0
    return render_template('index.html',
                           total=total,
                           pass_count=pass_count,
                           fail_count=fail_count,
                           app_count=app_count,
                           job_count=job_count,
                           table=df.to_dict(orient='records'))

# --- Upload
@app.route('/upload', methods=['GET','POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file selected','danger')
            return redirect(url_for('upload'))
        try:
            df = pd.read_csv(file, encoding='latin1', low_memory=False, on_bad_lines='skip')
            # columns adjust
            needed_cols = ['name','iti_name','trade','shift','unit','contact','email','apprenticeship','passing_year','status']
            df = df[needed_cols]
            conn = sqlite3.connect(DB_NAME)
            df.to_sql('trainees', conn, if_exists='append', index=False)
            conn.close()
            flash('Data uploaded successfully','success')
        except Exception as e:
            flash(f'Error reading CSV: {e}','danger')
        return redirect(url_for('upload'))
    return render_template('upload.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
