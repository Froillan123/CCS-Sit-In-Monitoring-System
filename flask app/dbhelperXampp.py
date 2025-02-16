import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',  # Default XAMPP MySQL username
    'password': '',  # Default XAMPP MySQL password (empty)
    'database': 'student'  # Your database name
}

# Function to execute queries that modify data (INSERT, UPDATE, DELETE)
def postprocess(sql: str, params=()) -> bool:
    try:
        connection = mysql.connector.connect(**db_config)
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

# Function to execute queries that retrieve data (SELECT)
def getprocess(sql: str, params=()) -> list:
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)  # Return results as dictionaries
        cursor.execute(sql, params)
        return cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Retrieve all records from a table
def getall_records(table: str) -> list:
    sql = f"SELECT * FROM {table}"
    return getprocess(sql)

# Retrieve a student by ID number
def get_student_by_id(idno: str) -> dict:
    sql = "SELECT * FROM students WHERE idno = %s"
    student = getprocess(sql, (idno,))
    return student[0] if student else None

# Retrieve a student by email
def get_student_by_email(email: str) -> dict:
    sql = "SELECT * FROM students WHERE email = %s"
    student = getprocess(sql, (email,))
    return student[0] if student else None

# Retrieve a student by username and password
def get_user_by_credentials(username: str, password: str) -> dict:
    sql = "SELECT * FROM students WHERE username = %s AND password = %s"
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
    sql = "SELECT * FROM students WHERE username = %s"
    student = getprocess(sql, (username,))
    return student[0] if student else None

# Retrieve students by first name
def get_fname_student(firstname: str) -> list:
    sql = "SELECT * FROM students WHERE firstname = %s"
    return getprocess(sql, (firstname,))

# Retrieve an admin user by username
def get_username_admin(admin_username: str) -> list:
    sql = "SELECT * FROM admin_users WHERE admin_username = %s"
    return getprocess(sql, (admin_username,))

# Retrieve an admin's first name by username
def get_firstname_admin(admin_username: str) -> str:
    sql = "SELECT admin_firstname FROM admin_users WHERE admin_username = %s"
    result = getprocess(sql, (admin_username,))
    return result[0]['admin_firstname'] if result else None

# Retrieve an admin user by username and password
def get_admin_user_by_credentials(admin_username: str, password: str) -> dict:
    sql = "SELECT * FROM admin_users WHERE admin_username = %s AND password = %s"
    admin_user = getprocess(sql, (admin_username, password))
    return admin_user[0] if admin_user else None

# Retrieve an admin by username
def get_admin_by_username(admin_username: str) -> dict:
    sql = "SELECT * FROM admin_users WHERE admin_username = %s"
    admin = getprocess(sql, (admin_username,))
    return admin[0] if admin else None

# Retrieve the total session count for a student
def get_total_session(idno: str) -> dict:
    sql = "SELECT sessions_left FROM students WHERE idno = %s"
    session = getprocess(sql, (idno,))
    return session[0] if session else None

# Retrieve all announcements from the database
def get_all_announcements() -> list:
    sql = "SELECT * FROM announcements ORDER BY announcement_date DESC"
    return getprocess(sql)

# Retrieve available laboratories
def get_laboratories() -> list:
    sql = "SELECT * FROM laboratories WHERE status = 'Available'"
    return getprocess(sql)

# Retrieve a student by ID number
def get_student_by_idno(student_idno: str) -> dict:
    sql = "SELECT * FROM students WHERE idno = %s"
    students = getprocess(sql, (student_idno,))
    return students[0] if students else None

# Retrieve an announcement by its ID
def get_announcement_by_id(announcement_id: int) -> dict:
    sql = "SELECT * FROM announcements WHERE id = %s"
    result = getprocess(sql, (announcement_id,))
    return result[0] if result else None

# Retrieve lab names and IDs
def get_lab_names() -> list:
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
def update_student_sessions(idno: str, sessions_left: int) -> bool:
    sql = "UPDATE students SET sessions_left = %s WHERE idno = %s"
    return postprocess(sql, (sessions_left, idno))

# Insert session history
def insert_session_history(student_idno: str, login_time: str) -> bool:
    sql = "INSERT INTO session_history (student_idno, login_time) VALUES (%s, %s)"
    return postprocess(sql, (student_idno, login_time))

# Update session history with logout time and duration
def update_session_history(student_idno: str, logout_time: str) -> bool:
    sql = """
        UPDATE session_history
        SET logout_time = %s,
            duration = TIMESTAMPDIFF(SECOND, login_time, %s)
        WHERE student_idno = %s AND logout_time IS NULL
    """
    return postprocess(sql, (logout_time, logout_time, student_idno))

# Insert an extension request
def insert_extension_request(student_idno: str, request_time: str) -> bool:
    sql = "INSERT INTO extension_requests (student_idno, request_time) VALUES (%s, %s)"
    return postprocess(sql, (student_idno, request_time))