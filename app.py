import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import io

app = Flask(__name__)
app.secret_key = 'replace-with-secure-key'

DB_FILE = 'trainees.db'

# --- Ensure DB file exists ---
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS trainees (
        id INTEGER PRIMARY KEY AUTOINCREMENT
    );
    """)
    conn.close()

# ---------- LOGIN ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # demo login: admin@iti.com / admin
        if email == 'admin@iti.com' and password == 'admin':
            session['user'] = 'admin'
            flash("Login successful")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for('login'))

# ---------- DASHBOARD ----------
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT * FROM trainees", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()

    total = len(df)
    # Example: if your CSV has 'Result' column
    pass_count = len(df[df.get('Result','').astype(str).str.lower()=='pass']) if not df.empty else 0
    fail_count = len(df[df.get('Result','').astype(str).str.lower()=='fail']) if not df.empty else 0

    return render_template('index.html',
        total=total,
        pass_count=pass_count,
        fail_count=fail_count)

# ---------- UPLOAD ----------
@app.route('/upload', methods=['GET','POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        f = request.files.get('file')
        if not f or f.filename.strip() == "":
            flash("No file selected")
            return redirect(url_for('upload'))

        filename = f.filename.lower()
        try:
            if filename.endswith(('.xlsx','.xls')):
                df = pd.read_excel(f, dtype=str)
            elif filename.endswith('.csv'):
                try:
                    df = pd.read_csv(f, encoding='utf-8', on_bad_lines='skip', low_memory=False)
                except Exception:
                    f.stream.seek(0)
                    df = pd.read_csv(f, encoding='latin1', on_bad_lines='skip', engine='python', sep=None, dtype=str)
            else:
                flash("Upload CSV or Excel only")
                return redirect(url_for('upload'))

            if df is None or df.empty:
                flash("Uploaded file empty")
                return redirect(url_for('upload'))

        except Exception as e:
            flash(f"Error reading file: {e}")
            return redirect(url_for('upload'))

        try:
            conn = sqlite3.connect(DB_FILE)
            df.to_sql('trainees', conn, if_exists='replace', index=False)
            conn.close()
        except Exception as e:
            flash(f"Error saving to DB: {e}")
            return redirect(url_for('upload'))

        flash("Data uploaded successfully!")
        return redirect(url_for('dashboard'))

    return render_template('upload.html')

# ---------- DOWNLOAD ----------
@app.route('/download')
def download():
    if 'user' not in session:
        return redirect(url_for('login'))
    fmt = request.args.get('format','csv').lower()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM trainees", conn)
    conn.close()

    if df.empty:
        flash("No data to download")
        return redirect(url_for('dashboard'))

    if fmt=='xlsx':
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df.to_excel(writer,index=False,sheet_name='Trainees')
        out.seek(0)
        return send_file(out,as_attachment=True,download_name='trainees.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        buf = io.StringIO()
        df.to_csv(buf,index=False)
        csv_bytes = io.BytesIO(buf.getvalue().encode('utf-8'))
        return send_file(csv_bytes,as_attachment=True,download_name='trainees.csv',mimetype='text/csv')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)
