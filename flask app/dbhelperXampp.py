import mysql.connector
from mysql.connector import Error
from datetime import datetime
import time

# Database configuration
config = {
    'user': 'root',
    'password': '',  # Default XAMPP MySQL password (empty)
    'host': '127.0.0.1',  # Use IP instead of 'localhost'
    'port': 3306,  # Ensure it's the correct port
    'database': 'student',
    'raise_on_warnings': True
}


# Function to execute queries that modify data (INSERT, UPDATE, DELETE)
def postprocess(sql: str, params=()) -> bool:
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute(sql, params)
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def getprocess(sql: str, params=()) -> list:
    connection = None  # Ensure 'connection' is always defined
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)  # Return results as dictionaries
        cursor.execute(sql, params)
        return cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Retrieve all records from a table
def getall_records(table: str) -> list:
    sql = f"SELECT * FROM {table}"
    return getprocess(sql)

# Retrieve paginated students
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
        LIMIT %s OFFSET %s
    """
    return getprocess(sql, (per_page, offset))

# Retrieve reservations by student ID
def get_reservations_by_student_id(student_id):
    sql = """
        SELECT r.id, r.student_name, r.purpose, l.lab_name, r.reservation_date, r.time_in, r.time_out, r.status
        FROM reservations r
        JOIN laboratories l ON r.lab_id = l.id
        WHERE r.student_idno = %s
    """
    return getprocess(sql, (student_id,))

# Retrieve a student by ID number
def get_student_by_id(idno: str) -> dict:
    sql = "SELECT * FROM students WHERE idno = %s"
    result = getprocess(sql, (idno,))
    return result[0] if result else None

# Retrieve a lab by name
def get_lab_by_name(lab_name: str) -> dict:
    sql = "SELECT * FROM laboratories WHERE lab_name = %s"
    result = getprocess(sql, (lab_name,))
    return result[0] if result else None


# Retrieve a student by email
def get_student_by_email(email: str) -> dict:
    sql = "SELECT * FROM students WHERE email = %s"
    result = getprocess(sql, (email,))
    return result[0] if result else None

# Retrieve a student by username and password
def get_user_by_credentials(username: str, password: str) -> dict:
    sql = "SELECT * FROM students WHERE username = %s AND password = %s"
    result = getprocess(sql, (username, password))
    return result[0] if result else None

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
    sql = "SELECT * FROM students WHERE username = %s"
    result = getprocess(sql, (username,))
    return result[0] if result else None

# Retrieve students by first name
def get_fname_student(firstname: str) -> list:
    sql = "SELECT * FROM students WHERE firstname = %s"
    return getprocess(sql, (firstname,))

# Retrieve admin by username
def get_username_admin(admin_username: str) -> list:
    sql = "SELECT * FROM admin_users WHERE admin_username = %s"
    return getprocess(sql, (admin_username,))

# Retrieve admin's first name
def get_firstname_admin(admin_username: str) -> str:
    sql = "SELECT admin_firstname FROM admin_users WHERE admin_username = %s"
    result = getprocess(sql, (admin_username,))
    return result[0]['admin_firstname'] if result else None

# Retrieve an admin user by username and password
def get_admin_user_by_credentials(admin_username: str, password: str) -> dict:
    sql = "SELECT * FROM admin_users WHERE admin_username = %s AND password = %s"
    result = getprocess(sql, (admin_username, password))
    return result[0] if result else None

# Retrieve an admin by username
def get_admin_by_username(admin_username: str) -> dict:
    sql = "SELECT * FROM admin_users WHERE admin_username = %s"
    result = getprocess(sql, (admin_username,))
    return result[0] if result else None

# Retrieve total sessions left for a student
def get_total_session(idno: str) -> dict:
    sql = "SELECT sessions_left FROM students WHERE idno = %s"
    result = getprocess(sql, (idno,))
    return result[0] if result else None

# Retrieve all announcements
def get_all_announcements() -> list:
    sql = "SELECT * FROM announcements ORDER BY announcement_date DESC"
    return getprocess(sql)

# Retrieve available laboratories
def get_laboratories() -> list:
    sql = "SELECT * FROM laboratories WHERE status = 'Available'"
    return getprocess(sql)

# Retrieve a student by ID number
def get_student_by_idno(student_idno):
    sql = "SELECT * FROM students WHERE idno = %s"
    result = getprocess(sql, (student_idno,))
    return result[0] if result else None

# Retrieve an announcement by ID
def get_announcement_by_id(announcement_id: int) -> dict:
    sql = "SELECT * FROM announcements WHERE id = %s"
    result = getprocess(sql, (announcement_id,))
    return result[0] if result else None

# Retrieve all lab names
def get_lab_names():
    sql = "SELECT id, lab_name FROM laboratories"
    result = getprocess(sql)
    return [{'id': row['id'], 'lab_name': row['lab_name']} for row in result] if result else []

# Update an announcement
def update_announcement(announcement_id: int, announcement_text: str) -> bool:
    sql = "UPDATE announcements SET announcement_text = %s WHERE id = %s"
    return postprocess(sql, (announcement_text, announcement_id))

# Delete an announcement
def delete_announcement(announcement_id: int) -> bool:
    sql = "DELETE FROM announcements WHERE id = %s"
    return postprocess(sql, (announcement_id,))

# Add a new record to a table
def add_record(table: str, **kwargs) -> bool:
    fields = ", ".join(kwargs.keys())
    placeholders = ", ".join(["%s" for _ in kwargs])
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

    set_clause = ", ".join([f"{key} = %s" for key in keys[1:]])
    sql = f"UPDATE {table} SET {set_clause} WHERE {keys[0]} = %s"
    return postprocess(sql, values[1:] + [values[0]])

# Delete a record from a table
def delete_record(table: str, **kwargs) -> bool:
    key = list(kwargs.keys())[0]
    value = kwargs[key]

    sql = f"DELETE FROM {table} WHERE {key} = %s"
    return postprocess(sql, (value,))

# Update student sessions
def update_student_sessions(idno, sessions_left):
    sql = "UPDATE students SET sessions_left = %s WHERE idno = %s"
    success = postprocess(sql, (sessions_left, idno))
    if success:
        print("Sessions updated successfully!")
    else:
        print("Failed to update sessions.")
    return success

# Insert session history
def insert_session_history(student_idno, login_time):
    sql = "INSERT INTO session_history (student_idno, login_time) VALUES (%s, %s)"
    return postprocess(sql, (student_idno, login_time))

# Update session history
def update_session_history(student_idno, logout_time):
    sql = """
        UPDATE session_history
        SET logout_time = %s,
            duration = TIMESTAMPDIFF(SECOND, login_time, %s)
        WHERE student_idno = %s AND logout_time IS NULL
    """
    return postprocess(sql, (logout_time, logout_time, student_idno))

# Insert extension request
def insert_extension_request(student_idno, request_time):
    sql = "INSERT INTO extension_requests (student_idno, request_time) VALUES (%s, %s)"
    return postprocess(sql, (student_idno, request_time))

# Retrieve all reservations
def get_all_reservations():
    sql = "SELECT * FROM reservations WHERE status = 'Pending'"
    return getprocess(sql)

# Create a reservation
def create_reservation(student_idno: str, student_name: str, lab_id: str, 
                      purpose: str, reservation_date: str, time_in: str, 
                      time_out: str, status: str = "Pending") -> bool:
    sql = """
        INSERT INTO reservations 
        (student_idno, student_name, lab_id, purpose, reservation_date, time_in, time_out, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    return postprocess(sql, (student_idno, student_name, lab_id, purpose, 
                           reservation_date, time_in, time_out, status))

# Retrieve student session history
def get_student_session_history(student_idno: str, limit: int = 30) -> list:
    sql = """
        SELECT * FROM session_history
        WHERE student_idno = %s
        ORDER BY id DESC
        LIMIT %s
    """
    return getprocess(sql, (student_idno, limit))

# Retrieve student weekly usage
def get_student_weekly_usage(student_idno: str) -> dict:
    sql = """
        SELECT DAYOFWEEK(login_time) AS day, COUNT(*) AS session_count
        FROM session_history
        WHERE student_idno = %s
        GROUP BY day
        ORDER BY day;
    """
    usage_data = getprocess(sql, (student_idno,))
    
    day_mapping = {
        1: 'Sunday',
        2: 'Monday',
        3: 'Tuesday',
        4: 'Wednesday',
        5: 'Thursday',
        6: 'Friday',
        7: 'Saturday'
    }
    
    return {day_mapping.get(row['day'], 0): row['session_count'] for row in usage_data}

# Retrieve student activity breakdown
def get_student_activity_breakdown(student_idno: str) -> dict:
    sql = """
        SELECT purpose, COUNT(*) as count 
        FROM reservations 
        WHERE student_idno = %s
        GROUP BY purpose
    """
    results = getprocess(sql, (student_idno,))
    return {row['purpose']: row['count'] for row in results}

# Update reservation status
def update_reservation_status(reservation_id: int, status: str) -> bool:
    sql = "UPDATE reservations SET status = %s WHERE id = %s"
    return postprocess(sql, (status, reservation_id))