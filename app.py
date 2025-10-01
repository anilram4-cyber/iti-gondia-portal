from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # session/flash के लिए

# -------- Home page ----------
@app.route('/')
def home():
    return render_template('index.html')

# -------- Login page ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # TODO: यहां users.json से verify करना है
        if username == "admin" and password == "123":
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('login.html')

# -------- Upload page ----------
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(request.url)
        if file:
            filepath = os.path.join("uploads", file.filename)
            os.makedirs("uploads", exist_ok=True)
            file.save(filepath)
            flash("File uploaded successfully!", "success")
            return redirect(url_for('home'))
    return render_template('upload.html')

# --------- Run app locally ----------
if __name__ == '__main__':
    app.run(debug=True)
