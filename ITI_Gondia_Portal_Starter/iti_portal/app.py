from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import sqlite3, os, io, csv, datetime as dt
import pandas as pd
import xlsxwriter

APP_SECRET = "change-me"
DB_PATH = "portal.db"

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with open("schema.sql","r") as f:
        sql = f.read()
    con = get_db()
    con.executescript(sql)
    con.commit()
    con.close()

def ensure_db():
    if not os.path.exists(DB_PATH):
        init_db()

def mask_value(val, hide_flag, is_admin):
    if is_admin:
        return val or ""
    if hide_flag:
        return "NA"
    # viewer: default is allowed but blank -> "NA" if empty?
    return val if (val and val.strip()) else "NA"

def fetch_filters(con):
    years = [r["AcademicYear"] for r in con.execute("SELECT DISTINCT AcademicYear FROM trainees ORDER BY AcademicYear").fetchall()]
    trades = [r["Trade"] for r in con.execute("SELECT DISTINCT Trade FROM trainees ORDER BY Trade").fetchall()]
    statuses = [r["CurrentStatus"] for r in con.execute("SELECT DISTINCT CurrentStatus FROM trainees ORDER BY CurrentStatus").fetchall()]
    cats = [r["Category"] for r in con.execute("SELECT DISTINCT Category FROM trainees ORDER BY Category").fetchall()]
    return {"years": years, "trades": trades, "statuses": statuses, "categories": cats}

def build_where(args):
    wh = []
    params = []
    if args.get("year"):
        wh.append("AcademicYear=?"); params.append(args["year"])
    if args.get("trade"):
        wh.append("Trade=?"); params.append(args["trade"])
    if args.get("status"):
        wh.append("CurrentStatus=?"); params.append(args["status"])
    if args.get("result"):
        wh.append("Result=?"); params.append(args["result"])
    if args.get("category"):
        wh.append("Category=?"); params.append(args["category"])
    if args.get("q"):
        wh.append("(StudentName LIKE ? OR StudentID LIKE ? OR StatusDetails LIKE ?)")
        q = f"%{args['q']}%"; params += [q,q,q]
    where = " WHERE " + " AND ".join(wh) if wh else ""
    return where, params

def kpis(con, where="", params=None):
    params = params or []
    total = con.execute(f"SELECT COUNT(*) c FROM trainees {where}", params).fetchone()["c"]
    pass_count = con.execute(f"SELECT COUNT(*) c FROM trainees {where} AND Result='Pass'" if where else "SELECT COUNT(*) c FROM trainees WHERE Result='Pass'", params).fetchone()["c"]
    fail_count = con.execute(f"SELECT COUNT(*) c FROM trainees {where} AND Result='Fail'" if where else "SELECT COUNT(*) c FROM trainees WHERE Result='Fail'", params).fetchone()["c"]
    unplaced = con.execute(f"SELECT COUNT(*) c FROM trainees {where} AND CurrentStatus='Unplaced'" if where else "SELECT COUNT(*) c FROM trainees WHERE CurrentStatus='Unplaced'", params).fetchone()["c"]
    return {"total": total, "pass_count": pass_count, "fail_count": fail_count, "unplaced": unplaced}

app = Flask(__name__)
app.secret_key = APP_SECRET

USERS = {
    "admin": {"password":"admin123", "role":"admin"},
    "viewer": {"password":"view123", "role":"viewer"}
}

@app.context_processor
def inject_year():
    return {"year": dt.date.today().year}

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()
        user = USERS.get(u)
        if user and user["password"] == p:
            session["user"] = u
            session["role"] = user["role"]
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
def index():
    ensure_db()
    if not session.get("user"):
        return redirect(url_for("login"))
    con = get_db()
    filters = fetch_filters(con)
    args = {k: request.args.get(k,"").strip() or "" for k in ["year","trade","status","result","category","q"]}
    where, params = build_where(args)
    rows = con.execute(f"SELECT * FROM trainees {where} ORDER BY AcademicYear DESC, Trade, StudentName LIMIT 1000", params).fetchall()
    is_admin = session.get("role")=="admin"
    masked = []
    for r in rows:
        masked.append({
            "StudentID": r["StudentID"],
            "StudentName": r["StudentName"],
            "Trade": r["Trade"],
            "AcademicYear": r["AcademicYear"],
            "Result": r["Result"],
            "CurrentStatus": r["CurrentStatus"],
            "StatusDetails": r["StatusDetails"],
            "ContactNo": mask_value(r["ContactNo"], r["HideContact"], is_admin),
            "Email": mask_value(r["Email"], r["HideEmail"], is_admin),
            "LastUpdated": r["LastUpdated"],
        })
    stats = kpis(con, where, params)
    con.close()
    class Q: pass
    q = Q(); q.year=args["year"]; q.trade=args["trade"]; q.status=args["status"]; q.result=args["result"]; q.category=args["category"]; q.q=args["q"]
    q.to_dict = lambda: {"year":q.year,"trade":q.trade,"status":q.status,"result":q.result,"category":q.category,"q":q.q}
    return render_template("index.html", rows=masked, filters=filters, query=q, kpi=stats)

@app.route("/upload", methods=["GET","POST"])
def upload():
    ensure_db()
    if session.get("role")!="admin":
        return redirect(url_for("index"))
    if request.method=="POST":
        f = request.files.get("file")
        if not f:
            return "No file", 400
        df = pd.read_csv(f)
        required = ["StudentID","StudentName","Gender","Category","Trade","AcademicYear","Result","CurrentStatus","StatusDetails","ContactNo","Email","LastUpdated","Remarks","HideContact","HideEmail"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            return f"Missing columns: {missing}", 400
        df = df[required].fillna("")
        con = get_db()
        if request.form.get("replace")=="1":
            con.execute("DELETE FROM trainees")
            con.commit()
        for _, row in df.iterrows():
            con.execute("""INSERT INTO trainees
                (StudentID,StudentName,Gender,Category,Trade,AcademicYear,Result,CurrentStatus,StatusDetails,ContactNo,Email,LastUpdated,Remarks,HideContact,HideEmail)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (row["StudentID"],row["StudentName"],row["Gender"],row["Category"],row["Trade"],row["AcademicYear"],row["Result"],row["CurrentStatus"],row["StatusDetails"],
                 row["ContactNo"],row["Email"],row["LastUpdated"],row["Remarks"],int(row["HideContact"] or 0),int(row["HideEmail"] or 0))
            )
        con.commit()
        con.close()
        return redirect(url_for("index"))
    return render_template("upload.html")

@app.route("/export")
def export_data():
    ensure_db()
    if not session.get("user"):
        return redirect(url_for("login"))
    fmt = request.args.get("fmt","csv")
    con = get_db()
    args = {k: request.args.get(k,"").strip() or "" for k in ["year","trade","status","result","category","q"]}
    where, params = build_where(args)
    rows = con.execute(f"SELECT * FROM trainees {where} ORDER BY AcademicYear DESC, Trade, StudentName", params).fetchall()
    is_admin = session.get("role")=="admin"
    con.close()

    records = []
    for r in rows:
        records.append({
            "StudentID": r["StudentID"],
            "StudentName": r["StudentName"],
            "Gender": r["Gender"],
            "Category": r["Category"],
            "Trade": r["Trade"],
            "AcademicYear": r["AcademicYear"],
            "Result": r["Result"],
            "CurrentStatus": r["CurrentStatus"],
            "StatusDetails": r["StatusDetails"],
            "ContactNo": mask_value(r["ContactNo"], r["HideContact"], is_admin),
            "Email": mask_value(r["Email"], r["HideEmail"], is_admin),
            "LastUpdated": r["LastUpdated"],
            "Remarks": r["Remarks"]
        })
    df = pd.DataFrame(records)
    if fmt=="csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(io.BytesIO(buf.getvalue().encode("utf-8")), as_attachment=True, download_name="trainees_export.csv", mimetype="text/csv")
    else:
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Trainees")
        out.seek(0)
        return send_file(out, as_attachment=True, download_name="trainees_export.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/api/trainees")
def api_trainees():
    ensure_db()
    if not session.get("user"):
        return jsonify({"error":"unauthorized"}), 401
    con = get_db()
    args = {k: request.args.get(k,"").strip() or "" for k in ["year","trade","status","result","category","q"]}
    where, params = build_where(args)
    rows = con.execute(f"SELECT * FROM trainees {where} LIMIT 1000", params).fetchall()
    is_admin = session.get("role")=="admin"
    data = []
    for r in rows:
        data.append({
            "StudentID": r["StudentID"],
            "StudentName": r["StudentName"],
            "Trade": r["Trade"],
            "AcademicYear": r["AcademicYear"],
            "Result": r["Result"],
            "CurrentStatus": r["CurrentStatus"],
            "StatusDetails": r["StatusDetails"],
            "ContactNo": mask_value(r["ContactNo"], r["HideContact"], is_admin),
            "Email": mask_value(r["Email"], r["HideEmail"], is_admin),
            "LastUpdated": r["LastUpdated"]
        })
    con.close()
    return jsonify(data)

if __name__ == "__main__":
    ensure_db()
    app.run(debug=True)
