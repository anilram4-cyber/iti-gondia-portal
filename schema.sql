-- Users table (optional)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    "ITI code" TEXT NOT NULL,
    "ITI Name" TEXT NOT NULL,
    "District" TEXT,
    "Roll No." TEXT,
    "TraineeName" TEXT NOT NULL,
    "Trade name" TEXT NOT NULL,
    "Trade code" TEXT,
    "Course Duration" TEXT NOT NULL,
    "session" TEXT NOT NULL,
    "Year" TEXT NOT NULL,
    "Mobile No" TEXT NOT NULL,
    "Result" TEXT NOT NULL,
    "Apprenticeship Yes/No" TEXT,
    "Employment( Yes /NO)" TEXT,
    "Self Employment( Yes /NO)" TEXT,
    "Higher Education( Yes /NO)" TEXT,
    "Other" TEXT,
    "Remark" TEXT
);
