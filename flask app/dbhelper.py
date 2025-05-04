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
    
    # Check if points reached a multiple of 3 and convert ONLY the multiple of 3
    sessions_to_add = new_points // 3
    old_sessions_to_add = 0
    
    if current_points:
        old_points = current_points[0]['points']
        old_sessions_to_add = old_points // 3
    
    # Only add the NEW sessions converted (not all of them)
    additional_sessions = sessions_to_add - old_sessions_to_add
    
    if additional_sessions > 0:
        # Calculate remaining points - we keep these, not reset them
        remaining_points = new_points % 3
        
        # Add only the new sessions to student
        postprocess(
            "UPDATE students SET sessions_left = sessions_left + ? WHERE idno = ?",
            (additional_sessions, student_idno)
        )
        
        # Add conversion record to history
        postprocess(
            """INSERT INTO points_history 
            (student_idno, points_change, reason, awarded_by) 
            VALUES (?, ?, ?, ?)""",
            (student_idno, -(additional_sessions * 3), f"Converted {additional_sessions * 3} points to {additional_sessions} sessions", "system")
        )
        
        # Get updated sessions
        updated_sessions = getprocess(
            "SELECT sessions_left FROM students WHERE idno = ?", 
            (student_idno,)
        )[0]['sessions_left']
        
        # Return the new points, additional sessions, and total sessions
        return {
            "new_points": new_points, 
            "additional_sessions": additional_sessions,
            "remaining_points": remaining_points,
            "total_sessions": updated_sessions
        }
    
    # If no conversion happened, return the new total points
    return {
        "new_points": new_points, 
        "additional_sessions": 0,
        "remaining_points": new_points % 3,
        "total_sessions": getprocess("SELECT sessions_left FROM students WHERE idno = ?", (student_idno,))[0]['sessions_left']
    }

def convert_points_to_sessions(student_idno):
    # Get current points
    current_points_result = getprocess(
        "SELECT points FROM student_points WHERE student_idno = ?", 
        (student_idno,)
    )
    
    if not current_points_result:
        return {"sessions_added": 0, "remaining_points": 0, "total_sessions": 0}
    
    current_points = current_points_result[0]['points']
    sessions_to_add = current_points // 3
    
    if sessions_to_add > 0:
        # Calculate remaining points - which we keep
        remaining_points = current_points % 3
        
        # Add sessions to student
        postprocess(
            "UPDATE students SET sessions_left = sessions_left + ? WHERE idno = ?",
            (sessions_to_add, student_idno)
        )
        
        # Update points to remaining after conversion, but don't reset completely
        postprocess(
            "UPDATE student_points SET points = ?, last_updated = CURRENT_TIMESTAMP WHERE student_idno = ?",
            (remaining_points, student_idno)
        )
        
        # Add to history
        postprocess(
            """INSERT INTO points_history 
            (student_idno, points_change, reason, awarded_by) 
            VALUES (?, ?, ?, ?)""",
            (student_idno, -(sessions_to_add * 3), f"Manual conversion: {sessions_to_add * 3} points to {sessions_to_add} sessions", "user")
        )
        
        # Get updated sessions
        updated_sessions = getprocess(
            "SELECT sessions_left FROM students WHERE idno = ?", 
            (student_idno,)
        )[0]['sessions_left']
        
        return {
            "sessions_added": sessions_to_add, 
            "remaining_points": remaining_points,
            "total_sessions": updated_sessions
        }
    
    # Get updated sessions
    updated_sessions = getprocess(
        "SELECT sessions_left FROM students WHERE idno = ?", 
        (student_idno,)
    )[0]['sessions_left']
    
    return {
        "sessions_added": 0, 
        "remaining_points": current_points,
        "total_sessions": updated_sessions
    }

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
    
# Create lab computers table if it doesn't exist
def create_lab_computers_table():
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_computers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER NOT NULL,
            computer_number INTEGER NOT NULL,
            status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'In Use', 'Unavailable')),
            student_idno TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lab_id) REFERENCES laboratories(id),
            FOREIGN KEY (student_idno) REFERENCES students(idno)
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')),
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            subject_code TEXT,
            subject_name TEXT,
            status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'Reserved', 'Unavailable')),
            reason TEXT,
            FOREIGN KEY (lab_id) REFERENCES laboratories(id)
        )''')
        
        conn.commit()
        print("Lab computers and schedules tables created or already exist")
    except Exception as e:
        print(f"Error creating lab computers and schedules tables: {e}")
    finally:
        if conn:
            conn.close()

# Create student_reservation table if it doesn't exist
def create_student_reservation_table():
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_idno TEXT NOT NULL,
            lab_id INTEGER NOT NULL,
            computer_id INTEGER,
            purpose TEXT NOT NULL,
            reservation_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            feedback_submitted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_idno) REFERENCES students(idno),
            FOREIGN KEY (lab_id) REFERENCES laboratories(id),
            FOREIGN KEY (computer_id) REFERENCES lab_computers(id)
        )''')
        
        conn.commit()
        print("Student reservation table created or already exists")
    except Exception as e:
        print(f"Error creating student reservation table: {e}")
    finally:
        if conn:
            conn.close()

# Function to create a new student reservation
def create_student_reservation(student_idno, lab_id, computer_id, purpose, reservation_date, time_slot):
    sql = """
        INSERT INTO student_reservation 
        (student_idno, lab_id, computer_id, purpose, reservation_date, time_slot, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    """
    return postprocess(sql, (student_idno, lab_id, computer_id, purpose, reservation_date, time_slot))

# Function to get student reservations by student ID
def get_student_reservations(student_idno):
    sql = """
        SELECT sr.*, l.lab_name, lc.computer_number
        FROM student_reservation sr
        JOIN laboratories l ON sr.lab_id = l.id
        LEFT JOIN lab_computers lc ON sr.computer_id = lc.id
        WHERE sr.student_idno = ?
        ORDER BY sr.created_at DESC
    """
    return getprocess(sql, (student_idno,))

# Function to check if a student has a pending reservation
def has_pending_student_reservation(student_idno):
    sql = """
        SELECT COUNT(*) as count
        FROM student_reservation
        WHERE student_idno = ? AND status = 'Pending'
    """
    result = getprocess(sql, (student_idno,))
    return result[0]['count'] > 0 if result else False

# Function to get available time slots for a lab on a specific date
def get_available_time_slots(lab_id, reservation_date):
    # Convert reservation_date to day of week
    try:
        date_obj = datetime.strptime(reservation_date, '%Y-%m-%d')
        day_of_week = date_obj.strftime('%A')
    except ValueError:
        return []
    
    # Get all schedules for this lab on the specified day
    sql = """
        SELECT start_time, end_time, status
        FROM lab_schedules
        WHERE lab_id = ? AND day_of_week = ?
        ORDER BY start_time
    """
    schedules = getprocess(sql, (lab_id, day_of_week))
    
    # Return all time slots with their status
    time_slots = []
    for schedule in schedules:
        time_slots.append({
            'start_time': schedule['start_time'],
            'end_time': schedule['end_time'],
            'time_slot': f"{schedule['start_time']} - {schedule['end_time']}",
            'status': schedule['status']
        })
    
    return time_slots

# Function to get available computers for a lab
def get_available_computers(lab_id):
    sql = """
        SELECT id, computer_number, status
        FROM lab_computers
        WHERE lab_id = ? AND status = 'Available'
        ORDER BY computer_number
    """
    return getprocess(sql, (lab_id,))

# Function to update student reservation status
def update_student_reservation_status(reservation_id, status):
    sql = """
        UPDATE student_reservation
        SET status = ?
        WHERE id = ?
    """
    return postprocess(sql, (status, reservation_id))

# Initialize all tables when module is loaded
def initialize_tables():
    create_lab_computers_table()
    create_student_reservation_table()
    create_points_tables()
    create_reservation_notifications_table()

# Initialize lab computers for a lab
def initialize_lab_computers(lab_id, computer_count=50):
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Check if computers already exist for this lab
        cursor.execute('SELECT COUNT(*) FROM lab_computers WHERE lab_id = ?', (lab_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            for i in range(1, computer_count + 1):
                cursor.execute('''
                INSERT INTO lab_computers (lab_id, computer_number, status)
                VALUES (?, ?, 'Available')
                ''', (lab_id, i))
            
            conn.commit()
            print(f"Initialized {computer_count} computers for lab {lab_id}")
            return True
        else:
            print(f"Computers already exist for lab {lab_id}")
            return False
    except Exception as e:
        print(f"Error initializing lab computers: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Get computers for a specific lab
def get_lab_computers(lab_id):
    try:
        conn = sqlite3.connect('student.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT lc.*, s.firstname, s.lastname
        FROM lab_computers lc
        LEFT JOIN students s ON lc.student_idno = s.idno
        WHERE lc.lab_id = ?
        ORDER BY lc.computer_number
        ''', (lab_id,))
        
        computers = cursor.fetchall()
        return [dict(computer) for computer in computers]
    except Exception as e:
        print(f"Error getting lab computers: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Update computer status
def update_computer_status(computer_id, status, student_idno=None):
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        if status == 'In Use' and student_idno:
            cursor.execute('''
            UPDATE lab_computers 
            SET status = ?, student_idno = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (status, student_idno, computer_id))
        else:
            cursor.execute('''
            UPDATE lab_computers 
            SET status = ?, student_idno = NULL, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (status, computer_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating computer status: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Add or update lab schedule
def add_or_update_lab_schedule(lab_id, day_of_week, start_time, end_time, status, subject_code=None, subject_name=None, reason=None, schedule_id=None):
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        if schedule_id:
            # Update existing schedule
            cursor.execute('''
            UPDATE lab_schedules
            SET day_of_week = ?, start_time = ?, end_time = ?, subject_code = ?,
                subject_name = ?, status = ?, reason = ?
            WHERE id = ?
            ''', (day_of_week, start_time, end_time, subject_code, subject_name, status, reason, schedule_id))
        else:
            # Create new schedule
            cursor.execute('''
            INSERT INTO lab_schedules
            (lab_id, day_of_week, start_time, end_time, subject_code, subject_name, status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (lab_id, day_of_week, start_time, end_time, subject_code, subject_name, status, reason))
            
            schedule_id = cursor.lastrowid
        
        conn.commit()
        return schedule_id
    except Exception as e:
        print(f"Error adding/updating lab schedule: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Get lab schedules
def get_lab_schedules(lab_id=None, day_of_week=None):
    try:
        conn = sqlite3.connect('student.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Debug information
        if lab_id:
            print(f"DEBUG: Fetching schedules for lab ID {lab_id}")
            # Print lab info
            cursor.execute('SELECT * FROM laboratories WHERE id = ?', (lab_id,))
            lab_info = cursor.fetchone()
            if lab_info:
                print(f"DEBUG: Lab found: {dict(lab_info)}")
            else:
                print(f"DEBUG: No lab found with ID {lab_id}")
        
        query = '''
        SELECT ls.*, l.lab_name
        FROM lab_schedules ls
        JOIN laboratories l ON ls.lab_id = l.id
        WHERE 1=1
        '''
        
        params = []
        
        if lab_id:
            query += ' AND ls.lab_id = ?'
            params.append(lab_id)
            
        if day_of_week:
            query += ' AND ls.day_of_week = ?'
            params.append(day_of_week)
            
        query += ' ORDER BY ls.day_of_week, ls.start_time'
        
        print(f"DEBUG: Query: {query}")
        print(f"DEBUG: Params: {params}")
        
        cursor.execute(query, params)
        schedules = cursor.fetchall()
        
        result = [dict(schedule) for schedule in schedules]
        print(f"DEBUG: Found {len(result)} schedules")
        
        # If no schedules found, check for what might be the issue
        if not result and lab_id:
            cursor.execute('SELECT COUNT(*) FROM lab_schedules WHERE lab_id = ?', (lab_id,))
            count = cursor.fetchone()[0]
            print(f"DEBUG: Total schedules for lab ID {lab_id}: {count}")
            
            # Check for any schedules to make sure the table has data
            cursor.execute('SELECT COUNT(*), MIN(lab_id), MAX(lab_id) FROM lab_schedules')
            total_info = cursor.fetchone()
            if total_info:
                print(f"DEBUG: Total schedules in DB: {total_info[0]}, Min lab_id: {total_info[1]}, Max lab_id: {total_info[2]}")
            
            # List all lab IDs in the schedule table
            cursor.execute('SELECT DISTINCT lab_id, COUNT(*) FROM lab_schedules GROUP BY lab_id')
            lab_ids = cursor.fetchall()
            print(f"DEBUG: Distinct lab_ids in schedules: {[dict(row) for row in lab_ids]}")
            
        return result
    except Exception as e:
        print(f"Error getting lab schedules: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Delete lab schedule
def delete_lab_schedule(schedule_id):
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM lab_schedules WHERE id = ?', (schedule_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting lab schedule: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Import lab schedules from predefined data
def import_default_lab_schedules(lab_mappings=None):
    try:
        print("DEBUG: Starting import_default_lab_schedules")
        if lab_mappings is None:
            lab_mappings = {}
        print(f"DEBUG: Using lab ID mappings: {lab_mappings}")
        
        conn = sqlite3.connect('student.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First ensure all required lab IDs exist
        required_lab_ids = set()
        
        # Define the schedule data structure 
        # Format: (lab_id, day, start_time, end_time, subject_code, subject_name, status)
        default_schedules = [
            # Lab 544 - Monday
            (544, 'Monday', '07:00', '08:30', 'ITP10123', 'Computer Programming 1', 'Reserved'),
            (544, 'Monday', '08:30', '10:00', None, None, 'Available'),
            (544, 'Monday', '10:00', '11:30', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            (544, 'Monday', '11:30', '13:00', None, None, 'Available'),
            (544, 'Monday', '13:00', '14:30', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            (544, 'Monday', '14:30', '16:00', None, None, 'Available'),
            (544, 'Monday', '16:00', '17:30', 'DBMS20267', 'Database Management Systems', 'Reserved'),
            (544, 'Monday', '17:30', '19:00', None, None, 'Available'),
            (544, 'Monday', '19:00', '21:00', 'ITE20245', 'IT Elective 1 (Mobile Dev)', 'Reserved'),
            
            # Lab 544 - Tuesday
            (544, 'Tuesday', '07:00', '08:30', 'ITP10123', 'Computer Programming 1', 'Reserved'),
            (544, 'Tuesday', '08:30', '10:00', None, None, 'Available'),
            (544, 'Tuesday', '10:00', '11:30', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            (544, 'Tuesday', '11:30', '13:00', None, None, 'Available'),
            (544, 'Tuesday', '13:00', '14:30', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            (544, 'Tuesday', '14:30', '16:00', None, None, 'Available'),
            (544, 'Tuesday', '16:00', '17:30', 'DBMS20267', 'Database Management Systems', 'Reserved'),
            (544, 'Tuesday', '17:30', '19:00', None, None, 'Available'),
            (544, 'Tuesday', '19:00', '21:00', 'ITE20245', 'IT Elective 1 (Mobile Dev)', 'Reserved'),
            
            # Lab 544 - Wednesday
            (544, 'Wednesday', '07:00', '08:30', 'ITP10123', 'Computer Programming 1', 'Reserved'),
            (544, 'Wednesday', '08:30', '10:00', None, None, 'Available'),
            (544, 'Wednesday', '10:00', '11:30', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            (544, 'Wednesday', '11:30', '13:00', None, None, 'Available'),
            (544, 'Wednesday', '13:00', '14:30', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            (544, 'Wednesday', '14:30', '16:00', None, None, 'Available'),
            (544, 'Wednesday', '16:00', '17:30', 'DBMS20267', 'Database Management Systems', 'Reserved'),
            (544, 'Wednesday', '17:30', '19:00', None, None, 'Available'),
            (544, 'Wednesday', '19:00', '21:00', 'ITE20245', 'IT Elective 1 (Mobile Dev)', 'Reserved'),
            
            # Add schedules for Thursday, Friday and Saturday for lab 544
            (544, 'Thursday', '07:00', '08:30', 'ITP10123', 'Computer Programming 1', 'Reserved'),
            (544, 'Thursday', '08:30', '10:00', None, None, 'Available'),
            (544, 'Thursday', '10:00', '11:30', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            
            (544, 'Friday', '07:00', '08:30', 'ITP10123', 'Computer Programming 1', 'Reserved'),
            (544, 'Friday', '08:30', '10:00', None, None, 'Available'),
            (544, 'Friday', '10:00', '11:30', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            
            (544, 'Saturday', '07:00', '08:30', None, None, 'Available'),
            (544, 'Saturday', '08:30', '10:00', None, None, 'Available'),
            
            # Lab 542 - Monday to Saturday
            (542, 'Monday', '07:00', '08:30', None, None, 'Available'),
            (542, 'Monday', '08:30', '10:00', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            (542, 'Monday', '10:00', '11:30', None, None, 'Available'),
            (542, 'Monday', '11:30', '13:00', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            
            (542, 'Tuesday', '07:00', '08:30', None, None, 'Available'),
            (542, 'Tuesday', '08:30', '10:00', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            
            (542, 'Wednesday', '07:00', '08:30', None, None, 'Available'),
            (542, 'Wednesday', '08:30', '10:00', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            
            (542, 'Thursday', '07:00', '08:30', None, None, 'Available'),
            (542, 'Thursday', '08:30', '10:00', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            
            (542, 'Friday', '07:00', '08:30', None, None, 'Available'),
            (542, 'Friday', '08:30', '10:00', 'OOP20239', 'Computer Programming 2 (Java)', 'Reserved'),
            
            (542, 'Saturday', '07:00', '08:30', None, None, 'Available'),
            (542, 'Saturday', '08:30', '10:00', None, None, 'Available'),
            
            # Lab 524 - Monday to Saturday
            (524, 'Monday', '07:00', '08:30', None, None, 'Available'),
            (524, 'Monday', '08:30', '10:00', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            (524, 'Monday', '10:00', '11:30', None, None, 'Available'),
            (524, 'Monday', '11:30', '13:00', 'DBMS20267', 'Database Management Systems', 'Reserved'),
            
            (524, 'Tuesday', '07:00', '08:30', None, None, 'Available'),
            (524, 'Tuesday', '08:30', '10:00', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            
            (524, 'Wednesday', '07:00', '08:30', None, None, 'Available'),
            (524, 'Wednesday', '08:30', '10:00', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            
            (524, 'Thursday', '07:00', '08:30', None, None, 'Available'),
            (524, 'Thursday', '08:30', '10:00', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            
            (524, 'Friday', '07:00', '08:30', None, None, 'Available'),
            (524, 'Friday', '08:30', '10:00', 'DSA20145', 'Data Structures and Algorithms', 'Reserved'),
            
            (524, 'Saturday', '07:00', '08:30', None, None, 'Available'),
            (524, 'Saturday', '08:30', '10:00', None, None, 'Available'),
        ]
        
        # Apply lab ID mappings to the schedules
        mapped_schedules = []
        for schedule in default_schedules:
            original_lab_id = schedule[0]
            # If there's a mapping for this lab ID, use it, otherwise keep the original
            actual_lab_id = lab_mappings.get(original_lab_id, original_lab_id)
            
            # Create a new schedule tuple with the updated lab ID
            new_schedule = (actual_lab_id,) + schedule[1:]
            mapped_schedules.append(new_schedule)
        
        # Extract unique lab IDs from the schedules
        for schedule in mapped_schedules:
            required_lab_ids.add(schedule[0])
        
        print(f"DEBUG: Importing {len(mapped_schedules)} default schedules for labs: {required_lab_ids}")
        
        # Insert schedules in batches for better performance
        cursor.executemany('''
        INSERT INTO lab_schedules 
        (lab_id, day_of_week, start_time, end_time, subject_code, subject_name, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', mapped_schedules)
        
        conn.commit()
        print("DEBUG: Default lab schedules imported successfully")
        return True
    except Exception as e:
        import traceback
        print(f"DEBUG: Error importing default lab schedules: {str(e)}")
        print(traceback.format_exc())
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

# Call these functions when the app starts
create_lab_computers_table()

# Initialize computers for all labs
def initialize_all_labs_computers():
    try:
        print("DEBUG: Initializing computers for all labs")
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Get all labs
        cursor.execute('SELECT id FROM laboratories')
        labs = cursor.fetchall()
        
        initialized_count = 0
        for lab in labs:
            lab_id = lab[0]
            if initialize_lab_computers(lab_id):
                initialized_count += 1
        
        print(f"DEBUG: Initialized computers for {initialized_count} labs")
        return True
    except Exception as e:
        print(f"DEBUG: Error initializing lab computers: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Create laboratories table and populate with default labs if empty
def create_and_populate_laboratories():
    try:
        print("DEBUG: Creating and checking laboratories table")
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Create laboratories table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS laboratories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT NOT NULL,
            status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'Unavailable'))
        )''')
        
        # Check if laboratories table has any rows
        cursor.execute('SELECT COUNT(*) FROM laboratories')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("DEBUG: Laboratories table is empty, adding default labs")
            # Insert default labs
            default_labs = [
                ('Lab 517', 'Available'),
                ('Lab 524', 'Available'),
                ('Lab 526', 'Available'),
                ('Lab 528', 'Available'),
                ('Lab 530', 'Available'),
                ('Lab 542', 'Available'),
                ('Lab 544', 'Available')
            ]
            
            cursor.executemany('INSERT INTO laboratories (lab_name, status) VALUES (?, ?)', default_labs)
            conn.commit()
            print(f"DEBUG: Added {len(default_labs)} default laboratories")
        else:
            print(f"DEBUG: Laboratories table already has {count} labs")
        
        return True
    except Exception as e:
        print(f"DEBUG: Error in create_and_populate_laboratories: {e}")
        return False
    finally:
        if conn:
            conn.close()

def drop_and_recreate_lab_schedules():
    """Drop and recreate lab_schedules table structure without inserting any data."""
    try:
        print("DEBUG: Starting to drop and recreate lab_schedules table")
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Drop the lab_schedules table if it exists
        cursor.execute('DROP TABLE IF EXISTS lab_schedules')
        print("DEBUG: lab_schedules table dropped")
        
        # Create the lab_schedules table again
        cursor.execute('''
        CREATE TABLE lab_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')),
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            subject_code TEXT,
            subject_name TEXT,
            status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'Reserved', 'Unavailable')),
            reason TEXT,
            FOREIGN KEY (lab_id) REFERENCES laboratories(id)
        )''')
        print("DEBUG: lab_schedules table recreated")
        
        conn.commit()
        print("DEBUG: Successfully recreated lab_schedules table structure")
        return True
    except Exception as e:
        import traceback
        print(f"ERROR: Error recreating lab schedules table: {str(e)}")
        print(traceback.format_exc())
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

def create_reservation_notifications_table():
    """Create the reservation_notifications table if it doesn't exist"""
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservation_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_idno TEXT NOT NULL,
            reservation_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_idno) REFERENCES students(idno),
            FOREIGN KEY (reservation_id) REFERENCES student_reservation(id) ON DELETE CASCADE
        )''')
        
        conn.commit()
        print("Reservation notifications table created or already exists")
        return True
    except Exception as e:
        print(f"Error creating reservation notifications table: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_reservation_notification(student_idno, reservation_id, title, message, notification_type):
    """Add a new reservation notification for a student
    notification_type can be: 'status_update', 'upcoming', 'system'
    """
    sql = """
        INSERT INTO reservation_notifications 
        (student_idno, reservation_id, title, message, notification_type)
        VALUES (?, ?, ?, ?, ?)
    """
    return postprocess(sql, (student_idno, reservation_id, title, message, notification_type))

def get_student_notifications(student_idno, limit=20):
    """Get notifications for a student, including reservation notifications"""
    sql = """
        SELECT * FROM reservation_notifications
        WHERE student_idno = ?
        ORDER BY created_at DESC
        LIMIT ?
    """
    return getprocess(sql, (student_idno, limit))

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    sql = """
        UPDATE reservation_notifications
        SET is_read = 1
        WHERE id = ?
    """
    return postprocess(sql, (notification_id,))

def mark_all_notifications_read(student_idno):
    """Mark all notifications for a student as read"""
    sql = """
        UPDATE reservation_notifications
        SET is_read = 1
        WHERE student_idno = ? AND is_read = 0
    """
    return postprocess(sql, (student_idno,))

def get_unread_notifications_count(student_idno):
    """Get count of unread notifications for a student"""
    sql = """
        SELECT COUNT(*) as count FROM reservation_notifications
        WHERE student_idno = ? AND is_read = 0
    """
    result = getprocess(sql, (student_idno,))
    return result[0]['count'] if result else 0