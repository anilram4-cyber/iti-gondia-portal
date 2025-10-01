from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'supersecret'  # flash messages

DB_FILE = 'database.db'

# ---------- helper: init db ----------
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        # simple table with flexible columns
        conn.execute("""
        CREATE TABLE IF NOT EXISTS trainees (
            RollNo TEXT,
            StudentName TEXT,
            ITIName TEXT,
            Trade TEXT,
            ShiftNo TEXT,
            UnitNo TEXT,
            ContactNo TEXT,
            Email TEXT,
            Apprenticeship TEXT,
            PassingYear TEXT
        )
        """)
        conn.commit()
        conn.close()

init_db()

# ---------- routes ----------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # no real auth now – just show template
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM trainees", conn)
    conn.close()

    total = len(df)
    passed = len(df[df['Apprenticeship'] == 'Yes']) if 'Apprenticeship' in df else 0
    failed = total - passed
    return render_template('index.html', total=total, passed=passed, failed=failed)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            flash("No file selected")
            return redirect(url_for('upload'))

        try:
            df = pd.read_csv(
                f,
                encoding='latin1',   # or utf-8
                sep=',',
                on_bad_lines='skip',
                engine='python',
                low_memory=False,
                dtype=str
            )
        except Exception as e:
            flash(f"Error reading CSV: {e}")
            return redirect(url_for('upload'))

        conn = sqlite3.connect(DB_FILE)
        # overwrite table to always match csv columns
        df.to_sql('trainees', conn, if_exists='replace', index=False)
        conn.close()

        flash("Data uploaded successfully!")
        return redirect(url_for('dashboard'))

    return render_template('upload.html')

# ---------- run locally ----------
if __name__ == '__main__':
    app.run(debug=True)
