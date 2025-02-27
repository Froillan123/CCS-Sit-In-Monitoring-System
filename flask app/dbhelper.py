from sqlite3 import connect, Row
from datetime import datetime
import sqlite3
import time
database = "student.db"

# Function to execute queries that modify data (INSERT, UPDATE, DELETE)
def postprocess(sql: str, params=()) -> bool:
    db = connect(database)
    cursor = db.cursor()
    try:
        cursor.execute(sql, params)
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        db.close()

# Function to execute queries that retrieve data (SELECT)
def getprocess(sql: str, params=()) -> list:
    db = connect(database)
    db.row_factory = Row
    cursor = db.cursor()
    try:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        db.close()

# Retrieve all records from a table
def getall_records(table: str) -> list:
    sql = f"SELECT * FROM {table}"
    return getprocess(sql)

def get_all_students() -> list:
    sql = "SELECT * FROM students"
    return getprocess(sql)  # Ensure this returns a list of dictionaries

def get_paginated_students(offset, per_page):
    sql = """
        SELECT 
            idno, 
            firstname, 
            lastname, 
            midname, 
            course, 
            year_level, 
            email 
        FROM students
        LIMIT ? OFFSET ?
    """
    students = getprocess(sql, (per_page, offset))
    return students

def get_reservations_by_student_id(student_id):
    # Assuming you're using SQLite
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()

    query = """
    SELECT r.id, r.student_name, r.purpose, l.lab_name, r.reservation_date, r.time_in, r.time_out, r.status
    FROM reservations r
    JOIN laboratories l ON r.lab_id = l.id
    WHERE r.student_idno = ?
    """
    cursor.execute(query, (student_id,))
    reservations = cursor.fetchall()

    conn.close()
    return reservations

# Retrieve a student by ID number
def get_student_by_id(idno: str) -> dict:
    sql = "SELECT * FROM students WHERE idno = ?"
    student = getprocess(sql, (idno,))
    return student[0] if student else None

def get_lab_by_name(lab_name: str) -> dict:
    sql = "SELECT * FROM laboratories  WHERE lab_name = ?"
    lab_name = getprocess(sql, (lab_name,))
    return lab_name[0] if lab_name else None


# Retrieve a student by email
def get_student_by_email(email: str) -> dict:
    sql = "SELECT * FROM students WHERE email = ?"
    student = getprocess(sql, (email,))
    return student[0] if student else None

# Retrieve a student by username and password
def get_user_by_credentials(username: str, password: str) -> dict:
    sql = "SELECT * FROM students WHERE username = ? AND password = ?"
    user = getprocess(sql, (username, password))
    return user[0] if user else None

# Retrieve the total count of students
def get_count_students() -> int:
    sql = "SELECT COUNT(*) FROM students"
    result = getprocess(sql)
    return result[0]["COUNT(*)"] if result else 0

# Retrieve the total count of laboratories
def get_count_laboratories() -> int:
    sql = "SELECT COUNT(*) FROM laboratories"
    result = getprocess(sql)
    return result[0]["COUNT(*)"] if result else 0


# Retrieve a student by username
def get_student_by_username(username: str) -> dict:
    sql = "SELECT * FROM students WHERE username = ?"
    student = getprocess(sql, (username,))
    return student[0] if student else None

# Retrieve students by first name
def get_fname_student(firstname: str) -> list:
    sql = "SELECT * FROM students WHERE firstname = ?"
    return getprocess(sql, (firstname,))


def get_username_admin(admin_username: str) -> list:
    sql = "SELECT * FROM admin_users WHERE admin_username = ?"
    return getprocess(sql, (admin_username,))

def get_firstname_admin(admin_firstname: str) -> str:
    sql = "SELECT admin_firstname FROM admin_users WHERE admin_firstname = ?"
    result = getprocess(sql, (admin_firstname,))
    if result:
        return result[0]['admin_firstname']  # Return the first name
    return None


# Retrieve an admin user by username and password
def get_admin_user_by_credentials(admin_username: str, password: str) -> dict:
    sql = "SELECT * FROM admin_users WHERE admin_username = ? AND password = ?"
    admin_user = getprocess(sql, (admin_username, password))
    return admin_user[0] if admin_user else None

# Retrieve an admin by username
def get_admin_by_username(admin_username: str) -> dict:
    sql = "SELECT * FROM admin_users WHERE admin_username = ?"
    admin = getprocess(sql, (admin_username,))
    return admin[0] if admin else None


def get_total_session(idno: str) -> dict:
    sql = "SELECT sessions_left FROM students WHERE idno = ?"
    session = getprocess(sql, (idno,))
    return session[0] if session else None




# Function to retrieve all announcements from the database
def get_all_announcements() -> list:
    sql = "SELECT * FROM announcements ORDER BY announcement_date DESC"
    return getprocess(sql)

def get_laboratories() -> list:
    sql = "SELECT * FROM laboratories WHERE status = 'Available'"
    labs = getprocess(sql)
    return labs
    
def get_student_by_idno(student_idno):
    # Function to fetch student data by idno
    query = "SELECT * FROM students WHERE idno = ?"
    students = getprocess(query, (student_idno,))
    return students[0] if students else None  # Return the first student or None


# Function to get the announcement by its ID
def get_announcement_by_id(announcement_id: int) -> dict:
    sql = "SELECT * FROM announcements WHERE id = ?"
    result = getprocess(sql, (announcement_id,))
    return result[0] if result else None


def get_lab_names():
    sql = "SELECT id, lab_name FROM laboratories"  # Include the lab ID in the query
    result = getprocess(sql)  # Assuming getprocess() executes queries correctly
    return [{'id': row['id'], 'lab_name': row['lab_name']} for row in result] if result else []  # Return a list of dictionaries


# Function to update an announcement (if needed)
def update_announcement(announcement_id: int, announcement_text: str) -> bool:
    sql = "UPDATE announcements SET announcement_text = ? WHERE id = ?"
    params = (announcement_text, announcement_id)
    return postprocess(sql, params)



# Function to delete an announcement
def delete_announcement(announcement_id: int) -> bool:
    sql = "DELETE FROM announcements WHERE id = ?"
    return postprocess(sql, (announcement_id,))


# Add a new record to a table
def add_record(table: str, **kwargs) -> bool:
    fields = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?" for _ in kwargs])
    values = tuple(kwargs.values())

    sql = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
    return postprocess(sql, values)

# Update an existing record in a table
def update_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())

    if len(keys) < 2:
        print("Error: Must provide at least one field to update and a primary key.")
        return False

    set_clause = ", ".join([f"{key} = ?" for key in keys[1:]])
    sql = f"UPDATE {table} SET {set_clause} WHERE {keys[0]} = ?"
    
    return postprocess(sql, values[1:] + [values[0]])

# Delete a record from a table
def delete_record(table: str, **kwargs) -> bool:
    key = list(kwargs.keys())[0]
    value = kwargs[key]

    sql = f"DELETE FROM {table} WHERE {key} = ?"
    return postprocess(sql, (value,))

def update_student_sessions(idno, sessions_left):
    query = "UPDATE students SET sessions_left = ? WHERE idno = ?"
    success = postprocess(query, (sessions_left, idno))
    if success:
        print("Sessions updated successfully!")
    else:
        print("Failed to update sessions.")
    return success


def insert_session_history(student_idno, login_time):
    sql = "INSERT INTO session_history (student_idno, login_time) VALUES (?, ?)"
    return postprocess(sql, (student_idno, login_time))

def update_session_history(student_idno, logout_time):
    sql = """
        UPDATE session_history
        SET logout_time = ?,
            duration = strftime('%s', ?) - strftime('%s', login_time)
        WHERE student_idno = ? AND logout_time IS NULL
    """
    return postprocess(sql, (logout_time, logout_time, student_idno))


def insert_extension_request(student_idno, request_time):
    sql = "INSERT INTO extension_requests (student_idno, request_time) VALUES (?, ?)"
    return postprocess(sql, (student_idno, request_time))


def get_all_reservations():
    try:
        db = sqlite3.connect('student.db')
        db.row_factory = sqlite3.Row  # Enables dictionary-like access
        cursor = db.cursor()

        # Fetch only reservations that are pending
        cursor.execute("SELECT * FROM reservations WHERE status = 'Pending'")
        reservations = cursor.fetchall()

        return [dict(row) for row in reservations]  # Convert rows to dictionaries

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

    finally:
        db.close()


def create_reservation(student_idno: str, student_name: str, lab_id: str, 
                      purpose: str, reservation_date: str, time_in: str, 
                      time_out: str, status: str = "Pending") -> bool:
    sql = """
        INSERT INTO reservations 
        (student_idno, student_name, lab_id, purpose, reservation_date, time_in, time_out, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    return postprocess(sql, (student_idno, student_name, lab_id, purpose, 
                           reservation_date, time_in, time_out, status))


def get_student_session_history(student_idno: str, limit: int = 30) -> list:
    sql = """
        SELECT * FROM session_history
        WHERE student_idno = ?
        ORDER BY id 
        LIMIT ?
    """
    return getprocess(sql, (student_idno, limit))


def get_student_weekly_usage(student_idno: str) -> dict:
    sql = """
        SELECT strftime('%w', login_time) AS day, COUNT(*) AS session_count
        FROM session_history
        WHERE student_idno = ? AND strftime('%w', login_time) BETWEEN '0' AND '6'
        GROUP BY day
        ORDER BY day;
    """
    usage_data = getprocess(sql, (student_idno,))
    
    day_mapping = {
        '0': 'Sunday',
        '1': 'Monday',
        '2': 'Tuesday',
        '3': 'Wednesday',
        '4': 'Thursday',
        '5': 'Friday',
        '6': 'Saturday'
    }
    
    return {day_mapping.get(row['day'], 0): row['session_count'] for row in usage_data}


def get_student_activity_breakdown(student_idno: str) -> dict:
    sql = """
        SELECT purpose, COUNT(*) as count 
        FROM reservations 
        WHERE student_idno = ?
        GROUP BY purpose
    """
    results = getprocess(sql, (student_idno,))
    return {row['purpose']: row['count'] for row in results}

def update_reservation_status(reservation_id: int, status: str) -> bool:
    sql = "UPDATE reservations SET status = ? WHERE id = ?"
    return postprocess(sql, (status, reservation_id))


# Save a message to the database
def save_message(student_idno, message, sender):
    sql = 'INSERT INTO chat_history (student_idno, message, sender) VALUES (?, ?, ?)'
    params = (student_idno, message, sender)
    return postprocess(sql, params)

# Retrieve chat history for a student
def get_chat_history(student_idno):
    sql = 'SELECT * FROM chat_history WHERE student_idno = ? ORDER BY timestamp'
    params = (student_idno,)
    return getprocess(sql, params)


def get_unread_notifications_from_db(user_id):
    # Fetch unread notifications for the given user
    query = """
        SELECT n.id, a.admin_username, a.announcement_text, a.announcement_date, n.is_read
        FROM notifications n
        JOIN announcements a ON n.announcement_id = a.id
        WHERE n.user_id = %s AND n.is_read = FALSE
        ORDER BY a.announcement_date DESC;
    """
    result = getprocess(query, (user_id,))
    return result