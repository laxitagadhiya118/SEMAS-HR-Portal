import sqlite3

# Create database
conn = sqlite3.connect("employee_system.db")

# Create cursor
cursor = conn.cursor()

# Create Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# Create Employees Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    department TEXT,
    position TEXT,
    hire_date TEXT,
    salary REAL,
    status TEXT DEFAULT 'Active'
)
""")

# Create Attendance Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    date TEXT,
    check_in TEXT,
    check_out TEXT,
    status TEXT,
    FOREIGN KEY(employee_id) REFERENCES employees(id)
)
""")

# Create Leave Requests Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS leave_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    leave_type TEXT,
    start_date TEXT,
    end_date TEXT,
    reason TEXT,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY(employee_id) REFERENCES employees(id)
)
""")

# Save changes
conn.commit()

print("Database created successfully!")

conn.close()