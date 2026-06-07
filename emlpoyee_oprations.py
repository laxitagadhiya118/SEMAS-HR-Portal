import sqlite3
import os
from wsgiref import headers
from tabulate import tabulate


base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "employee_system.db")


def connect_db():
    return sqlite3.connect(db_path)

# Employee CRUD
def add_employee():
    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    email = input("Enter email: ")
    phone = input("Enter phone: ")
    department = input("Enter department: ")
    position = input("Enter position: ")
    hire_date = input("Enter hire date YYYY-MM-DD: ")
    salary = float(input("Enter salary: "))

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO employees 
        (first_name, last_name, email, phone, department, position, hire_date, salary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, email, phone, department, position, hire_date, salary))

    conn.commit()
    conn.close()

    print("Employee added successfully!")


def view_employees():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()

    conn.close()

    headers = [
        "ID",
        "First Name",
        "Last Name",
        "Email",
        "Phone",
        "Department",
        "Position",
        "Hire Date",
        "Salary",
        "Status"
    ]

    if not employees:
        print("No employees found.")
    else:
        print(tabulate(employees, headers=headers, tablefmt="grid"))


def update_employee():
    employee_id = input("Enter employee ID to update: ")

    new_department = input("Enter new department: ")
    new_position = input("Enter new position: ")
    new_salary = float(input("Enter new salary: "))

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE employees
        SET department = ?, position = ?, salary = ?
        WHERE id = ?
    """, (new_department, new_position, new_salary, employee_id))

    conn.commit()
    conn.close()

    print("Employee updated successfully!")


def delete_employee():
    employee_id = input("Enter employee ID to delete: ")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE id = ?
    """, (employee_id,))

    conn.commit()
    conn.close()

    print("Employee deleted successfully!")

# Employee attandance
def mark_attendance():
    employee_id = input("Enter Employee ID: ")
    date = input("Enter Date (YYYY-MM-DD): ")
    check_in = input("Enter Check In Time (HH:MM): ")
    check_out = input("Enter Check Out Time (HH:MM): ")
    status = input("Status (Present/Absent): ")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO attendance
        (employee_id, date, check_in, check_out, status)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, date, check_in, check_out, status))

    conn.commit()
    conn.close()

    print("Attendance marked successfully!")

def view_attendance():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT attendance.id, employees.first_name, employees.last_name,
               attendance.date, attendance.check_in, attendance.check_out, attendance.status
        FROM attendance
        JOIN employees ON attendance.employee_id = employees.id
    """)

    records = cursor.fetchall()
    conn.close()

    headers = ["ID", "First Name", "Last Name", "Date", "Check In", "Check Out", "Status"]
    print(tabulate(records, headers=headers, tablefmt="grid"))

# leave _requests
def add_leave_request():
    employee_id = input("Enter Employee ID: ")
    leave_type = input("Enter leave type: ")
    start_date = input("Enter start date YYYY-MM-DD: ")
    end_date = input("Enter end date YYYY-MM-DD: ")
    reason = input("Enter reason: ")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO leave_requests
        (employee_id, leave_type, start_date, end_date, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, leave_type, start_date, end_date, reason))

    conn.commit()
    conn.close()

    print("Leave request added successfully!")

def view_leave_requests():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT leave_requests.id, employees.first_name, employees.last_name,
               leave_requests.leave_type, leave_requests.start_date,
               leave_requests.end_date, leave_requests.reason, leave_requests.status
        FROM leave_requests
        JOIN employees ON leave_requests.employee_id = employees.id
    """)

    requests = cursor.fetchall()
    conn.close()

    headers = ["ID", "First Name", "Last Name", "Leave Type", "Start Date", "End Date", "Reason", "Status"]
    print(tabulate(requests, headers=headers, tablefmt="grid"))

def update_leave_status():
    leave_id = input("Enter Leave Request ID: ")
    status = input("Enter status Approved/Rejected: ")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE leave_requests
        SET status = ?
        WHERE id = ?
    """, (status, leave_id))

    conn.commit()
    conn.close()

    print("Leave status updated successfully!")

# Total employee management system
def total_employees():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]

    conn.close()

    print("Total Employees:", total)

#active employee
def active_employees():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 'Active'")
    total = cursor.fetchone()[0]

    conn.close()

    print("Active Employees:", total)

#department_wise employee

def department_wise_employees():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT department, COUNT(*)
        FROM employees
        GROUP BY department
    """)

    results = cursor.fetchall()
    conn.close()

    print("\nDepartment Wise Employees")
    for row in results:
        print(row[0], ":", row[1])

#leave_req employee
def leave_request_count():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, COUNT(*)
        FROM leave_requests
        GROUP BY status
    """)

    results = cursor.fetchall()
    conn.close()

    print("\nLeave Requests")
    for row in results:
        print(row[0], ":", row[1])

#attandance_count
def attendance_summary():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, COUNT(*)
        FROM attendance
        GROUP BY status
    """)

    results = cursor.fetchall()
    conn.close()

    print("\nAttendance Summary")
    for row in results:
        print(row[0], ":", row[1])

#add analytics dashboard
def analytics_dashboard():
    print("\n--- Analytics Dashboard ---")
    total_employees()
    active_employees()
    department_wise_employees()
    leave_request_count()
    attendance_summary()



#main menu
while True:
    print("\nEmployee Management System")
    print("1. Add Employee")
    print("2. View Employees")
    print("3. Update Employee")
    print("4. Delete Employee")
    print("5. Mark Attendance")
    print("6. View Attendance")
    print("7. Add Leave Request")
    print("8. View Leave Requests")
    print("9. Approve/Reject Leave")
    print("10. Analytics Dashboard")
    print("11. Exit")
    choice = input("Choose option: ")

    if choice == "1":
        add_employee()
    elif choice == "2":
        view_employees()
    elif choice == "3":
        update_employee()
    elif choice == "4":
        delete_employee()
    elif choice == "5":
        mark_attendance()
    elif choice == "6":
        view_attendance()
    elif choice == "7":
        add_leave_request()
    elif choice == "8":
        view_leave_requests()
    elif choice == "9":
        update_leave_status()
    elif choice == "10":
        analytics_dashboard()
    elif choice == "11":
        print("Goodbye!")
        break
    else:
        print("Invalid choice. Try again.")

