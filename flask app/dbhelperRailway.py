import psycopg2
import psycopg2.extras
from psycopg2 import Error
import uuid
from datetime import datetime

database_config = {
    "dbname": "railway",
    "user": "postgres",
    "password": "aBAIAwTmOYJaznnGExaUNWqEMPXaefSI",
    "host": "roundhouse.proxy.rlwy.net",
    "port": "40173"
}

def connect_to_db():
    """Establish connection to the PostgreSQL database"""
    try:
        connection = psycopg2.connect(**database_config)
        return connection
    except Error as e:
        return None
    
def postprocess(sql: str, params=()) -> bool:
    connection = connect_to_db()
    if not connection:
        return False
    
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def getprocess(sql: str, params=()) -> list:
    connection = connect_to_db()
    if not connection:
        return []
    
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)  # Fetch results as dictionaries
    try:
        cursor.execute(sql, params)
        data = cursor.fetchall()
        return data
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def getall_records(table: str) -> list:
    sql = f'SELECT * FROM "{table}"'
    return getprocess(sql)

def get_student_by_id(idno: str) -> dict:
    sql = 'SELECT * FROM students WHERE idno = %s'
    student = getprocess(sql, (idno,))
    return student[0] if student else None

def get_student_by_email(email: str) -> dict:
    sql = 'SELECT * FROM students WHERE email = %s'
    student = getprocess(sql, (email,))
    return student[0] if student else None

def get_user_by_credentials(username: str, password: str) -> dict:
    sql = 'SELECT * FROM students WHERE username = %s AND password = %s'
    user = getprocess(sql, (username, password))
    return user[0] if user else None

def get_student_by_username(username: str) -> dict:
    sql = 'SELECT * FROM students WHERE username = %s'
    student = getprocess(sql, (username,))
    return student[0] if student else None

def get_count_students() -> int:
    sql = 'SELECT COUNT(*) FROM students'
    results = getprocess(sql)
    return results[0]['count'] if results else 0

def get_fname_student(firstname: str) -> list:
    sql = 'SELECT * FROM students WHERE firstname = %s'
    students = getprocess(sql, (firstname,))
    return students  # Now returns a list of students

def get_admin_user_by_credentials(admin_username: str, password: str) -> dict:
    sql = 'SELECT * FROM admin_users WHERE admin_username = %s AND password = %s'
    admin_user = getprocess(sql,(admin_username,password))
    return admin_user[0] if admin_user else None

def get_admin_by_username(admin_username: str) -> dict:
    sql = 'SELECT * FROM admin_users WHERE admin_username = %s'
    student = getprocess(sql, (admin_username,))
    return student[0] if student else None



def generate_session_token():
    """Generate a unique session token."""
    return str(uuid.uuid4())

def login_user(student_id, lastname, firstname):
    """Handles user login, generates a session token, and stores login time with student name."""
    connection = connect_to_db()
    if not connection:
        return None

    token = generate_session_token()
    login_time = datetime.now()
    student_name = f"{lastname} {firstname}"  # Concatenate lastname + firstname

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO student_sessions (student_id, session_token, login_time, student_name) 
                VALUES (%s, %s, %s, %s)
                """,
                (student_id, token, login_time, student_name)
            )
            connection.commit()
        return token
    except Exception as e:
        print(f"Error during login: {e}")
        return None
    finally:
        connection.close()

def logout_user(student_id, token):
    """Handles user logout and updates the session timeout time."""
    connection = connect_to_db()
    if not connection:
        return False

    timeout = datetime.now()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE student_sessions SET timeout = %s WHERE student_id = %s AND session_token = %s AND timeout IS NULL",
                (timeout, student_id, token)
            )
            connection.commit()
        return True
    except Exception as e:
        print(f"Error during logout: {e}")
        return False
    finally:
        connection.close()


def save_session(student_id, token, lastname, firstname):
    """Save login session to student_sessions table."""
    connection = connect_to_db()
    if not connection:
        return False

    login_time = datetime.now()
    student_name = f"{lastname} {firstname}"  # Concatenate lastname + firstname

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO student_sessions (student_id, session_token, login_time, timeout, student_name) VALUES (%s, %s, %s, NULL, %s)",
                (student_id, token, login_time, student_name)
            )
            connection.commit()
        return True
    except Exception as e:
        print(f"Error saving session: {e}")
        return False
    finally:
        connection.close()



def add_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    fields = '"{}"'.format('", "'.join(keys))
    placeholders = ", ".join(["%s"] * len(values))  # Use %s for PostgreSQL placeholders
    sql = f"INSERT INTO \"{table}\" ({fields}) VALUES ({placeholders})"
    return postprocess(sql, values)

def update_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    set_clause = ", ".join([f"\"{key}\" = %s" for key in keys[1:]])  # %s for PostgreSQL placeholders
    sql = f"UPDATE \"{table}\" SET {set_clause} WHERE \"{keys[0]}\" = %s"
    return postprocess(sql, values[1:] + [values[0]])

def delete_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    sql = f"DELETE FROM \"{table}\" WHERE \"{keys[0]}\" = %s"
    return postprocess(sql, (values[0],))


