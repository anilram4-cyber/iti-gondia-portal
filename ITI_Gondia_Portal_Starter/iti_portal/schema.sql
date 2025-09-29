
DROP TABLE IF EXISTS trainees;
CREATE TABLE trainees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID TEXT,
    StudentName TEXT,
    Gender TEXT,
    Category TEXT,
    Trade TEXT,
    AcademicYear TEXT,
    Result TEXT,
    CurrentStatus TEXT,
    StatusDetails TEXT,
    ContactNo TEXT,
    Email TEXT,
    LastUpdated TEXT,
    Remarks TEXT,
    HideContact INTEGER DEFAULT 0,
    HideEmail INTEGER DEFAULT 0
);
