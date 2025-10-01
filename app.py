from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, pandas as pd, json, os

app = Flask(__name__)
app.secret_key = "your_secret_key"

DB_FILE = "trainees.db"
USERS_FILE = "users.json"

# --- Database init ---
if not os.path.exists(DB_FILE):
    # create database from schema.sql
    with open("schema.sql", "r") as f:
        schema = f.read()
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(schema)
    conn.close()

# --- Load users for login ---
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
else:
    USERS = {}

# ---------- Routes -------------

@app.route("/")
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith((".csv", ".xlsx")):
            if file.filename.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            # Save data to DB
            conn = sqlite3.connect(DB_FILE)
            df.to_sql("trainees", conn, if_exists="append", index=False)
            conn.close()
            flash("Data uploaded successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Upload a CSV or XLSX file", "warning")

    return render_template("upload.html")

# -------- Run local ----------
if __name__ == "__main__":
    app.run(debug=True)

@app.route('/dashboard')
def dashboard():
    # Example: show dashboard page
    return render_template('index.html')
