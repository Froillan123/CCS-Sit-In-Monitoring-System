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

def get_user_by_credentials(username: str, password: str) -> dict:
    sql = 'SELECT * FROM students WHERE username = ? AND password = ?'
    user = getprocess(sql, (username, password))
    return user[0] if user else None

# Function to add a new record to a table
def add_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    fields = "`, `".join(keys)
    placeholders = ", ".join("?" * len(values))
    sql = f"INSERT INTO `{table}` (`{fields}`) VALUES ({placeholders})"
    return postprocess(sql, values)

# Function to update an existing record in a table
def update_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    set_clause = ", ".join([f"`{key}` = ?" for key in keys[1:]])  # Exclude the first key (idno)
    sql = f"UPDATE `{table}` SET {set_clause} WHERE `{keys[0]}` = ?"
    result = postprocess(sql, values[1:] + [values[0]])  # Pass values excluding the idno in the set clause

    if result and table == "students":  # Update the attendance table too
        update_attendance(kwargs)
    
    return result

# Function to delete a record from a table
def delete_record(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    sql = f"DELETE FROM `{table}` WHERE `{keys[0]}` = ?"
    return postprocess(sql, (values[0],))






