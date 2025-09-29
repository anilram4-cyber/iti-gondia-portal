# ITI Gondia – Trainee Search & Monitoring Portal

## Quick Start
1. Create a Python venv and install requirements:
```
pip install -r requirements.txt
```
2. Run:
```
python app.py
```
3. Open: http://127.0.0.1:5000

## Login
- Admin: **admin / admin123**
- Viewer: **viewer / view123**

Admin can upload CSV and sees full data. Viewer sees masked Email/Contact or 'NA' if flagged.

## CSV Columns
```
StudentID,StudentName,Gender,Category,Trade,AcademicYear,Result,CurrentStatus,StatusDetails,ContactNo,Email,LastUpdated,Remarks,HideContact,HideEmail
```
- `HideContact`, `HideEmail` -> 1 to force NA for everyone except Admin.
- Keep `AcademicYear` like 2020-21, 2021-22, etc.

## Upload
Admin can go to **Upload** and choose "Replace all data" or "Append".

## Export
Use Export buttons for **Excel** or **CSV**. Viewer exports are masked as on-screen.
