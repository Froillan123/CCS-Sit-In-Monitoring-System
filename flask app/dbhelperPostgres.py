import psycopg2
import psycopg2.extras
from psycopg2 import Error

database_config = {
    'host': 'dpg-cuinej3qf0us73drhcq0-a',
    'user': 'root',
    'password': 'Q1mVmkv85tQ70kSjZoYmYyxAqudsdZvN',
    'dbname': 'student_8ri4',
}

def connect_to_db():
    """Establish connection to the PostgreSQL database"""
    try:
        connection = psycopg2.connect(**database_config)
        return connection
    except Error as e:
        print(f"Error: {e}")
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

def get_admin_user_by_credentials(username: str, password: str) -> dict:
    sql = 'SELECT * FROM admin_users WHERE username = %s AND password = %s'
    admin_user = getprocess(sql, (username, password))
    return admin_user[0] if admin_user else None

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

def create_tables_if_not_exists():
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        idno INTEGER NOT NULL UNIQUE,
        lastname VARCHAR(255),
        firstname VARCHAR(255),
        midname VARCHAR(255),
        course VARCHAR(255),
        year_level INTEGER,
        email VARCHAR(255) UNIQUE,
        username VARCHAR(255) UNIQUE,
        password VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS admin_users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE,
        name TEXT
    );
    """
    return postprocess(create_tables_sql)

# Call create_tables_if_not_exists to ensure tables are created if they don't exist
create_tables_if_not_exists()
