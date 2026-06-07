from flask import Flask, render_template, request, redirect, session, Response, make_response
import sqlite3
import os
from functools import wraps
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


app = Flask(__name__)
app.secret_key = "semas_secret_key"

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "employee_system.db")


def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return route_function(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/")

        return "Invalid username or password"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def dashboard():
    conn = get_db_connection()

    total_employees = conn.execute(
        "SELECT COUNT(*) FROM employees"
    ).fetchone()[0]

    active_employees = conn.execute(
        "SELECT COUNT(*) FROM employees WHERE LOWER(TRIM(status)) = 'active'"
    ).fetchone()[0]

    total_attendance = conn.execute(
        "SELECT COUNT(*) FROM attendance"
    ).fetchone()[0]

    total_leave_requests = conn.execute(
        "SELECT COUNT(*) FROM leave_requests"
    ).fetchone()[0]

    pending_leaves = conn.execute(
        "SELECT COUNT(*) FROM leave_requests WHERE LOWER(TRIM(status)) = 'pending'"
    ).fetchone()[0]

    department_rows = conn.execute("""
        SELECT 
            CASE 
                WHEN department IS NULL OR TRIM(department) = '' THEN 'Unknown'
                ELSE department
            END AS department,
            COUNT(*) AS count
        FROM employees
        GROUP BY 
            CASE 
                WHEN department IS NULL OR TRIM(department) = '' THEN 'Unknown'
                ELSE department
            END
    """).fetchall()

    attendance_rows = conn.execute("""
        SELECT 
            CASE 
                WHEN status IS NULL OR TRIM(status) = '' THEN 'Unknown'
                ELSE LOWER(TRIM(status))
            END AS status,
            COUNT(*) AS count
        FROM attendance
        GROUP BY 
            CASE 
                WHEN status IS NULL OR TRIM(status) = '' THEN 'Unknown'
                ELSE LOWER(TRIM(status))
            END
    """).fetchall()

    leave_rows = conn.execute("""
        SELECT 
            CASE 
                WHEN status IS NULL OR TRIM(status) = '' THEN 'Unknown'
                ELSE LOWER(TRIM(status))
            END AS status,
            COUNT(*) AS count
        FROM leave_requests
        GROUP BY 
            CASE 
                WHEN status IS NULL OR TRIM(status) = '' THEN 'Unknown'
                ELSE LOWER(TRIM(status))
            END
    """).fetchall()

    conn.close()

    departments = [row["department"] for row in department_rows]
    department_counts = [row["count"] for row in department_rows]

    attendance_statuses = [
        row["status"].capitalize() if row["status"] != "Unknown" else "Unknown"
        for row in attendance_rows
    ]
    attendance_counts = [row["count"] for row in attendance_rows]

    leave_statuses = [
        row["status"].capitalize() if row["status"] != "Unknown" else "Unknown"
        for row in leave_rows
    ]
    leave_counts = [row["count"] for row in leave_rows]

    return render_template(
        "index.html",
        total_employees=total_employees,
        active_employees=active_employees,
        total_attendance=total_attendance,
        total_leave_requests=total_leave_requests,
        pending_leaves=pending_leaves,
        departments=departments,
        department_counts=department_counts,
        attendance_statuses=attendance_statuses,
        attendance_counts=attendance_counts,
        leave_statuses=leave_statuses,
        leave_counts=leave_counts
    )


@app.route("/employees")
@login_required
def employees():
    search = request.args.get("search", "")

    conn = get_db_connection()

    if search:
        all_employees = conn.execute("""
            SELECT * FROM employees
            WHERE first_name LIKE ?
               OR last_name LIKE ?
               OR department LIKE ?
               OR position LIKE ?
               OR email LIKE ?
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()
    else:
        all_employees = conn.execute("SELECT * FROM employees").fetchall()

    conn.close()

    return render_template(
        "employees.html",
        employees=all_employees,
        search=search
    )


@app.route("/add-employee", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        conn = get_db_connection()

        conn.execute("""
            INSERT INTO employees
            (first_name, last_name, email, phone, department, position, hire_date, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["first_name"],
            request.form["last_name"],
            request.form["email"],
            request.form["phone"],
            request.form["department"],
            request.form["position"],
            request.form["hire_date"],
            request.form["salary"]
        ))

        conn.commit()
        conn.close()

        return redirect("/employees")

    return render_template("add_employee.html")


@app.route("/edit-employee/<int:id>", methods=["GET", "POST"])
@login_required
def edit_employee(id):
    conn = get_db_connection()
    employee = conn.execute(
        "SELECT * FROM employees WHERE id = ?", (id,)
    ).fetchone()

    if request.method == "POST":
        conn.execute("""
            UPDATE employees
            SET first_name = ?, last_name = ?, email = ?, phone = ?,
                department = ?, position = ?, hire_date = ?, salary = ?, status = ?
            WHERE id = ?
        """, (
            request.form["first_name"],
            request.form["last_name"],
            request.form["email"],
            request.form["phone"],
            request.form["department"],
            request.form["position"],
            request.form["hire_date"],
            request.form["salary"],
            request.form["status"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/employees")

    conn.close()

    return render_template("edit_employee.html", employee=employee)


@app.route("/delete-employee/<int:id>")
@login_required
def delete_employee(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM employees WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/employees")


@app.route("/export-employees")
@login_required
def export_employees():
    conn = get_db_connection()
    employees_data = conn.execute("SELECT * FROM employees").fetchall()
    conn.close()

    csv_data = "ID,First Name,Last Name,Email,Phone,Department,Position,Hire Date,Salary,Status\n"

    for emp in employees_data:
        csv_data += (
            f"{emp['id']},{emp['first_name']},{emp['last_name']},{emp['email']},"
            f"{emp['phone']},{emp['department']},{emp['position']},"
            f"{emp['hire_date']},{emp['salary']},{emp['status']}\n"
        )

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"}
    )


@app.route("/export-employees-pdf")
@login_required
def export_employees_pdf():
    conn = get_db_connection()
    employees_data = conn.execute("SELECT * FROM employees").fetchall()
    conn.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Employee Report", styles["Title"]),
        Spacer(1, 12)
    ]

    data = [
        ["ID", "First Name", "Last Name", "Email", "Department", "Position", "Salary", "Status"]
    ]

    for emp in employees_data:
        data.append([
            emp["id"],
            emp["first_name"],
            emp["last_name"],
            emp["email"],
            emp["department"],
            emp["position"],
            emp["salary"],
            emp["status"]
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=employees_report.pdf"

    return response


@app.route("/attendance")
@login_required
def attendance():
    conn = get_db_connection()

    records = conn.execute("""
        SELECT attendance.id, employees.first_name, employees.last_name,
               attendance.date, attendance.check_in, attendance.check_out, attendance.status
        FROM attendance
        JOIN employees ON attendance.employee_id = employees.id
    """).fetchall()

    conn.close()

    return render_template("attendance.html", records=records)


@app.route("/add-attendance", methods=["GET", "POST"])
@login_required
def add_attendance():
    conn = get_db_connection()
    employee_list = conn.execute(
        "SELECT id, first_name, last_name FROM employees"
    ).fetchall()

    if request.method == "POST":
        conn.execute("""
            INSERT INTO attendance
            (employee_id, date, check_in, check_out, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["employee_id"],
            request.form["date"],
            request.form["check_in"],
            request.form["check_out"],
            request.form["status"]
        ))

        conn.commit()
        conn.close()

        return redirect("/attendance")

    conn.close()

    return render_template("add_attendance.html", employees=employee_list)


@app.route("/export-attendance-pdf")
@login_required
def export_attendance_pdf():
    conn = get_db_connection()

    records = conn.execute("""
        SELECT attendance.id, employees.first_name, employees.last_name,
               attendance.date, attendance.check_in, attendance.check_out, attendance.status
        FROM attendance
        JOIN employees ON attendance.employee_id = employees.id
    """).fetchall()

    conn.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Attendance Report", styles["Title"]),
        Spacer(1, 12)
    ]

    data = [
        ["ID", "First Name", "Last Name", "Date", "Check In", "Check Out", "Status"]
    ]

    for record in records:
        data.append([
            record["id"],
            record["first_name"],
            record["last_name"],
            record["date"],
            record["check_in"],
            record["check_out"],
            record["status"]
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=attendance_report.pdf"

    return response


@app.route("/leave-requests")
@login_required
def leave_requests():
    conn = get_db_connection()

    requests_data = conn.execute("""
        SELECT leave_requests.id, employees.first_name, employees.last_name,
               leave_requests.leave_type, leave_requests.start_date,
               leave_requests.end_date, leave_requests.reason, leave_requests.status
        FROM leave_requests
        JOIN employees ON leave_requests.employee_id = employees.id
    """).fetchall()

    conn.close()

    return render_template("leave_requests.html", requests=requests_data)


@app.route("/add-leave-request", methods=["GET", "POST"])
@login_required
def add_leave_request():
    conn = get_db_connection()
    employee_list = conn.execute(
        "SELECT id, first_name, last_name FROM employees"
    ).fetchall()

    if request.method == "POST":
        conn.execute("""
            INSERT INTO leave_requests
            (employee_id, leave_type, start_date, end_date, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["employee_id"],
            request.form["leave_type"],
            request.form["start_date"],
            request.form["end_date"],
            request.form["reason"]
        ))

        conn.commit()
        conn.close()

        return redirect("/leave-requests")

    conn.close()

    return render_template("add_leave_request.html", employees=employee_list)


@app.route("/approve-leave/<int:id>")
@login_required
def approve_leave(id):
    conn = get_db_connection()

    conn.execute(
        "UPDATE leave_requests SET status = 'Approved' WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/leave-requests")


@app.route("/reject-leave/<int:id>")
@login_required
def reject_leave(id):
    conn = get_db_connection()

    conn.execute(
        "UPDATE leave_requests SET status = 'Rejected' WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/leave-requests")


@app.route("/export-leave-pdf")
@login_required
def export_leave_pdf():
    conn = get_db_connection()

    requests_data = conn.execute("""
        SELECT leave_requests.id, employees.first_name, employees.last_name,
               leave_requests.leave_type, leave_requests.start_date,
               leave_requests.end_date, leave_requests.reason, leave_requests.status
        FROM leave_requests
        JOIN employees ON leave_requests.employee_id = employees.id
    """).fetchall()

    conn.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Leave Requests Report", styles["Title"]),
        Spacer(1, 12)
    ]

    data = [
        ["ID", "Employee", "Type", "Start", "End", "Reason", "Status"]
    ]

    for req in requests_data:
        data.append([
            req["id"],
            req["first_name"] + " " + req["last_name"],
            req["leave_type"],
            req["start_date"],
            req["end_date"],
            req["reason"],
            req["status"]
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=leave_requests_report.pdf"

    return response


@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html")


if __name__ == "__main__":
    app.run(debug=True)