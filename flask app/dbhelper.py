from sqlite3 import connect, Row
from datetime import datetime, timedelta
import sqlite3
import time
import threading
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
    SELECT r.id, r.student_name, r.purpose, l.lab_name, r.reservation_date, r.status
    FROM reservations r
    JOIN laboratories l ON r.lab_id = l.id
    WHERE r.student_idno = ?
    """
    cursor.execute(query, (student_id,))
    reservations = cursor.fetchall()

    conn.close()
    return reservations

def delete_reservation(reservation_id):
    sql = "DELETE FROM reservations WHERE id = ?"
    return postprocess(sql, (reservation_id,))

def delete_old_reservations():
    while True:
        # Fetch reservations older than 2 hours
        sql = """
        DELETE FROM reservations
        WHERE status = 'Pending' AND login_time < ?
        """
        two_hours_ago = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        postprocess(sql, (two_hours_ago,))
        
        # Sleep for 1 hour before checking again
        time.sleep(3600)


def has_pending_reservation(student_idno: str) -> bool:
    sql = """
        SELECT id FROM reservations 
        WHERE student_idno = ? AND status = 'Pending'
    """
    result = getprocess(sql, (student_idno,))
    return len(result) > 0  # Returns True if there is at least one pending reservation

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

def update_student_sessions(student_idno, sessions_left):
    """Update a student's remaining sessions"""
    sql = "UPDATE students SET sessions_left = ? WHERE idno = ?"
    return postprocess(sql, (sessions_left, student_idno))


def insert_session_history(student_idno, login_time, logout_time, duration=None):
    """Insert a record into session history with optional duration"""
    print(f"DEBUG: Inserting session history for student {student_idno}")
    
    # If duration not provided, calculate it
    if duration is None and login_time and logout_time:
        try:
            login = datetime.strptime(login_time, '%Y-%m-%d %H:%M:%S')
            logout = datetime.strptime(logout_time, '%Y-%m-%d %H:%M:%S')
            duration = str(logout - login)
        except ValueError as e:
            print(f"Duration calculation error: {e}")
            duration = None

    sql = """
    INSERT INTO session_history 
    (student_idno, login_time, logout_time, duration)
    VALUES (?, ?, ?, ?)
    """
    params = (student_idno, login_time, logout_time, duration)

    print(f"Executing SQL: {sql} with params: {params}")
    result = postprocess(sql, params)
    print(f"Insert result: {result}")
    return result


def increment_daily_sitin(student_idno):
    # Get student's program
    student = get_student_by_idno(student_idno)
    if not student:
        raise ValueError("Student not found")
    
    program = student['course']
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Try to update existing record
    updated = postprocess(
        "UPDATE daily_sitins SET count = count + 1 WHERE program = ? AND sitin_date = ?",
        (program, today)
    )
    
    # If no record exists, insert a new one
    if not updated or updated.rowcount == 0:
        postprocess(
            "INSERT INTO daily_sitins (program, sitin_date, count) VALUES (?, ?, 1)",
            (program, today)
        )



def get_todays_sitin_counts():
    today = datetime.now().strftime('%Y-%m-%d')
    results = getprocess("""
        SELECT p.program_code, p.program_name, COALESCE(d.count, 0) as count
        FROM programs p
        LEFT JOIN daily_sitins d ON p.program_code = d.program AND d.sitin_date = ?
        ORDER BY p.program_code
    """, (today,))
    
    return {row['program_code']: row['count'] for row in results}

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



def get_reservation_by_id(reservation_id):
    sql = """
    SELECT reservations.*, laboratories.lab_name AS lab_name
    FROM reservations
    JOIN laboratories ON reservations.lab_id = laboratories.id
    WHERE reservations.id = ?
    """
    result = getprocess(sql, (reservation_id,))
    if result:
        return result[0]  # Ensure this includes 'lab_name'
    return None


def update_reservation_status(reservation_id, status):
    sql = "UPDATE reservations SET status = ? WHERE id = ?"
    return postprocess(sql, (status, reservation_id))

def update_reservation_logout(reservation_id, logout_time):
    try:
        sql = """
        UPDATE reservations
        SET logout_time = ?
        WHERE id = ?
        """
        return postprocess(sql, (logout_time, reservation_id))
    except Exception as e:
        print(f"Error updating reservation logout time: {e}")
        return False


def update_student_sessions(student_idno, sessions_left):
    sql = "UPDATE students SET sessions_left = ? WHERE idno = ?"
    return postprocess(sql, (sessions_left, student_idno))

def create_reservation(student_idno: str, student_name: str, lab_id: str, 
                      purpose: str, reservation_date: str, login_time: str, 
                      status: str = "Pending") -> bool:
    sql = """
        INSERT INTO reservations 
        (student_idno, student_name, lab_id, purpose, reservation_date, login_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    return postprocess(sql, (student_idno, student_name, lab_id, purpose, reservation_date, login_time, status))



def get_student_session_history(student_idno: str, limit: int = 30) -> list:
    sql = """
        SELECT 
            id,
            student_idno,
            login_time,
            logout_time,
            duration,
            strftime('%H:%M:%S', datetime(duration, 'unixepoch')) as formatted_duration
        FROM session_history
        WHERE student_idno = ?
        ORDER BY login_time DESC
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

def update_reservation_session(reservation_id, session_number):
    """Update a reservation with session number"""
    sql = "UPDATE reservations SET session_number = ? WHERE id = ?"
    return postprocess(sql, (session_number, reservation_id))

def update_reservation_logout(reservation_id, logout_time):
    """Update a reservation with logout time and status"""
    sql = "UPDATE reservations SET logout_time = ?, status = 'Logged Out' WHERE id = ?"
    return postprocess(sql, (logout_time, reservation_id))

# Function to create the student points tables if they don't exist
def create_points_tables():
    db = connect(database)
    cursor = db.cursor()
    try:
        # Create student_points table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_idno TEXT NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_idno) REFERENCES students(idno) ON DELETE CASCADE
        )
        ''')
        
        # Create points_history table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_idno TEXT NOT NULL,
            points_change INTEGER NOT NULL,
            reason TEXT NOT NULL,
            awarded_by TEXT NOT NULL,
            awarded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_idno) REFERENCES students(idno) ON DELETE CASCADE
        )
        ''')
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating points tables: {e}")
        return False
    finally:
        cursor.close()
        db.close()

# dbhelper.py
def add_points_to_student(student_idno, points, reason, awarded_by):
    # First, check if student has a points record
    current_points = getprocess(
        "SELECT points FROM student_points WHERE student_idno = ?", 
        (student_idno,)
    )
    
    if not current_points:
        # Create new record
        postprocess(
            "INSERT INTO student_points (student_idno, points) VALUES (?, ?)",
            (student_idno, points)
        )
        new_points = points
    else:
        # Update existing record
        new_points = current_points[0]['points'] + points
        postprocess(
            "UPDATE student_points SET points = ?, last_updated = CURRENT_TIMESTAMP WHERE student_idno = ?",
            (new_points, student_idno)
        )
    
    # Add to points history
    postprocess(
        """INSERT INTO points_history 
        (student_idno, points_change, reason, awarded_by) 
        VALUES (?, ?, ?, ?)""",
        (student_idno, points, reason, awarded_by)
    )
    
    # Check if points reached a multiple of 3 and auto-convert
    sessions_added = new_points // 3
    if sessions_added > 0:
        # Add sessions to student
        postprocess(
            "UPDATE students SET sessions_left = sessions_left + ? WHERE idno = ?",
            (sessions_added, student_idno)
        )
        
        # Add conversion record to history
        postprocess(
            """INSERT INTO points_history 
            (student_idno, points_change, reason, awarded_by) 
            VALUES (?, ?, ?, ?)""",
            (student_idno, -(sessions_added * 3), "Auto-converted to sessions", "system")
        )
    
    return new_points

def convert_points_to_sessions(student_idno):
    # Get current points
    current_points_result = getprocess(
        "SELECT points FROM student_points WHERE student_idno = ?", 
        (student_idno,)
    )
    
    if not current_points_result:
        return 0, 0
    
    current_points = current_points_result[0]['points']
    sessions_to_add = current_points // 3
    
    if sessions_to_add > 0:
        # Add sessions to student
        postprocess(
            "UPDATE students SET sessions_left = sessions_left + ? WHERE idno = ?",
            (sessions_to_add, student_idno)
        )
        
        # Add to history
        postprocess(
            """INSERT INTO points_history 
            (student_idno, points_change, reason, awarded_by) 
            VALUES (?, ?, ?, ?)""",
            (student_idno, -(sessions_to_add * 3), "Manual conversion to sessions", "user")
        )
        
        return sessions_to_add, current_points
    
    return 0, current_points

# Function to get student points leaderboard
def get_points_leaderboard(limit=10):
    sql = """
    SELECT 
        s.idno as student_idno,
        s.firstname || ' ' || s.lastname as student_name,
        s.course,
        s.year_level,
        COALESCE(sp.points, 0) as total_points
    FROM students s
    LEFT JOIN student_points sp ON s.idno = sp.student_idno
    ORDER BY total_points DESC, s.lastname, s.firstname
    LIMIT ?
    """
    leaderboard = getprocess(sql, (limit,))
    
    # Add sit-in counts for each student in the leaderboard
    for student in leaderboard:
        student['sitin_count'] = get_student_sitin_count(student['student_idno'])
    
    return leaderboard

# Function to check if a student has been awarded points for a reservation
def has_points_for_reservation(student_idno, reservation_id):
    sql = """
    SELECT 1 FROM reservations 
    WHERE id = ? AND student_idno = ? AND points_awarded = 1
    """
    result = getprocess(sql, (reservation_id, student_idno))
    return len(result) > 0

# Function to count the number of sit-ins a student has completed
def get_student_sitin_count(student_idno):
    sql = """
    SELECT COUNT(*) as sitin_count
    FROM reservations 
    WHERE student_idno = ? AND status = 'Logged Out'
    """
    result = getprocess(sql, (student_idno,))
    return result[0]['sitin_count'] if result else 0