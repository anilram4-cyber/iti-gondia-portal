import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'change_this_secret'  # अपने secret key से बदलें

DB_FILE = 'trainees.db'

# ---------- DB Init ----------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS trainees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iti_code TEXT,
            iti_name TEXT,
            district TEXT,
            roll_no TEXT,
            trainee_name TEXT,
            trade_name TEXT,
            trade_code TEXT,
            course_duration TEXT,
            session TEXT,
            year TEXT,
            mobile_no TEXT,
            result TEXT,
            apprenticeship TEXT,
            employment TEXT,
            self_employment TEXT,
            higher_education TEXT,
            other TEXT,
            remark TEXT
        )
        ''')
    print("DB initialized.")

init_db()

# Dummy users (admin/principal)
USERS = {
    'admin': 'admin123',
    'principal': 'principal123'
}

# ---------- Login Required ----------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Routes ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if uname in USERS and USERS[uname] == pwd:
            session['username'] = uname
            flash('Logged in successfully!', 'info')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM trainees", conn)

    if df.empty:
        summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'apprenticeship': 0,
            'employment': 0,
            'self_employment': 0,
            'higher_education': 0
        }
    else:
        summary = {
            'total': len(df),
            'passed': (df['result'].str.lower() == 'pass').sum(),
            'failed': (df['result'].str.lower() == 'fail').sum(),
            'apprenticeship': (df['apprenticeship'].str.lower() == 'yes').sum(),
            'employment': (df['employment'].str.lower() == 'yes').sum(),
            'self_employment': (df['self_employment'].str.lower() == 'yes').sum(),
            'higher_education': (df['higher_education'].str.lower() == 'yes').sum()
        }

    return render_template('index.html', summary=summary)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file selected', 'error')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == '.csv':
                df = pd.read_csv(file)
            elif ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file)
            else:
                flash('Only CSV or Excel files allowed', 'error')
                return redirect(request.url)
        except Exception as e:
            flash(f'Error reading file: {e}', 'error')
            return redirect(request.url)

        # Insert into DB
        with sqlite3.connect(DB_FILE) as conn:
            for _, row in df.iterrows():
                conn.execute('''
                INSERT INTO trainees (
                    iti_code, iti_name, district, roll_no, trainee_name,
                    trade_name, trade_code, course_duration, session, year,
                    mobile_no, result, apprenticeship, employment,
                    self_employment, higher_education, other, remark
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    row.get('ITI code',''),
                    row.get('ITI Name',''),
                    row.get('District',''),
                    row.get('Roll No.',''),
                    row.get('TraineeName',''),
                    row.get('Trade name',''),
                    row.get('Trade code',''),
                    row.get('Course Duration',''),
                    row.get('session',''),
                    row.get('Year',''),
                    row.get('Mobile No',''),
                    row.get('Result Pass /Fail',''),
                    row.get('Apprenticeship  Yes/No',''),
                    row.get('Employment( Yes /NO)',''),
                    row.get('Self Employment( Yes /NO)',''),
                    row.get('Higher Education( Yes /NO)',''),
                    row.get('Other',''),
                    row.get('Remark','')
                ))
            conn.commit()

        flash('Data uploaded successfully', 'info')
        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/download_template')
@login_required
def download_template():
    cols = [
        'ITI code','ITI Name','District','Roll No.','TraineeName',
        'Trade name','Trade code','Course Duration','session','Year',
        'Mobile No','Result Pass /Fail','Apprenticeship  Yes/No',
        'Employment( Yes /NO)','Self Employment( Yes /NO)',
        'Higher Education( Yes /NO)','Other','Remark'
    ]
    df = pd.DataFrame(columns=cols)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True,
                     download_name='iti_template.csv')

@app.route('/download')
@login_required
def download():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM trainees", conn)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True,
                     download_name='trainees_data.csv')

# ---------- Main ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
