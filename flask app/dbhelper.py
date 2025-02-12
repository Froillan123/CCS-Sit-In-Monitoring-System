from sqlite3 import connect, Row
from datetime import datetime
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

# Retrieve a student by ID number
def get_student_by_id(idno: str) -> dict:
    sql = "SELECT * FROM students WHERE idno = ?"
    student = getprocess(sql, (idno,))
    return student[0] if student else None

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
