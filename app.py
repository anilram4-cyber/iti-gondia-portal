from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'replace_this_secret'

DB_FILE = 'database.db'

# DB ensure
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS trainees (
        "ITI Code" TEXT,
        "ITI Name" TEXT,
        "District" TEXT,
        "Roll No." TEXT,
        "TraineeName" TEXT,
        "Trade name" TEXT,
        "Trade code" TEXT,
        "Course Duration" TEXT,
        "session" TEXT,
        "Year" TEXT,
        "Mobile No" TEXT,
        "Result" TEXT,
        "Apprenticeship" TEXT,
        "Employment" TEXT,
        "Self Employment" TEXT,
        "Higher Education" TEXT,
        "Other" TEXT,
        "Remark" TEXT
    );''')
    conn.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # simple login bypass
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM trainees", conn)
    conn.close()
    total = len(df)
    passed = len(df[df['Result'].str.lower()=='pass']) if not df.empty else 0
    failed = len(df[df['Result'].str.lower()=='fail']) if not df.empty else 0
    return render_template('index.html', total=total, passed=passed, failed=failed)

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        if not f:
            flash("No file selected")
            return redirect(url_for('upload'))
        try:
            df = pd.read_csv(f, encoding='utf-8', on_bad_lines='skip')
        except Exception:
            df = pd.read_csv(f, encoding='latin1', on_bad_lines='skip')
        conn = sqlite3.connect(DB_FILE)
        df.to_sql('trainees', conn, if_exists='append', index=False)
        conn.close()
        flash("Data uploaded successfully!")
        return redirect(url_for('dashboard'))
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
