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

# create DB if not exists
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

# decorator for login required
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated

@app.route('/', methods=['GET'])
@login_required
def index():
    conn=get_db()
    rows=conn.execute("SELECT * FROM trainees").fetchall()
    conn.close()
    # summary counts
    total=len(rows)
    passed=len([r for r in rows if str(r['Result Pass/Fail']).lower()=='pass'])
    failed=len([r for r in rows if str(r['Result Pass/Fail']).lower()=='fail'])
    apprenticeship=len([r for r in rows if str(r['Apprenticeship Yes/No']).lower()=='yes'])
    employment=len([r for r in rows if str(r['Employment Yes/No']).lower()=='yes'])
    higher=len([r for r in rows if str(r['Higher Education Yes/No']).lower()=='yes'])
    selfemp=len([r for r in rows if str(r['Self Employment Yes/No']).lower()=='yes'])
    return render_template('index.html',
                           rows=rows,total=total,passed=passed,failed=failed,
                           apprenticeship=apprenticeship,employment=employment,
                           higher=higher,selfemp=selfemp)

@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    if session['user']['role'] not in ['admin','principal']:
        flash("Not authorized")
        return redirect(url_for('index'))
    if request.method=='POST':
        file=request.files['file']
        if not file: 
            flash("No file selected")
            return redirect(url_for('upload'))
        filename=secure_filename(file.filename)
        try:
            try:
                df=pd.read_csv(file,encoding='utf-8')
            except UnicodeDecodeError:
                df=pd.read_csv(file,encoding='latin1')
        except Exception as e:
            flash(f"Error reading file: {e}")
            return redirect(url_for('upload'))

        mandatory=["ITI code","ITI Name","TraineeName","Trade name",
                   "Course Duration","session","Year","Mobile No","Result Pass/Fail"]
        skip=[]
        good=[]
        for i,row in df.iterrows():
            if any(pd.isna(row[m]) or str(row[m]).strip()=='' for m in mandatory):
                skip.append(i)
                continue
            good.append(row.fillna(''))

        conn=get_db()
        for r in good:
            vals=[r.get(col,'') for col in df.columns]
            cols=",".join([f'"{c}"' for c in df.columns])
            placeholders=",".join(["?"]*len(df.columns))
            conn.execute(f"INSERT INTO trainees ({cols}) VALUES ({placeholders})",tuple(vals))
        conn.commit()
        conn.close()
        flash(f"Uploaded {len(good)} rows. Skipped {len(skip)} rows.")
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/download_template')
@login_required
def download_template():
    cols=["ITI code","ITI Name","District","Roll No.","TraineeName",
          "Trade name","Trade code","Course Duration","session","Year",
          "Mobile No","Email","Result Pass/Fail","Apprenticeship Yes/No",
          "Employment Yes/No","Self Employment Yes/No","Higher Education Yes/No",
          "Other","Remark"]
    df=pd.DataFrame(columns=cols)
    output=BytesIO()
    df.to_csv(output,index=False)
    output.seek(0)
    return send_file(output,mimetype='text/csv',download_name='template.csv',as_attachment=True)

@app.route('/export')
@login_required
def export():
    conn=get_db()
    rows=conn.execute("SELECT * FROM trainees").fetchall()
    conn.close()
    df=pd.DataFrame(rows)
    if session['user']['role']=='viewer':
        if 'Mobile No' in df.columns: df['Mobile No']='NA'
        if 'Email' in df.columns: df['Email']='NA'
    output=BytesIO()
    df.to_excel(output,index=False,engine='xlsxwriter')
    output.seek(0)
    return send_file(output,mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name='trainees.xlsx',as_attachment=True)

if __name__=='__main__':
    app.run(debug=True)
