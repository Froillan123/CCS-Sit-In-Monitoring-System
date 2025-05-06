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

def create_reservation(student_idno, lab_id, purpose, reservation_date, 
                      time_slot=None, computer_id=None, status="Pending", 
                      reservation_type="reservation"):
    """Create a new reservation in the consolidated reservations table
    reservation_type can be: 'sit-in' or 'reservation'
    """
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Get student name
        cursor.execute("SELECT firstname || ' ' || lastname as student_name FROM students WHERE idno = ?", 
                      (student_idno,))
        student = cursor.fetchone()
        if not student:
            print(f"Student with ID {student_idno} not found")
            return False
        
        student_name = student[0]
        
        # Get computer number if computer_id is provided
        computer_number = None
        if computer_id:
            cursor.execute("SELECT computer_number FROM lab_computers WHERE id = ?", (computer_id,))
            computer = cursor.fetchone()
            if computer:
                computer_number = computer[0]
        
        # For sit-ins, get an available computer if none is assigned
        if reservation_type == 'sit-in' and not computer_id:
            cursor.execute('''
                SELECT id, computer_number 
                FROM lab_computers 
                WHERE lab_id = ? AND status = 'Available' 
                ORDER BY computer_number 
                LIMIT 1
            ''', (lab_id,))
            available_computer = cursor.fetchone()
            if available_computer:
                computer_id = available_computer[0]
                computer_number = available_computer[1]
        
        # Insert reservation
        cursor.execute('''
            INSERT INTO reservations 
            (student_idno, student_name, lab_id, computer_id, computer_number, purpose, 
            reservation_date, time_slot, status, reservation_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (student_idno, student_name, lab_id, computer_id, computer_number, 
              purpose, reservation_date, time_slot, status, reservation_type))
        
        reservation_id = cursor.lastrowid
        conn.commit()
        
        # If computer was assigned, update its status
        if computer_id and status == 'Approved':
            update_computer_status(computer_id, 'In Use', student_idno)
        
        # Add notification
        notification_title = "New Reservation" if reservation_type == "reservation" else "New Sit-In"
        notification_message = f"Your {reservation_type} request has been submitted and is pending approval."
        add_reservation_notification(student_idno, reservation_id, notification_title, 
                                    notification_message, "status_update")
        
        return reservation_id
    except Exception as e:
        print(f"Error creating reservation: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


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
    SELECT 
        (SELECT COUNT(*) FROM reservations 
         WHERE student_idno = ? 
         AND (status = 'Logged Out' OR status = 'Closed')
         AND reservation_type = 'sit-in')
        as sitin_count
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
            points_awarded INTEGER DEFAULT 0,
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

# Create logged_out_student_reservation table for completed reservations
def create_logged_out_student_reservation_table():
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logged_out_student_reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id INTEGER,
            student_idno TEXT NOT NULL,
            lab_id INTEGER NOT NULL,
            computer_id INTEGER,
            purpose TEXT NOT NULL,
            reservation_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            login_time TEXT,
            logout_time TEXT,
            status TEXT DEFAULT 'Logged Out',
            feedback_submitted INTEGER DEFAULT 0,
            points_awarded INTEGER DEFAULT 0,
            created_at TIMESTAMP,
            logged_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_idno) REFERENCES students(idno),
            FOREIGN KEY (lab_id) REFERENCES laboratories(id),
            FOREIGN KEY (computer_id) REFERENCES lab_computers(id)
        )''')
        
        conn.commit()
        print("Logged out student reservation table created or already exists")
    except Exception as e:
        print(f"Error creating logged out student reservation table: {e}")
    finally:
        if conn:
            conn.close()

# Function to move a logged out reservation to the logged_out_student_reservation table
def move_to_logged_out_reservations(reservation_id, logout_time):
    try:
        # First, get the reservation data
        sql_get = """
            SELECT * FROM student_reservation
            WHERE id = ?
        """
        reservation = getprocess(sql_get, (reservation_id,))
        
        if not reservation or len(reservation) == 0:
            print(f"Reservation with ID {reservation_id} not found")
            return False
            
        reservation = reservation[0]
        
        # Insert into logged_out_student_reservation
        sql_insert = """
            INSERT INTO logged_out_student_reservation
            (original_id, student_idno, lab_id, computer_id, purpose, reservation_date, 
            time_slot, login_time, logout_time, status, feedback_submitted, points_awarded, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Logged Out', ?, ?, ?)
        """
        
        params = (
            reservation_id,
            reservation['student_idno'],
            reservation['lab_id'],
            reservation['computer_id'],
            reservation['purpose'],
            reservation['reservation_date'],
            reservation['time_slot'],
            reservation.get('login_time', None),
            logout_time,
            reservation['feedback_submitted'],
            reservation.get('points_awarded', 0),
            reservation['created_at']
        )
        
        if not postprocess(sql_insert, params):
            print(f"Failed to insert into logged_out_student_reservation table")
            return False
            
        # Delete from student_reservation
        sql_delete = """
            DELETE FROM student_reservation
            WHERE id = ?
        """
        
        if not postprocess(sql_delete, (reservation_id,)):
            print(f"Failed to delete from student_reservation table")
            return False
            
        return True
    except Exception as e:
        print(f"Error moving reservation to logged_out table: {e}")
        return False

# Function to get student's logged out reservations
def get_student_logged_out_reservations(student_idno):
    sql = """
        SELECT lo.*, l.lab_name, lc.computer_number
        FROM logged_out_student_reservation lo
        JOIN laboratories l ON lo.lab_id = l.id
        LEFT JOIN lab_computers lc ON lo.computer_id = lc.id
        WHERE lo.student_idno = ?
        ORDER BY lo.logged_out_at DESC
    """
    return getprocess(sql, (student_idno,))

# Function to create a new student reservation
def create_student_reservation(student_idno, lab_id, computer_id, purpose, reservation_date, time_slot):
    # Check if the student exists and get their name
    student = get_student_by_idno(student_idno)
    if not student:
        print(f"Student with ID {student_idno} not found")
        return False
    
    student_name = f"{student['firstname']} {student['lastname']}"
    
    # Use the consolidated reservations table instead of student_reservation
    sql = """
        INSERT INTO reservations 
        (student_idno, student_name, lab_id, computer_id, purpose, reservation_date, 
         time_slot, status, reservation_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    return postprocess(sql, (
        student_idno,
        student_name,
        lab_id,
        computer_id, 
        purpose, 
        reservation_date, 
        time_slot, 
        'Pending',
        'reservation'  # Set reservation_type to 'reservation'
    ))

# Get reservations by student ID
def get_student_reservations(student_idno, include_logged_out=False):
    """Get all reservations for a student
    Parameters:
        student_idno: The student ID number
        include_logged_out: Whether to include logged out reservations
    """
    try:
        print(f"Getting reservations for student: {student_idno}, include_logged_out: {include_logged_out}")
        
        status_condition = "" if include_logged_out else "AND r.status != 'Logged Out'"
        
        sql = f"""
            SELECT 
                r.id, 
                r.student_idno, 
                r.lab_id, 
                r.computer_id, 
                r.purpose, 
                r.reservation_date, 
                r.time_slot, 
                r.login_time, 
                r.logout_time, 
                r.status, 
                r.reservation_type,
                r.created_at,
                l.lab_name, 
                lc.computer_number,
                CASE 
                    WHEN r.login_time IS NOT NULL AND r.logout_time IS NULL THEN 'Active Now' 
                    ELSE r.status 
                END AS display_status
            FROM 
                reservations r
            JOIN 
                laboratories l ON r.lab_id = l.id
            LEFT JOIN 
                lab_computers lc ON r.computer_id = lc.id
            WHERE 
                r.student_idno = ? {status_condition}
            ORDER BY 
                r.created_at DESC
        """
        
        reservations = getprocess(sql, (student_idno,))
        print(f"Found {len(reservations)} reservations for student {student_idno}")
        
        # Format dates for better display
        for res in reservations:
            # Make sure all reservations have reservation_type
            if 'reservation_type' not in res or not res['reservation_type']:
                res['reservation_type'] = 'reservation'
                
            # Make sure all the required fields exist
            if 'lab_name' not in res or not res['lab_name']:
                res['lab_name'] = 'Unknown Lab'
                
            # Ensure status is not null
            if 'status' not in res or not res['status']:
                res['status'] = 'Pending'
        
        return reservations
    except Exception as e:
        print(f"Error getting student reservations: {e}")
        import traceback
        traceback.print_exc()
        return []

# Function to check if a student has a pending reservation
def has_pending_student_reservation(student_idno):
    sql = """
        SELECT COUNT(*) as count
        FROM reservations
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
        # Check if end_time exists - it's now optional
        if schedule['end_time']:
            time_slot = f"{schedule['start_time']} - {schedule['end_time']}"
        else:
            # If no end_time is provided, just use the start_time alone
            time_slot = schedule['start_time']
            
        time_slots.append({
            'start_time': schedule['start_time'],
            'end_time': schedule.get('end_time', ''),  # Handle missing end_time
            'time_slot': time_slot,
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
    """Update the status of a student reservation"""
    try:
        query = "UPDATE reservations SET status = ? WHERE id = ?"
        result = postprocess(query, (status, reservation_id))
        
        if result:
            print(f"Updated reservation {reservation_id} status to {status}")
            return True
        else:
            print(f"Failed to update reservation {reservation_id} status")
            return False
    except Exception as e:
        print(f"Error updating student reservation status: {e}")
        return False

# Initialize all tables when module is loaded
def initialize_tables():
    """Initialize all necessary tables"""
    create_reservations_table()
    create_lab_computers_table()
    create_reservation_notifications_table()
    create_points_tables()
    return True

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
def add_or_update_lab_schedule(lab_id, day_of_week, start_time, end_time=None, status='Available', subject_code=None, subject_name=None, reason=None, schedule_id=None):
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

def create_reservations_table():
    """Create a new consolidated reservations table that handles both sit-ins and lab reservations"""
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Create the reservations table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_idno TEXT NOT NULL,
            student_name TEXT NOT NULL,
            lab_id INTEGER NOT NULL,
            computer_id INTEGER,
            computer_number INTEGER,
            purpose TEXT NOT NULL,
            reservation_date TEXT NOT NULL,
            time_slot TEXT,
            login_time TEXT,
            logout_time TEXT,
            status TEXT DEFAULT 'Pending', -- Pending, Approved, Rejected, Logged Out
            reservation_type TEXT NOT NULL DEFAULT 'sit-in', -- 'sit-in' or 'reservation'
            session_number INTEGER,
            points_awarded INTEGER DEFAULT 0,
            feedback_submitted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_idno) REFERENCES students(idno),
            FOREIGN KEY (lab_id) REFERENCES laboratories(id),
            FOREIGN KEY (computer_id) REFERENCES lab_computers(id)
        )''')
        
        # Create indices for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reservations_student_idno ON reservations(student_idno)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reservations_date ON reservations(reservation_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reservations_type ON reservations(reservation_type)')
        
        conn.commit()
        print("Consolidated reservations table created or already exists")
        return True
    except Exception as e:
        print(f"Error creating reservations table: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Function to create reservation notifications table with corrected foreign key
def create_reservation_notifications_table():
    """Create the reservation notifications table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservation_notifications (
                    id SERIAL PRIMARY KEY,
                    student_idno VARCHAR(50) NOT NULL,
                    reservation_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    is_read INTEGER DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_idno) REFERENCES students(student_idno),
                    FOREIGN KEY (reservation_id) REFERENCES reservations(id)
                )
            """)
            
            # Add notification_sent column to reservations table if it doesn't exist
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'reservations' 
                        AND column_name = 'notification_sent'
                    ) THEN
                        ALTER TABLE reservations ADD COLUMN notification_sent BOOLEAN DEFAULT FALSE;
                    END IF;
                END $$;
            """)
            
            # Add is_waiting_for_sit_in and waiting_since columns to students table if they don't exist
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'students' 
                        AND column_name = 'is_waiting_for_sit_in'
                    ) THEN
                        ALTER TABLE students ADD COLUMN is_waiting_for_sit_in BOOLEAN DEFAULT FALSE;
                    END IF;
                    
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'students' 
                        AND column_name = 'waiting_since'
                    ) THEN
                        ALTER TABLE students ADD COLUMN waiting_since TIMESTAMP;
                    END IF;
                END $$;
            """)
            
            # Add is_available_for_sit_in column to lab_computers table if it doesn't exist
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'lab_computers' 
                        AND column_name = 'is_available_for_sit_in'
                    ) THEN
                        ALTER TABLE lab_computers ADD COLUMN is_available_for_sit_in BOOLEAN DEFAULT TRUE;
                    END IF;
                END $$;
            """)
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error creating reservation notifications table: {str(e)}")
        return False

# Migrate data from old tables to new consolidated table
def migrate_reservations_data():
    """Migrate data from student_reservation and logged_out_student_reservation to the new reservations table"""
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Check if old tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('student_reservation', 'logged_out_student_reservation')")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        if 'student_reservation' in table_names:
            print("Migrating data from student_reservation table")
            
            # Get student names for each reservation
            cursor.execute('''
                SELECT sr.id, sr.student_idno, s.firstname || ' ' || s.lastname as student_name, 
                       sr.lab_id, sr.computer_id, lc.computer_number, sr.purpose, sr.reservation_date, 
                       sr.time_slot, NULL as login_time, NULL as logout_time, sr.status, 
                       'reservation' as reservation_type, NULL as session_number, 
                       sr.points_awarded, sr.feedback_submitted, sr.created_at
                FROM student_reservation sr
                JOIN students s ON sr.student_idno = s.idno
                LEFT JOIN lab_computers lc ON sr.computer_id = lc.id
            ''')
            
            student_reservations = cursor.fetchall()
            
            # Insert into new reservations table
            for res in student_reservations:
                cursor.execute('''
                    INSERT INTO reservations 
                    (id, student_idno, student_name, lab_id, computer_id, computer_number, purpose, 
                     reservation_date, time_slot, login_time, logout_time, status, reservation_type, 
                     session_number, points_awarded, feedback_submitted, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', res)
            
            print(f"Migrated {len(student_reservations)} records from student_reservation")
        
        if 'logged_out_student_reservation' in table_names:
            print("Migrating data from logged_out_student_reservation table")
            
            # Get student names for each logged out reservation
            cursor.execute('''
                SELECT losr.original_id, losr.student_idno, s.firstname || ' ' || s.lastname as student_name, 
                       losr.lab_id, losr.computer_id, lc.computer_number, losr.purpose, losr.reservation_date, 
                       losr.time_slot, losr.login_time, losr.logout_time, losr.status, 
                       'reservation' as reservation_type, NULL as session_number, 
                       losr.points_awarded, losr.feedback_submitted, losr.created_at
                FROM logged_out_student_reservation losr
                JOIN students s ON losr.student_idno = s.idno
                LEFT JOIN lab_computers lc ON losr.computer_id = lc.id
            ''')
            
            logged_out_reservations = cursor.fetchall()
            
            # Insert into new reservations table
            for res in logged_out_reservations:
                cursor.execute('''
                    INSERT INTO reservations 
                    (id, student_idno, student_name, lab_id, computer_id, computer_number, purpose, 
                     reservation_date, time_slot, login_time, logout_time, status, reservation_type, 
                     session_number, points_awarded, feedback_submitted, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', res)
            
            print(f"Migrated {len(logged_out_reservations)} records from logged_out_student_reservation")
        
        conn.commit()
        
        return True
    except Exception as e:
        print(f"Error migrating reservation data: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Script to create a separate notifications table when executed directly
def create_notifications_tables_script():
    """Create the reservation_notifications table with the correct reservation ID foreign key
    This function is meant to be called directly from the command line.
    """
    try:
        print("Creating notifications table...")
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Create the notifications table (drop if exists)
        cursor.execute('DROP TABLE IF EXISTS reservation_notifications')
        
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
            FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
        )''')
        
        conn.commit()
        print("Reservation notifications table created successfully!")
        return True
    except Exception as e:
        print(f"Error creating reservation notifications table: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Update the function to add a reservation notification to work with the new table
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

# Get reservations by student ID
def get_student_reservations(student_idno, include_logged_out=False):
    """Get all reservations for a student
    Parameters:
        student_idno: The student ID number
        include_logged_out: Whether to include logged out reservations
    """
    try:
        print(f"Getting reservations for student: {student_idno}, include_logged_out: {include_logged_out}")
        
        status_condition = "" if include_logged_out else "AND r.status != 'Logged Out'"
        
        sql = f"""
            SELECT 
                r.id, 
                r.student_idno, 
                r.lab_id, 
                r.computer_id, 
                r.purpose, 
                r.reservation_date, 
                r.time_slot, 
                r.login_time, 
                r.logout_time, 
                r.status, 
                r.reservation_type,
                r.created_at,
                l.lab_name, 
                lc.computer_number,
                CASE 
                    WHEN r.login_time IS NOT NULL AND r.logout_time IS NULL THEN 'Active Now' 
                    ELSE r.status 
                END AS display_status
            FROM 
                reservations r
            JOIN 
                laboratories l ON r.lab_id = l.id
            LEFT JOIN 
                lab_computers lc ON r.computer_id = lc.id
            WHERE 
                r.student_idno = ? {status_condition}
            ORDER BY 
                r.created_at DESC
        """
        
        reservations = getprocess(sql, (student_idno,))
        print(f"Found {len(reservations)} reservations for student {student_idno}")
        
        # Format dates for better display
        for res in reservations:
            # Make sure all reservations have reservation_type
            if 'reservation_type' not in res or not res['reservation_type']:
                res['reservation_type'] = 'reservation'
                
            # Make sure all the required fields exist
            if 'lab_name' not in res or not res['lab_name']:
                res['lab_name'] = 'Unknown Lab'
                
            # Ensure status is not null
            if 'status' not in res or not res['status']:
                res['status'] = 'Pending'
        
        return reservations
    except Exception as e:
        print(f"Error getting student reservations: {e}")
        import traceback
        traceback.print_exc()
        return []

# Update the initialize_tables function to use the new consolidated tables
def initialize_tables():
    """Initialize all necessary tables"""
    create_reservations_table()
    create_lab_computers_table()
    create_reservation_notifications_table()
    create_points_tables()
    return True

# Function to get a computer by its number in a specific lab
def get_computer_by_number(lab_id, computer_number):
    """Get computer details by lab ID and computer number"""
    try:
        sql = """
            SELECT * FROM lab_computers 
            WHERE lab_id = ? AND computer_number = ?
        """
        result = getprocess(sql, (lab_id, computer_number))
        return result[0] if result and len(result) > 0 else None
    except Exception as e:
        print(f"Error in get_computer_by_number: {e}")
        return None

# Function to get student notifications
def get_student_notifications(student_idno, limit=20, include_read=False, reservation_type=None):
    """Get notifications for a student with options to include read notifications and limit count
    
    Parameters:
    student_idno (str): The student ID number
    limit (int): Maximum number of notifications to return
    include_read (bool): Whether to include already read notifications
    reservation_type (str): Optional filter by reservation type ('reservation' or 'sit-in')
    """
    try:
        read_condition = "" if include_read else "AND is_read = 0"
        
        # Add reservation type filter if specified
        reservation_type_condition = ""
        params = [student_idno]
        
        if reservation_type:
            # Join with the reservations table to filter by reservation_type
            reservation_type_condition = """
                AND EXISTS (
                    SELECT 1 FROM reservations r 
                    WHERE r.id = reservation_notifications.reservation_id 
                    AND r.reservation_type = ?
                )
            """
            params.append(reservation_type)
        
        params.append(limit)
        
        sql = f"""
            SELECT 
                rn.*,
                r.reservation_type,
                r.status as reservation_status
            FROM 
                reservation_notifications rn
            LEFT JOIN
                reservations r ON rn.reservation_id = r.id
            WHERE 
                rn.student_idno = ? 
                {read_condition}
                {reservation_type_condition}
            ORDER BY 
                rn.created_at DESC
            LIMIT ?
        """
        return getprocess(sql, tuple(params))
    except Exception as e:
        print(f"Error getting student notifications: {e}")
        return []

if __name__ == "__main__":
    # This code will run when the script is executed directly
    print("Creating notification tables...")
    create_notifications_tables_script()
    print("Done!")