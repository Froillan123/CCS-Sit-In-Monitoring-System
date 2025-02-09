#dbhelper.py
from sqlite3 import connect, Row

database: str = 'student.db'

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

def getprocess(sql: str, params=()) -> list:
    db = connect(database)
    cursor = db.cursor()
    cursor.row_factory = Row
    try:
        cursor.execute(sql, params)
        data = cursor.fetchall()
        return data
    finally:
        cursor.close()
        db.close()

def getall_records(table: str) -> list:
    sql = f'SELECT * FROM `{table}`'
    return getprocess(sql)



def get_student_by_id(idno: str) -> dict:
    sql = 'SELECT * FROM students WHERE idno = ?'
    student = getprocess(sql, (idno,))
    return student[0] if student else None

def get_student_by_email(email: str) -> dict:
    sql = 'SELECT * FROM students WHERE email = ?'
    student = getprocess(sql, (email,))
    return student[0] if student else None

def get_user_by_credentials(username: str, password: str) -> dict:
    sql = 'SELECT * FROM students WHERE username = ? AND password = ?'
    user = getprocess(sql, (username, password))
    return user[0] if user else None

def get_count_students() -> int:
    sql = 'SELECT COUNT(*) FROM students'
    
    results = getprocess(sql)
    
    return results[0][0] if results else 0

def get_student_by_username(username: str) -> dict:
    sql = 'SELECT * FROM students WHERE username = ?'
    student = getprocess(sql, (username,))
    return student[0] if student else None

def get_fname_student(firstname: str) -> list:
    sql = 'SELECT * FROM students WHERE firstname = ?'
    students = getprocess(sql, (firstname,))
    return students 

def get_admin_user_by_credentials(username: str, password: str) -> dict:
    sql = 'SELECT * FROM admin_users WHERE username = ? AND password = ?'
    admin_user = getprocess(sql,(username,password))
    return admin_user[0] if admin_user else None

def get_admin_by_username(username: str) -> dict:
    sql = 'SELECT * FROM admin_users WHERE username = ?'
    student = getprocess(sql, (username,))
    return student[0] if student else None

def add_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    fields = "`, `".join(keys)
    placeholders = ", ".join("?" * len(values))
    sql = f"INSERT INTO `{table}` (`{fields}`) VALUES ({placeholders})"
    return postprocess(sql, values)

def update_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    set_clause = ", ".join([f"`{key}` = ?" for key in keys[1:]]) 
    sql = f"UPDATE `{table}` SET {set_clause} WHERE `{keys[0]}` = ?"
    result = postprocess(sql, values[1:] + [values[0]]) 
    return result

# Function to delete a record from a table
def delete_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    sql = f"DELETE FROM `{table}` WHERE `{keys[0]}` = ?"
    return postprocess(sql, (values[0],))






