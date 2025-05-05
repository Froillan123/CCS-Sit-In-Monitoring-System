import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify, Response, stream_with_context
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import time
import threading
import string
import secrets
import random
import json
import sqlite3
import datetime
import re
# from profanity_check import predict_prob  # Commented out due to compatibility issues
from better_profanity import profanity
from werkzeug.exceptions import BadRequest
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from flask_cors import CORS
import openai
from threading import Thread
from prompts import get_response
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
from functools import wraps

# Import dbhelper functions
from dbhelper import *

profanity.load_censor_words()

app = Flask(__name__)
CORS(app)
app.config["SESSION_COOKIE_NAME"] = "main_app_session"
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.secret_key = 'CCS-SIT-IN-MONITORING-SYSTEM'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Create uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Simple in-memory cache
class SimpleCache:
    def __init__(self):
        self._cache = {}
        
    def get(self, key):
        return self._cache.get(key)
        
    def set(self, key, value, timeout=None):
        self._cache[key] = value
        
    def delete(self, key):
        if key in self._cache:
            del self._cache[key]

# Initialize cache
cache = SimpleCache()

# Initialize all tables
initialize_tables()

# Create lab resources table if it doesn't exist
def create_lab_resources_table():
    try:
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            link TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT NOT NULL
        )''')
        conn.commit()
        print("Lab resources table created or already exists")
    except Exception as e:
        print(f"Error creating lab resources table: {e}")
    finally:
        if conn:
            conn.close()

# Create lab resources table
create_lab_resources_table()

# Ensure laboratories table exists with data
create_and_populate_laboratories()
print("DEBUG: Laboratories table initialized")

# Initialize computers for all labs
initialize_all_labs_computers()
print("DEBUG: Lab computers initialization completed")

# Delete old reservations thread
delete_thread = threading.Thread(target=delete_old_reservations)
delete_thread.daemon = True
delete_thread.start()

KEY_IV_FILE = "key_iv.dat"

# Check if the key and IV exist in the file, otherwise generate and store them
if not os.path.exists(KEY_IV_FILE):
    AES_KEY = get_random_bytes(32)  # 256-bit key
    AES_IV = get_random_bytes(16)   # 16-byte IV
    with open(KEY_IV_FILE, "wb") as f:
        f.write(base64.b64encode(AES_KEY) + b'\n')
        f.write(base64.b64encode(AES_IV) + b'\n')
else:
    # Load the key and IV from the file
    with open(KEY_IV_FILE, "rb") as f:
        AES_KEY = base64.b64decode(f.readline().strip())
        AES_IV = base64.b64decode(f.readline().strip())

def get_db_connection():
    conn = sqlite3.connect('student.db')
    conn.row_factory = sqlite3.Row
    return conn

def encrypt_message(message):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded_message = pad(message.encode('utf-8'), AES.block_size)
    encrypted_message = cipher.encrypt(padded_message)
    return base64.b64encode(encrypted_message).decode('utf-8')

def decrypt_message(encrypted_message):
    try:
        encrypted_message = base64.b64decode(encrypted_message)
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        decrypted_message = unpad(cipher.decrypt(encrypted_message), AES.block_size)
        return decrypted_message.decode('utf-8')
    except (ValueError, KeyError) as e:
        print(f"Decryption error: {e}")
        return "[Unable to decrypt message]"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data['message']
    student_idno = data['student_idno']

    # Encrypt the user's message before saving to the database
    encrypted_message = encrypt_message(message)

    # Save encrypted user message to the database
    conn = get_db_connection()
    conn.execute('INSERT INTO chat_history (student_idno, message, sender) VALUES (?, ?, ?)',
                 (student_idno, encrypted_message, 'user'))
    conn.commit()

    # Get custom chatbot response
    reply = get_response(message, session)  # Pass session to get_response

    # Encrypt the bot's reply before saving to the database
    encrypted_reply = encrypt_message(reply)

    # Save encrypted bot message to the database
    conn.execute('INSERT INTO chat_history (student_idno, message, sender) VALUES (?, ?, ?)',
                 (student_idno, encrypted_reply, 'bot'))
    conn.commit()
    conn.close()

    # Return the decrypted bot reply to the frontend
    return jsonify({'reply': reply})

@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    student_idno = request.args.get('student_idno')
    conn = get_db_connection()
    
    # Fetch encrypted chat history from the database
    history = conn.execute('SELECT * FROM chat_history WHERE student_idno = ? ORDER BY timestamp', (student_idno,)).fetchall()
    conn.close()

    # Decrypt messages before returning them
    decrypted_history = []
    for row in history:
        try:
            # Decrypt the message
            decrypted_message = decrypt_message(row['message'])
            decrypted_history.append({
                'id': row['id'],
                'student_idno': row['student_idno'],
                'message': decrypted_message,  # Decrypted message
                'sender': row['sender'],
                'timestamp': row['timestamp']
            })
        except Exception as e:
            # Handle decryption errors (e.g., corrupted data)
            print(f"Error decrypting message (ID: {row['id']}): {e}")
            decrypted_history.append({
                'id': row['id'],
                'student_idno': row['student_idno'],
                'message': "[Unable to decrypt message]",  # Fallback message
                'sender': row['sender'],
                'timestamp': row['timestamp']
            })

    return jsonify(decrypted_history)

active_users_dict = {}
announcements = []

@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    if hasattr(session, 'user_username') and 'user_username' not in session:
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

@app.route('/', methods=['GET', 'POST'])
def login():
    pagetitle = "Login"
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Username and Password are required", 'error')
            return redirect(url_for('login'))

        user = get_user_by_credentials(username, password)

        if user:
            if user['sessions_left'] <= 0:
                flash("You have no sessions left. Please request an extension.", 'warning')
                return redirect(url_for('no_sessions_left'))

            # Storing the username and other details in the session
            session['user_username'] = username
            session['student_idno'] = user['idno']
            session['student_firstname'] = user['firstname']
            session['student_lastname'] = user['lastname']
            session['student_midname'] = user['midname']
            
            # Mark user as active
            active_users_dict[username] = True
            socketio.emit('update_active_users', list(active_users_dict.keys()))  # Emit active users update


            flash("Login successful!", 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid username or password", 'error')
            return redirect(url_for('login'))

    return render_template('client/login.html', pagetitle=pagetitle)


@app.route('/no_sessions_left', methods=['GET', 'POST'])
def no_sessions_left():
    pagetitle = "No Sessions Left"
    if request.method == 'POST':
        student_idno = session.get('student_idno')
        if student_idno:
            flash("Your request for a session extension has been submitted.", 'info')
            return redirect(url_for('login'))  

    return render_template('client/no_sessions_left.html', pagetitle=pagetitle)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')  
        new_password = request.form.get('new_password')  

        if email and new_password:
            student = get_student_by_email(email)
            if not student:
                flash('Student does not exist.', 'error')
                return redirect(url_for('forgot_password'))

            result = update_record('students', email=email, password=new_password)
            
            if result:
                flash('Password updated successfully!', 'success')
                return redirect(url_for('login'))  
            else:
                flash('Error updating password. Please try again.', 'warning')
                return redirect(url_for('forgot_password'))

        flash('Invalid input. Please provide both email and new password.', 'warning')
        return redirect(url_for('forgot_password'))

    return render_template('client/forgotpassword.html')

@app.route('/reservations', methods=['POST'])
def reservations():
    student_idno = session.get('student_idno')
    student_firstname = session.get('student_firstname', '')
    student_lastname = session.get('student_lastname', '')
    student_midname = session.get('student_midname', '')

    student_name = f"{student_firstname} {student_midname} {student_lastname}".strip()

    lab_id = request.form.get('lab_id', '').strip()
    purpose = request.form.get('purpose_select', '').strip()
    reservation_date = request.form.get('reservation_date', '').strip()
    sessions_left = int(request.form.get('sessions_left', 0))  # Get sessions_left from the form
    login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current time as logged-in time

    # Check if all required fields are provided
    if not all([student_idno, student_name, lab_id, purpose, reservation_date]):
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

    # Validate the reservation date format
    try:
        datetime.strptime(reservation_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format (YYYY-MM-DD expected)'}), 400

    # Check if the student already has a pending reservation
    if has_pending_reservation(student_idno):
        return jsonify({'status': 'error', 'message': 'You already have a pending reservation'}), 400

    # Check if the student has sessions left
    if sessions_left <= 0:
        return jsonify({'status': 'error', 'message': 'You have no sessions left'}), 400

    # Create the reservation (without decreasing sessions here)
    if create_reservation(
        student_idno=student_idno,
        student_name=student_name,
        lab_id=lab_id,
        purpose=purpose,
        reservation_date=reservation_date,
        login_time=login_time,  # Logged-in time
        status='Pending'
    ):
        # Emit a Socket.IO event to notify both admin and student
        socketio.emit('new_reservation', {
            'student_idno': student_idno,
            'student_name': student_name,
            'lab_id': lab_id,
            'purpose': purpose,
            'reservation_date': reservation_date,
            'login_time': login_time,
            'status': 'Pending'
        })
        return jsonify({'status': 'success', 'message': 'Reservation created successfully'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Failed to create reservation'}), 500


    

@app.route('/sit-in-reservation/<int:reservation_id>', methods=['POST'])
def sit_in_reservation(reservation_id):
    try:
        print(f"Attempting to approve reservation with ID: {reservation_id}")  # Print reservation ID
        
        # Fetch the reservation details
        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            print(f"Reservation with ID {reservation_id} not found")
            return jsonify({'success': False, 'message': 'Reservation not found'})
        
        print(f"Fetched reservation: {reservation}")  # Print reservation details
        
        # Update the reservation status to "Approved"
        if update_reservation_status(reservation_id, 'Approved'):
            print(f"Successfully updated reservation {reservation_id} status to 'Approved'")  # Print success message
            # Emit a Socket.IO event to notify both admin and student
            socketio.emit('reservation_approved', {
                'reservation_id': reservation_id,
                'status': 'Approved'
            })
            return jsonify({'success': True, 'message': 'Reservation approved successfully'})
        else:
            print(f"Failed to update reservation {reservation_id} status to 'Approved'")
            return jsonify({'success': False, 'message': 'Failed to update reservation status'})
    
    except Exception as e:
        print(f"Error in sit-in reservation for {reservation_id}: {str(e)}")  # Print the exception message
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout-student/<int:reservation_id>', methods=['POST'])
def logout_student(reservation_id):
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        # Get the current reservation details first
        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            return jsonify({"success": False, "message": "Reservation not found"}), 404

        student_idno = reservation['student_idno']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update reservation with logout time and status
        sql = """
        UPDATE reservations 
        SET logout_time = ?, status = 'Logged Out'
        WHERE id = ? AND status = 'Approved'
        """
        params = (current_time, reservation_id)
        
        if not postprocess(sql, params):
            return jsonify({"success": False, "message": "Failed to log out student"}), 500

        # Decrease student's sessions_left by 1
        if not postprocess("UPDATE students SET sessions_left = sessions_left - 1 WHERE idno = ?", (student_idno,)):
            print(f"Warning: Failed to decrement sessions_left for student {student_idno}")

        # Calculate duration in seconds
        login_time = datetime.strptime(reservation['login_time'], '%Y-%m-%d %H:%M:%S')
        logout_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        duration_seconds = int((logout_time - login_time).total_seconds())

        # Record in session history - now passing all parameters correctly
        insert_session_history(
            student_idno=student_idno,
            login_time=reservation['login_time'],
            logout_time=current_time,
            duration=duration_seconds
        )

        # Get the updated reservation with lab name
        updated_reservation = getprocess(
            "SELECT r.*, l.lab_name FROM reservations r JOIN laboratories l ON r.lab_id = l.id WHERE r.id = ?",
            (reservation_id,)
        )[0]

        # Get the student's updated sessions_left
        student = getprocess("SELECT sessions_left FROM students WHERE idno = ?", (student_idno,))[0]
        updated_sessions_left = student['sessions_left']

        # Emit socket events
        socketio.emit('reservation_updated', {
            'reservation_id': reservation_id,
            'logout_time': updated_reservation['logout_time'],
            'status': updated_reservation['status'],
            'sessions_left': updated_sessions_left
        })
        
        socketio.emit(f'student_{updated_reservation["student_idno"]}_reservation_updated', {
            'reservation_id': reservation_id,
            'logout_time': updated_reservation['logout_time'],
            'status': updated_reservation['status'],
            'sessions_left': updated_sessions_left
        })

        return jsonify({
            "success": True, 
            "message": "Student logged out successfully",
            "sessions_left": updated_sessions_left,
            "student_idno": student_idno  # Include student_idno in the response
        })

    except Exception as e:
        print(f"Error logging out student: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/search_students')
def search_students():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    search_term = request.args.get('q', '').strip()
    if not search_term:
        return jsonify({"success": False, "message": "Search term required"}), 400

    # Search in database using dbhelper functions
    query = """
        SELECT idno, firstname, lastname, course, year_level, sessions_left 
        FROM students 
        WHERE idno LIKE ? OR firstname LIKE ? OR lastname LIKE ?
        LIMIT 10
    """
    search_pattern = f"%{search_term}%"
    students = getprocess(query, (search_pattern, search_pattern, search_pattern))
    
    student_list = []
    for student in students:
        student_list.append({
            "idno": student['idno'],
            "firstname": student['firstname'],
            "lastname": student['lastname'],
            "course": student['course'],
            "year_level": student['year_level'],
            "sessions_left": student['sessions_left']
        })
    
    return jsonify({"success": True, "data": student_list})


@app.route('/api/students/<int:student_id>/reset-sessions', methods=['POST'])
def reset_student_sessions(student_id):
    try:
        # Fetch the student from the database using the helper
        sql = "SELECT * FROM students WHERE id = ?"
        student = getprocess(sql, (student_id,))

        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404

        student = student[0]  # Get the first (and only) record

        DEFAULT_SESSIONS = 30  # Or get this from config

        # Update student sessions using the helper
        update_sql = "UPDATE students SET sessions_left = ? WHERE id = ?"
        postprocess(update_sql, (DEFAULT_SESSIONS, student_id))

        # Notify the student if they're online
        socketio.emit('update_session_count', {
            'student_idno': student['idno'],
            'sessions_left': DEFAULT_SESSIONS
        }, room=student['idno'])

        return jsonify({
            'success': True,
            'message': f'Sessions reset to {DEFAULT_SESSIONS} for student {student["idno"]}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resetting sessions: {str(e)}'
        }), 500

        
@app.route('/admin_create_sitin', methods=['POST'])
def admin_create_sitin():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    student_id = data.get('student_id')
    lab = data.get('lab')
    purpose = data.get('purpose')

    if not all([student_id, lab, purpose]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    # Get student info including current sessions_left
    student = get_student_by_idno(student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    if student['sessions_left'] <= 0:
        return jsonify({"success": False, "message": "Student has no sessions left"}), 400

    # Calculate session number (total sessions - remaining + 1)
    session_number = (30 - student['sessions_left']) + 1  # Assuming 30 is max sessions

    # Create reservation with session number
    sql = """
        INSERT INTO reservations 
        (student_idno, student_name, lab_id, purpose, reservation_date, 
         login_time, status, session_number) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        student_id, 
        f"{student['firstname']} {student['lastname']}",
        lab, 
        purpose,
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Approved',
        session_number
    )
    
    if not postprocess(sql, params):
        return jsonify({"success": False, "message": "Failed to create reservation"}), 500

    # Get the full reservation details with lab name
    new_reservation = getprocess(
        """SELECT r.*, l.lab_name 
           FROM reservations r 
           JOIN laboratories l ON r.lab_id = l.id 
           WHERE r.student_idno = ? 
           ORDER BY r.id DESC LIMIT 1""",
        (student_id,)
    )[0]

    # Add sessions_left to the response
    new_reservation['sessions_left'] = student['sessions_left']

    # Emit socket events
    socketio.emit('new_sitin', new_reservation)  # For admin interface
    socketio.emit(f'student_{student_id}_new_reservation', new_reservation)  # For student interface

    return jsonify({
        "success": True,
        "message": "Sit-in reservation created",
        "reservation": new_reservation
    })



def get_all_reservations(search_term='') -> list:
    if search_term:
        sql = """
        SELECT r.id, r.student_idno, r.student_name, l.lab_name, r.purpose, 
               r.reservation_date, r.login_time, r.logout_time, r.status
        FROM reservations r
        JOIN laboratories l ON r.lab_id = l.id
        WHERE r.student_idno LIKE ? AND r.status = 'Pending'
        """
        return getprocess(sql, (f"%{search_term}%",))
    else:
        sql = """
        SELECT r.id, r.student_idno, r.student_name, l.lab_name, r.purpose, 
               r.reservation_date, r.login_time, r.logout_time, r.status
        FROM reservations r
        JOIN laboratories l ON r.lab_id = l.id
        WHERE r.status = 'Pending'
        """
        return getprocess(sql)
    
@app.route('/get_all_reservations')
def get_all_reservations():
    try:
        query = """
            SELECT 
                r.id, 
                r.student_idno as student_id,
                r.student_name,
                l.lab_name,
                l.id as lab_id,  -- Changed from # to proper comment
                r.purpose,
                DATE(r.reservation_date) AS reservation_date,
                r.status,
                TIME(r.login_time) AS login_time,
                TIME(r.logout_time) AS logout_time,
                r.session_number
            FROM reservations r
            LEFT JOIN laboratories l ON r.lab_id = l.id
            LEFT JOIN students s ON r.student_idno = s.idno
            ORDER BY r.reservation_date DESC, r.login_time DESC
        """
        reservations = getprocess(query)
        
        # Convert datetime objects to strings
        for reservation in reservations:
            if 'reservation_date' in reservation:
                reservation['reservation_date'] = str(reservation['reservation_date'])
            if 'login_time' in reservation:
                reservation['login_time'] = str(reservation['login_time']) if reservation['login_time'] else None
            if 'logout_time' in reservation:
                reservation['logout_time'] = str(reservation['logout_time']) if reservation['logout_time'] else None
        
        return jsonify({
            'success': True,
            'reservations': reservations
        })
    except Exception as e:
        print(f"Error in get_all_reservations: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/get_reservation_history')
def get_reservation_history():
    if 'student_idno' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    student_idno = session['student_idno']
    
    sql = """
    SELECT r.id, l.lab_name, r.purpose, r.reservation_date, r.status, 
           COALESCE(r.logout_time, '') as logout_time,
           EXISTS(SELECT 1 FROM feedback WHERE reservation_id = r.id) as feedback_submitted
    FROM reservations r
    JOIN laboratories l ON r.lab_id = l.id
    WHERE r.student_idno = ? 
    AND r.status IN ('Closed', 'Cancelled', 'Logged Out', 'Approved', 'Disapproved')
    ORDER BY r.reservation_date DESC
    """
    
    try:
        reservations = getprocess(sql, (student_idno,))
        
        # Convert feedback_submitted from 0/1 to True/False
        formatted_reservations = [
            {**dict(row), "feedback_submitted": bool(row["feedback_submitted"])}
            for row in reservations
        ]

        return jsonify({
            "success": True, 
            "data": formatted_reservations
        })
    except Exception as e:
        print(f"Error fetching reservation history: {e}")
        return jsonify({"success": False, "message": "Error fetching reservation history"}), 500

    

@app.route('/get_reservations')
def get_reservations():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    search_term = request.args.get('search', '').strip()
    reservations = get_all_reservations(search_term)  # Fetch reservations with lab_name
    reservation_list = []

    for reservation in reservations:
        # Fetch sessions_left for the student
        student_idno = reservation['student_idno']
        student = get_student_by_idno(student_idno)
        sessions_left = student['sessions_left'] if student else 0

        reservation_list.append({
            "id": reservation['id'],
            "student_idno": reservation['student_idno'],
            "student_name": reservation['student_name'],
            "lab_name": reservation['lab_name'],  # Use lab_name instead of lab_id
            "purpose": reservation['purpose'],
            "reservation_date": reservation['reservation_date'],
            "login_time": reservation['login_time'],  # Use login_time instead of time_in
            "logout_time": reservation['logout_time'],  # Use logout_time instead of time_out
            "status": reservation['status'],
            "sessions_left": sessions_left  # Add sessions_left to the response
        })

    return jsonify({"success": True, "data": reservation_list})


@app.route('/get_currentsitin')
def get_currentsitin():
    try:
        # Check if admin is logged in
        if 'admin_username' not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401
            
        # Get all current sit-ins (includes both regular sit-ins and active reservations)
        query = """
            SELECT r.id, r.student_idno, r.student_name, l.lab_name, r.purpose, 
                   r.reservation_date, r.login_time, r.logout_time, r.status,
                   r.session_number,
                   'sit-in' as reservation_type
            FROM reservations r
            JOIN laboratories l ON r.lab_id = l.id
            WHERE r.status IN ('Active', 'In Use', 'Approved')
            
            UNION ALL
            
            SELECT sr.id, sr.student_idno, 
                   (SELECT firstname || ' ' || lastname FROM students s WHERE s.idno = sr.student_idno) as student_name,
                   l.lab_name, sr.purpose, sr.reservation_date, 
                   substr(sr.time_slot, 1, 5) as login_time, 
                   substr(sr.time_slot, -5) as logout_time,
                   sr.status,
                   NULL as session_number,
                   'reservation' as reservation_type
            FROM student_reservation sr
            JOIN laboratories l ON sr.lab_id = l.id
            WHERE sr.status = 'In Use'
            
            ORDER BY login_time DESC
        """
        result = getprocess(query)
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        print(f"Error fetching current sit-ins: {e}")
        return jsonify({"success": False, "message": str(e)}), 500



@app.route('/get_sitin_records')
def get_sitin_records():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        sql = """
        SELECT r.id, r.student_idno, r.student_name, l.lab_name, r.purpose, 
               r.reservation_date, r.login_time, r.logout_time, r.status,
               r.session_number, s.sessions_left, r.points_awarded,
               EXISTS(SELECT 1 FROM feedback WHERE reservation_id = r.id) as feedback_submitted
        FROM reservations r
        JOIN laboratories l ON r.lab_id = l.id
        JOIN students s ON r.student_idno = s.idno
        WHERE r.status = 'Logged Out' OR r.logout_time IS NOT NULL
        ORDER BY r.login_time DESC
        """
        reservations = getprocess(sql)
        
        return jsonify({"success": True, "data": reservations})
    except Exception as e:
        print(f"Error fetching sit-in records: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/student_dashboard')
def student_dashboard():
    pagetitle = "Student Dashboard"
    
    # Ensure the user is logged in
    if 'user_username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('login'))

    # Retrieve student data based on the username stored in the session
    student = get_student_by_username(session['user_username'])
    if not student:
        flash("Student not found", 'danger')
        return redirect(url_for('login'))

    # Fetch the lab names and current session information
    labs = get_lab_names()  
    current_session = get_total_session(student['idno'])

    # Get the student's reservations
    reservations = get_reservations_by_student_id(student['idno'])

    return render_template(
        'client/studentdashboard.html',
        student=student,
        pagetitle=pagetitle,
        labs=labs,
        idno=student['idno'],
        current_session=current_session,
        reservations=reservations 
    )

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        reservation_id = data.get('reservation_id')
        feedback_text = data.get('feedback_text')
        rating = data.get('rating')

        # Validate required fields
        if not all([reservation_id, feedback_text, rating]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        # Check for foul language using better_profanity instead of profanity_check
        contains_profanity = profanity.contains_profanity(feedback_text)
        censored_text = profanity.censor(feedback_text)

        # Fetch reservation details
        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404

        # Check if feedback already exists
        conn = get_db_connection()
        existing_feedback = conn.execute(
            'SELECT * FROM feedback WHERE reservation_id = ?', (reservation_id,)
        ).fetchone()
        if existing_feedback:
            conn.close()
            return jsonify({'success': False, 'message': 'Feedback already submitted'}), 400

        # Save feedback (including profanity flag)
        conn.execute(
            '''INSERT INTO feedback 
            (reservation_id, lab, student_idno, feedback_text, rating, contains_profanity, original_text) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (reservation_id, reservation['lab_name'], reservation['student_idno'], 
             censored_text, rating, contains_profanity, 
             feedback_text if contains_profanity else censored_text)
        )
        conn.commit()
        conn.close()

        # Notify admins with profanity alert
        socketio.emit('new_feedback', {
            'reservation_id': reservation_id,
            'lab': reservation['lab_name'],
            'student_idno': reservation['student_idno'],
            'feedback_text': censored_text,
            'original_text': feedback_text if contains_profanity else None,
            'rating': rating,
            'contains_profanity': contains_profanity
        }, broadcast=True)

        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully',
            'contains_profanity': contains_profanity,
            'censored_text': censored_text
        }), 200

    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@socketio.on('submit_feedback')
def handle_feedback(data):
    try:
        print('Received feedback:', data)
        reservation_id = data['reservation_id']
        feedback_text = data['feedback_text']
        rating = data['rating']

        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            emit('feedback_error', {'message': 'Reservation not found'})
            return

        # Check if feedback already exists
        conn = get_db_connection()
        existing = conn.execute(
            'SELECT 1 FROM feedback WHERE reservation_id = ?', (reservation_id,)
        ).fetchone()
        if existing:
            conn.close()
            emit('feedback_error', {'message': 'Feedback already submitted'})
            return

        # Save feedback
        conn.execute(
            'INSERT INTO feedback (reservation_id, lab, student_idno, feedback_text, rating) VALUES (?, ?, ?, ?, ?)',
            (reservation_id, reservation['lab_name'], reservation['student_idno'], feedback_text, rating)
        )
        conn.commit()
        conn.close()

        # Notify client of success
        emit('feedback_submitted', {
            'success': True,
            'message': 'Feedback submitted successfully',
            'reservation_id': reservation_id
        })

        # Broadcast to admins
        socketio.emit('new_feedback', {
            'reservation_id': reservation_id,
            'lab': reservation['lab_name'],
            'student_idno': reservation['student_idno'],
            'feedback_text': feedback_text,
            'rating': rating
        }, broadcast=True)

    except Exception as e:
        print(f"Error handling feedback: {e}")
        emit('feedback_error', {'message': str(e)})

@app.route('/get-feedback', methods=['GET'])
def get_feedback():
    conn = get_db_connection()
    feedback_data = conn.execute('SELECT * FROM feedback ORDER BY timestamp DESC').fetchall()
    conn.close()

    # Convert the feedback data to a list of dictionaries
    feedback_list = []
    for row in feedback_data:
        feedback_list.append({
            'id': row['id'],
            'lab': row['lab'],
            'student_idno': row['student_idno'],
            'feedback_text': row['feedback_text'],
            'rating': row['rating'],
            'timestamp': row['timestamp']
        })

    return jsonify(feedback_list)





@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_username' not in session:
        return jsonify({"success": False, "message": "You need to login first"}), 401

    try:
        data = request.form.get('data')
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        data = json.loads(data)
        username = session['user_username']

        update_record('students', username=username, firstname=data['firstname'], lastname=data['lastname'], midname=data['midname'], course=data['course'], year_level=data['year_level'], email=data['email'])

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename != '':
                filename = f"student_{username}.png"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                update_record('students', username=username, profile_picture=filename)

        return jsonify({"success": True, "message": "Profile updated successfully"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route('/api/students', methods=['GET'])
def get_all_students():
    try:
        # Check if we're looking for a specific student by ID number
        idno = request.args.get('idno', default='', type=str)
        if idno:
            # Query for a specific student by ID number
            query = """
                SELECT id, idno, lastname, firstname, midname, course, year_level, 
                       sessions_left, profile_picture
                FROM students
                WHERE idno = ?
            """
            students = getprocess(query, (idno,))
            return jsonify({
                'success': True,
                'students': students,
                'total': len(students)
            })
        
        # Otherwise handle pagination as before
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        search = request.args.get('search', default='', type=str)
        
        # Validate parameters
        if page < 1 or per_page < 1:
            raise BadRequest("Invalid pagination parameters")
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Base query
        query = """
            SELECT id, idno, lastname, firstname, midname, course, year_level, 
                   sessions_left, profile_picture
            FROM students
            WHERE idno LIKE ? OR lastname LIKE ? OR firstname LIKE ? OR course LIKE ?
            LIMIT ? OFFSET ?
        """
        search_term = f"%{search}%"
        params = (search_term, search_term, search_term, search_term, per_page, offset)
        
        # Get students
        students = getprocess(query, params)
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) as total 
            FROM students
            WHERE idno LIKE ? OR lastname LIKE ? OR firstname LIKE ? OR course LIKE ?
        """
        total = getprocess(count_query, (search_term, search_term, search_term, search_term))[0]['total']
        
        return jsonify({
            'success': True,
            'students': students,
            'total': total,
            'page': page,
            'per_page': per_page
        })
        
    except BadRequest as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error fetching students: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    
@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    try:
        query = "SELECT * FROM students WHERE id = ?"
        students = getprocess(query, (student_id,))
        
        if not students or len(students) == 0:
            return jsonify({
                'success': False, 
                'message': f'Student with ID {student_id} not found'
            }), 404
                
        return jsonify({
            'success': True,
            'student': students[0]  # Return single student object
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching student {student_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

    
@app.route('/api/students/<int:student_id>', methods=['GET', 'PUT', 'DELETE'])
def student_operations(student_id):
    try:
        if request.method == 'GET':
            query = "SELECT * FROM students WHERE id = ?"
            student = getprocess(query, (student_id,))
            
            if not student:
                return jsonify({
                    'success': False, 
                    'message': 'Student not found'
                }), 404
                
            return jsonify({
                'success': True,
                'student': student[0]  # Return single student object
            })
            
        elif request.method == 'PUT':
            data = request.get_json()
            required_fields = ['idno', 'lastname', 'firstname', 'course', 'year_level', 'sessions_left']
            
            if not all(field in data for field in required_fields):
                return jsonify({
                    'success': False,
                    'message': 'Missing required fields'
                }), 400
            
            query = """
                UPDATE students 
                SET idno=?, lastname=?, firstname=?, midname=?, 
                    course=?, year_level=?, sessions_left=?
                WHERE id=?
            """
            params = (
                data['idno'], data['lastname'], data['firstname'], 
                data.get('midname', ''), data['course'], 
                data['year_level'], data['sessions_left'], student_id
            )
            
            if postprocess(query, params):
                return jsonify({
                    'success': True,
                    'message': 'Student updated successfully'
                })
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
            
        elif request.method == 'DELETE':
            query = "DELETE FROM students WHERE id = ?"
            if postprocess(query, (student_id,)):
                return jsonify({
                    'success': True,
                    'message': 'Student deleted successfully'
                })
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def edit_student(student_id):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['idno', 'lastname', 'firstname', 'course', 'year_level', 'sessions_left']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Update student
        query = """
            UPDATE students 
            SET idno = ?, lastname = ?, firstname = ?, midname = ?, 
                course = ?, year_level = ?, sessions_left = ?
            WHERE id = ?
        """
        params = (
            data['idno'], data['lastname'], data['firstname'], data.get('midname', ''),
            data['course'], data['year_level'], data['sessions_left'], student_id
        )
        
        if postprocess(query, params):
            return jsonify({'success': True, 'message': 'Student updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Student not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        query = "DELETE FROM students WHERE id = ?"
        if postprocess(query, (student_id,)):
            return jsonify({'success': True, 'message': 'Student deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students/reset-sessions', methods=['POST'])
def reset_all_sessions():
    try:
        query = "UPDATE students SET sessions_left = 30"
        postprocess(query)
        return jsonify({'success': True, 'message': 'All student sessions reset to 30'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'user_username' not in session:
        return jsonify({"success": False, "message": "You need to login first"})

    if 'profile_picture' not in request.files:
        return jsonify({"success": False, "message": "No file selected"})

    file = request.files['profile_picture']

    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"})

    if file:
        filename = f"student_{session['user_username']}.png"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        update_record('students', username=session['user_username'], profile_picture=filename)
        return jsonify({"success": True, "filename": filename})

    return jsonify({"success": False, "message": "An error occurred"})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        idno = request.form.get('idno')
        lastname = request.form.get('lastname')
        firstname = request.form.get('firstname')
        midname = request.form.get('midname')
        course = request.form.get('course')
        year_level = request.form.get('year_level')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate required fields
        if not all([idno, lastname, firstname, course, username, password]):
            flash("All fields are required.", 'error')
            return redirect(url_for('login'))

        existing_student = get_student_by_id(idno)
        if existing_student:
            flash("Student ID already exists.", 'error')
            return redirect(url_for('register'))
        
        existing_email = get_student_by_email(email)
        if existing_email:
            flash("Email already exists.", 'error')
            return redirect(url_for('register'))

        student_data = {
            'idno': idno,
            'lastname': lastname,
            'firstname': firstname,
            'midname': midname,
            'course': course,
            'year_level': year_level,
            'email': email,
            'username': username,
            'password': password,
            'profile_picture': 'default.png'  
        }

        # Add student record to the database
        if add_record('students', **student_data):
            flash("Registration successful!", 'success')
            return redirect(url_for('login'))
        else:
            flash("Registration failed. Try again.", 'error')

    return render_template('client/register.html')


@app.route('/add_student', methods=['POST'])
def add_student():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Extract and validate data
            required_fields = ['idno', 'lastname', 'firstname', 'course', 
                              'year_level', 'username', 'password', 'repeat_password']
            
            if not all(data.get(field) for field in required_fields):
                return jsonify({
                    'success': False,
                    'message': 'All required fields must be filled'
                })

            if data['password'] != data['repeat_password']:
                return jsonify({
                    'success': False,
                    'message': 'Passwords do not match'
                })

            # Check for existing student
            if get_student_by_id(data['idno']):
                return jsonify({
                    'success': False,
                    'message': 'Student ID already exists'
                })
            
            if data.get('email') and get_student_by_email(data['email']):
                return jsonify({
                    'success': False,
                    'message': 'Email already exists'
                })

            # Prepare student data
            student_data = {
                'idno': data['idno'],
                'lastname': data['lastname'],
                'firstname': data['firstname'],
                'midname': data.get('midname', ''),
                'course': data['course'],
                'year_level': data['year_level'],
                'email': data.get('email', ''),
                'username': data['username'],
                'password': data['password'],
                'profile_picture': 'default.png',  # Always set default
                'sessions_left': 30 # Default sessions
            }

            # Add to database
            if add_record('students', **student_data):
                return jsonify({
                    'success': True,
                    'message': 'Student added successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to add student to database'
                })

        except Exception as e:
            print(f"Error adding student: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred while adding the student'
            })

    return jsonify({
        'success': False,
        'message': 'Invalid request method'
    })


@app.route('/get_labs', methods=['GET'])
def get_labs():
    try:
        labs = get_lab_names()
        return jsonify({"success": True, "labs": labs})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/load_section/<section_id>')
def load_section(section_id):
    if section_id == 'dashboard':
        return render_template('client/sections/dashboard.html')
    elif section_id == 'profile':
        student = get_student_by_username(session['user_username'])
        return render_template('client/sections/profile.html', student=student)
    elif section_id == 'announcements':
        return render_template('client/sections/announcements.html')
    elif section_id == 'lab-rules':
        return render_template('client/sections/lab_rules.html')
    elif section_id == 'history':
        return render_template('client/sections/history.html')
    elif section_id == 'reservations':
        return render_template('client/sections/reservations.html')
    elif section_id == 'laboratories':
        return render_template('client/sections/laboratories.html')
    else:
        return "Section not found", 404


    
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    username = session.get('user_username')

    if not username:
        flash("Error: No user is logged in", 'error')
        return redirect(url_for('login'))

    session.pop('user_username', None)

    if username in active_users_dict:
        del active_users_dict[username]
        socketio.emit('update_active_users', list(active_users_dict.keys()))  # Emit active users update

    flash("You Have Been Logged Out", 'info')
    return redirect(url_for('login'))




def format_duration(seconds):
    if not seconds:
        return "N/A"
    duration = timedelta(seconds=seconds)
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"
    
@app.route('/get_session_history/<student_idno>', methods=['GET'])
def get_session_history(student_idno):
    history = get_student_session_history(student_idno)
    return jsonify(history)

@app.route('/get_weekly_usage/<student_idno>', methods=['GET'])
def get_weekly_usage(student_idno):
    formatted_data = get_student_weekly_usage(student_idno)
    print("Formatted Data:", formatted_data)
    return jsonify(formatted_data)

@app.route('/sse/active_users')
def sse_active_users():
    def event_stream():
        while True:
            yield f"data: {json.dumps(len(active_users_dict))}\n\n"
            time.sleep(0.1)

    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers["X-Accel-Buffering"] = "no"  # Disable buffering
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response


def notify_active_users_update():
    """Notify all connected clients about active users update."""
    active_users_count = len(active_users_dict)  

def emit_active_users():
    """Helper function to emit the active users count."""
    active_users_count = len(active_users_dict)  
    print(f"Emitting active users count: {active_users_count}") 
    socketio.emit('update_active_users', active_users_count)

@app.route('/dashboard')
def dashboard():
    pagetitle = 'Dashboard'
    if 'admin_username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('admin_login'))

    # Get all necessary data
    admin_username = session.get('admin_username')
    active_students = list(active_users_dict.keys())
    labs = get_lab_names() or []  # Ensure labs is always at least an empty list
    
    print(f"DEBUG: Retrieved {len(labs)} labs for dashboard")
    for lab in labs:
        print(f"DEBUG: Lab ID: {lab.get('id')}, Name: {lab.get('lab_name')}")
        
    laboratories = get_count_laboratories()
    student_count = get_count_students()
    active_students_count = len(active_students)
    
    # Pagination for students
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    # Search functionality
    search_term = request.args.get('search', '')
    
    # Get students with search filter
    if search_term:
        students = getprocess("""
            SELECT id, idno, lastname, firstname, midname, course, year_level, sessions_left
            FROM students
            WHERE idno LIKE ? OR lastname LIKE ? OR firstname LIKE ? OR course LIKE ?
            LIMIT ? OFFSET ?
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", per_page, offset))
        
        total_students = getprocess("""
            SELECT COUNT(*) as count FROM students
            WHERE idno LIKE ? OR lastname LIKE ? OR firstname LIKE ? OR course LIKE ?
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))[0]['count']
    else:
        students = get_paginated_students(offset, per_page)
        total_students = get_count_students()
    
    total_pages = (total_students + per_page - 1) // per_page
    
    # Other data
    admin_firstname = session.get('admin_firstname')
    reservations = get_all_reservations()
    today = datetime.now().strftime('%Y-%m-%d')

    return render_template('admin/dashboard.html',
                         student_count=student_count,
                         active_students=active_students,
                         laboratories=laboratories,
                         labs=labs,
                         admin_username=admin_username,
                         pagetitle=pagetitle,
                         active_students_count=active_students_count,
                         students=students,
                         page=page,
                         total_pages=total_pages,
                         reservations=reservations,
                         today=today,
                         admin_firstname=admin_firstname,
                         search_term=search_term,
                         current_page='dashboard')


    
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    pagetitle = 'Administrator Login'
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Username and Password are required", 'error')
            return redirect(url_for('admin_login'))

        admin = get_admin_user_by_credentials(username, password)

        if admin:
            # Set session variables
            session['admin_username'] = username
            session['admin_firstname'] = admin['admin_firstname']  # Store the first name in the session
            session.permanent = True  # Make the session persistent
            flash("Login successful!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin/adminlogin.html', pagetitle=pagetitle)

@app.route('/admin/super-secret-admin-register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        admin_username = request.form.get('admin_username')
        password = request.form.get('password')
        email = request.form.get('email')
        name = request.form.get('name')

        if secret_key != "kimperor123":
            flash("Unauthorized access!", 'error')
            return render_template('admin/adminregister.html')
        if not admin_username.startswith("admin-"):
            flash("Invalid admin username format!", 'error')
            return render_template('admin/adminregister.html')
        existing_admin = get_admin_by_username(admin_username)
        if existing_admin:
            flash("Admin username already exists!", 'error')
            return render_template('admin/adminregister.html')
        name_parts = name.strip().split(maxsplit=1)  
        admin_firstname = name_parts[0] if len(name_parts) > 0 else ""
        admin_lastname = name_parts[1] if len(name_parts) > 1 else ""

        if add_record('admin_users', 
                      admin_username=admin_username, 
                      password=password, 
                      email=email, 
                      name=name, 
                      admin_firstname=admin_firstname, 
                      admin_lastname=admin_lastname):
            flash("Admin registered successfully!", 'success')
            return redirect(url_for('admin_login'))
        else:
            flash("Error registering admin. Please try again.", 'error')
            return render_template('admin/adminregister.html')

    return render_template('admin/adminregister.html')


@app.route('/adminLogout')
def adminLogout():
    if 'admin_username' in session:
        session.pop('admin_username', None)  
        flash("Admin has been logged out.", 'info')
    return redirect(url_for('admin_login'))



@app.route('/admin/settings')
def admin_settings():
    print("Admin Settings Route Accessed")
    return render_template('admin/admin_settings.html')

@app.route('/create_announcement', methods=['POST'])
def create_announcement():
    data = request.get_json()
    announcement_text = data.get('announcement_text')
    admin_username = session.get('admin_username')

    if not admin_username:
        return jsonify({"success": False, "message": "Admin not logged in"})

    if not announcement_text:
        return jsonify({"success": False, "message": "Missing announcement text"})

    try:
        # Add the announcement to the database
        query = """
            INSERT INTO announcements (admin_username, announcement_text, announcement_date)
            VALUES (?, ?, ?);
        """
        announcement_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (admin_username, announcement_text, announcement_date))
        announcement_id = cursor.lastrowid  # Get the ID of the newly inserted announcement

        # Fetch all student IDs to create notifications
        student_query = "SELECT id FROM students;"
        cursor.execute(student_query)
        students = cursor.fetchall()

        # Insert a notification for each student
        for student in students:
            notification_query = """
                INSERT INTO notifications (student_id, announcement_id, is_read)
                VALUES (?, ?, ?);
            """
            cursor.execute(notification_query, (student['id'], announcement_id, False))

        conn.commit()
        cursor.close()
        conn.close()

        # Emit a Socket.IO event to notify all clients
        socketio.emit('new_announcement', {
            'id': announcement_id,
            'admin_username': admin_username,
            'announcement_text': announcement_text,
            'announcement_date': announcement_date,
            'is_read': False  # Mark as unread by default
        })
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error creating announcement: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/get_announcement/<int:announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    try:
        announcement = get_announcement_by_id(announcement_id)  # Ensure this function exists
        return jsonify(announcement)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    

@app.route('/get_announcements', methods=['GET'])
def get_announcements():
    try:
        announcements = get_all_announcements() 
        return jsonify(announcements)  
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/update_announcement/<int:announcement_id>', methods=['POST'])
def update_announcement(announcement_id):
    data = request.get_json()
    announcement_text = data.get('announcement_text')

    if not announcement_text:
        return jsonify({"success": False, "message": "Missing announcement text"})

    try:
        success = update_record(
            table="announcements",
            id=announcement_id,
            announcement_text=announcement_text,
            announcement_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        if success:
            # Emit the updated announcement to all clients
            socketio.emit('announcement_updated', {
                'id': announcement_id,
                'announcement_text': announcement_text,
                'announcement_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'admin_username': 'Admin'  # Replace with actual admin username
            })
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to update announcement"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# Delete Announcement
@app.route('/delete_announcement/<int:announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    try:
        success = delete_record(table="announcements", id=announcement_id)
        if success:
            # Emit a Socket.IO event to notify all clients
            socketio.emit('announcement_deleted', {'id': announcement_id})
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to delete announcement"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    

def execute_query(query, params=None):
    try:
        # Connect to the SQLite database (replace with your actual database file)
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()

        # Execute the query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        conn.commit()  # Commit the transaction

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return True  # Query executed successfully
    except Exception as e:
        print(f"Error executing query: {e}")
        return False  # Query failed

@app.route('/mark_notification_as_read', methods=['POST'])
def mark_notification_as_read():
    data = request.get_json()
    notification_id = data.get('notification_id')
    if not notification_id:
        return jsonify({"success": False, "message": "Notification ID is required"})

    try:
        query = """
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = ?;
        """
        success = execute_query(query, (notification_id,))

        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to mark notification as read"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/get_unread_notifications', methods=['GET'])
def get_unread_notifications():
    student_id = session.get('student_id')  # Ensure the student is logged in and their ID is stored in the session
    if not student_id:
        return jsonify({"success": False, "message": "Student not logged in"})

    try:
        query = """
            SELECT n.id, a.admin_username, a.announcement_text, a.announcement_date, n.is_read
            FROM notifications n
            JOIN announcements a ON n.announcement_id = a.id
            WHERE n.student_id = ? AND n.is_read = FALSE
            ORDER BY a.announcement_date DESC;
        """
        unread_notifications = getprocess(query, (student_id,))
        return jsonify({"success": True, "data": unread_notifications})  # Return as an array
    except Exception as e:
        print(f"Error fetching unread notifications: {e}")
        return jsonify({"success": False, "message": str(e)})
    

@app.route('/activity_breakdown', methods=['GET'])
def activity_breakdown():
    if 'student_idno' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    student_idno = session['student_idno']
    activity_data = get_student_activity_breakdown(student_idno)
    return jsonify(activity_data)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    print("Client connected:", request.sid)
    emit('update_active_users', list(active_users_dict.keys()))

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print("Client disconnected:", request.sid)


@app.route('/get_user_count')
def get_user_count():
    active_students = list(active_users_dict.keys())  # Get list of active students
    active_students_count = len(active_students)  # Count active students
    return jsonify(student_count=get_count_students(), active_students_count=active_students_count)


def emit_active_users():
    """ Helper function to emit the active users count """
    active_users = list(active_users_dict.keys()) 
    print(f"Emitting active users: {active_users}") 
    socketio.emit('update_active_users', active_users)

@app.route('/get_leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        # Only fetch top 5 students for the leaderboard
        leaderboard = get_points_leaderboard(limit=5)
        
        return jsonify({
            "success": True,
            "leaderboard": leaderboard
        })

    except Exception as e:
        print(f"Error fetching leaderboard: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "Failed to fetch leaderboard data",
            "leaderboard": []
        }), 500

@app.route('/award_points', methods=['POST'])
def award_points():
    """Award 1 point to a student for a completed session"""
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    student_idno = data.get('student_idno')
    reservation_id = data.get('reservation_id')
    reason = data.get('reason', 'Reward for lab session')

    if not student_idno:
        return jsonify({"success": False, "message": "Student ID required"}), 400

    try:
        # Verify the student exists
        student = get_student_by_idno(student_idno)
        if not student:
            return jsonify({"success": False, "message": "Student not found"}), 404
            
        # Check if points already awarded for this reservation
        if reservation_id:
            points_awarded = getprocess(
                "SELECT 1 FROM points_history WHERE reason = ? AND student_idno = ?",
                (f"Reward for reservation {reservation_id}", student_idno)
            )
            if points_awarded:
                return jsonify({
                    "success": False, 
                    "message": "Points already awarded for this session"
                }), 400
        
        # Award 1 point (auto-conversion happens in add_points_to_student)
        result = add_points_to_student(
            student_idno=student_idno,
            points=1,
            reason=f"Reward for reservation {reservation_id}" if reservation_id else reason,
            awarded_by=session['admin_username']
        )
        
        # Extract values from the result dictionary
        new_points = result['new_points']
        additional_sessions = result['additional_sessions']
        remaining_points = result['remaining_points']
        sessions_left = result['total_sessions']
        
        # Mark reservation as having points awarded if applicable
        if reservation_id:
            try:
                postprocess(
                    "UPDATE reservations SET points_awarded = 1 WHERE id = ?",
                    (reservation_id,)
                )
            except Exception as e:
                print(f"Warning: Could not mark reservation as having points awarded: {e}")
                # Continue anyway - this is not critical
        
        # Prepare success message
        message = "Successfully awarded 1 point."
        if additional_sessions > 0:
            message += f" Earned {additional_sessions} new session(s)!"
        message += f" {remaining_points} points remaining."

        return jsonify({
            "success": True,
            "message": message,
            "points": new_points,
            "remaining_points": remaining_points,
            "sessions_added": additional_sessions,
            "sessions_left": sessions_left
        })

    except Exception as e:
        print(f"Error awarding points: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/convert_points', methods=['POST'])
def convert_points():
    """Convert available points to sessions (3 points = 1 session)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        # Get student ID associated with this user
        student = getprocess(
            "SELECT idno FROM students WHERE user_id = ?",
            (user_id,)
        )
        if not student:
            return jsonify({"success": False, "message": "Student not found"}), 404
        
        student_idno = student[0]['idno']
        
        # Perform conversion
        result = convert_points_to_sessions(student_idno)
        
        sessions_added = result['sessions_added']
        remaining_points = result['remaining_points']
        total_sessions = result['total_sessions']
        
        if sessions_added == 0:
            return jsonify({
                "success": False,
                "message": "Not enough points to convert (need at least 3)",
                "current_points": remaining_points,
                "total_sessions": total_sessions
            }), 400

        return jsonify({
            "success": True,
            "message": f"Converted {sessions_added * 3} points to {sessions_added} session(s)",
            "sessions_added": sessions_added,
            "remaining_points": remaining_points,
            "total_sessions": total_sessions
        })

    except Exception as e:
        print(f"Error converting points: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/points_balance', methods=['GET'])
def points_balance():
    """Get current points balance"""
    if 'student_idno' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        student_idno = session.get('student_idno')
        
        # Get student points
        points_data = getprocess(
            """SELECT points 
               FROM student_points
               WHERE student_idno = ?""",
            (student_idno,)
        )
        
        if not points_data or len(points_data) == 0:
            return jsonify({
                "success": True,
                "points": 0,
                "message": "No points record found"
            })
        
        return jsonify({
            "success": True,
            "points": points_data[0]['points']
        })

    except Exception as e:
        print(f"Error getting points balance: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/get_student_points', methods=['GET'])
def get_student_points():
    try:
        # Get current user ID
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not logged in'})
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current points for the student
        cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            points = result[0]
            return jsonify({'success': True, 'points': points})
        else:
            return jsonify({'success': False, 'error': 'User not found'})
    
    except Exception as e:
        print(f"Error getting student points: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve student points'})
    finally:
        if conn:
            conn.close()

@app.route('/points_history', methods=['GET'])
def points_history():
    """Get points transaction history"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        history = getprocess(
            """SELECT 
                  ph.points_change as points,
                  ph.reason,
                  ph.awarded_by,
                  ph.date
               FROM points_history ph
               JOIN students s ON ph.student_idno = s.idno
               WHERE s.user_id = ?
               ORDER BY ph.date DESC""",
            (user_id,)
        )
        
        return jsonify({
            "success": True,
            "history": history or []
        })

    except Exception as e:
        print(f"Error getting points history: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/create_lab_resource', methods=['POST'])
def create_lab_resource():
    try:
        # Make sure user is admin
        if session.get('admin_username') is None:
            return jsonify({"success": False, "message": "Unauthorized access"}), 401
        
        data = request.json
        title = data.get('title')
        content = data.get('content')
        link = data.get('link')
        
        # Validate input
        if not all([title, content, link]):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        # Add to database
        postprocess(
            """INSERT INTO lab_resources (title, content, link, created_by) 
               VALUES (?, ?, ?, ?)""",
            (title, content, link, session.get('admin_username'))
        )
        
        # Notify clients of new resource via Socket.IO
        socketio.emit('new_lab_resource', {
            'title': title,
            'content': content,
            'link': link,
            'created_by': session.get('admin_username'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return jsonify({"success": True, "message": "Lab resource created successfully"})
    
    except Exception as e:
        print(f"Error creating lab resource: {str(e)}")
        return jsonify({"success": False, "message": f"Failed to create lab resource: {str(e)}"}), 500

@app.route('/get_lab_resources', methods=['GET'])
def get_lab_resources():
    """Get lab resources for admin panel"""
    try:
        # For admin panel, always get fresh data
        resources = getprocess(
            """SELECT id, title, content, link, created_at, created_by 
               FROM lab_resources 
               ORDER BY created_at DESC"""
        )
        
        # Format resources consistently
        for resource in resources:
            if 'created_at' in resource and resource['created_at'] and not isinstance(resource['created_at'], str):
                resource['created_at'] = resource['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "resources": resources or []})
    
    except Exception as e:
        print(f"Error fetching lab resources: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Failed to fetch lab resources: {str(e)}",
            "resources": []
        }), 500

@app.route('/delete_lab_resource/<int:resource_id>', methods=['DELETE'])
def delete_lab_resource(resource_id):
    try:
        # Make sure user is admin
        if session.get('admin_username') is None:
            return jsonify({"success": False, "message": "Unauthorized access"}), 401
        
        # Delete the resource
        postprocess(
            "DELETE FROM lab_resources WHERE id = ?",
            (resource_id,)
        )
        
        # Notify clients of deletion via Socket.IO
        socketio.emit('lab_resource_deleted', {
            'resource_id': resource_id
        })
        
        return jsonify({"success": True, "message": "Lab resource deleted successfully"})
    
    except Exception as e:
        print(f"Error deleting lab resource: {str(e)}")
        return jsonify({"success": False, "message": f"Failed to delete lab resource: {str(e)}"}), 500

@app.route('/edit_resource/<int:resource_id>', methods=['GET', 'POST'])
def edit_resource(resource_id):
    try:
        # Check if user is a student or admin
        if not (session.get('student_idno') or session.get('admin_username')):
            return redirect(url_for('login'))
        
        # If it's a POST request, update the resource
        if request.method == 'POST':
            # Only admins can edit resources
            if not session.get('admin_username'):
                return jsonify({"success": False, "message": "Unauthorized access"}), 401
            
            data = request.json
            title = data.get('title')
            content = data.get('content')
            link = data.get('link')
            
            # Validate input
            if not all([title, content, link]):
                return jsonify({"success": False, "message": "All fields are required"}), 400
            
            # Update the resource
            postprocess(
                """UPDATE lab_resources 
                   SET title = ?, content = ?, link = ?
                   WHERE id = ?""",
                (title, content, link, resource_id)
            )
            
            # Notify clients of updated resource via Socket.IO
            socketio.emit('resource_updated', {
                'resource_id': resource_id,
                'title': title,
                'content': content,
                'link': link,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            if session.get('admin_username'):
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        
        # GET request - retrieve the resource
        resource = getprocess(
            """SELECT id, title, content, link, created_at, created_by 
               FROM lab_resources 
               WHERE id = ?""",
            (resource_id,),
            fetch_one=True
        )
        
        if not resource:
            flash("Resource not found", "error")
            if session.get('admin_username'):
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        
        # If it's a regular user, show the edit form
        template = 'admin/edit_resource.html' if session.get('admin_username') else 'client/edit_resource.html'
        return render_template(template, resource=resource)
    
    except Exception as e:
        print(f"Error editing lab resource: {str(e)}")
        flash(f"An error occurred: {str(e)}", "error")
        if session.get('admin_username'):
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

@app.route('/api/get_lab_resources', methods=['GET'])
def api_get_lab_resources():
    """
    Get all lab resources with optimized data format for the student dashboard
    """
    try:
        print("API endpoint /api/get_lab_resources called")
        
        # Query the database for resources
        resources = getprocess(
            """SELECT id, title, content, link, created_at as timestamp, created_by as uploader 
               FROM lab_resources 
               ORDER BY created_at DESC"""
        )
        
        # Process resources to ensure proper formatting
        formatted_resources = []
        
        if resources:
            for resource in resources:
                # Ensure dates are properly formatted
                if 'timestamp' in resource and resource['timestamp']:
                    # Convert datetime to string if it's not already
                    if not isinstance(resource['timestamp'], str):
                        resource['timestamp'] = resource['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Limit content length for performance
                if 'content' in resource and len(resource['content']) > 500:
                    resource['content'] = resource['content'][:500] + '...'
                    
                formatted_resources.append(resource)
        
        # Create the response
        response_data = {
            "success": True, 
            "resources": formatted_resources,
            "count": len(formatted_resources)
        }
        
        print(f"Returning {len(formatted_resources)} resources")
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error fetching lab resources: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Failed to fetch lab resources: {str(e)}",
            "resources": []
        }), 500

@app.route('/create-sample-resource', methods=['GET'])
def create_sample_resource():
    """Create a sample resource for testing"""
    try:
        # Add a sample resource to the database
        postprocess(
            """INSERT INTO lab_resources (title, content, link, created_by) 
               VALUES (?, ?, ?, ?)""",
            (
                "Sample Programming Resource", 
                "This is a sample resource to help students with programming concepts. It includes tutorials and examples to help you understand key concepts.", 
                "https://github.com/microsoft/vscode", 
                "Admin"
            )
        )
        
        # Add another sample resource
        postprocess(
            """INSERT INTO lab_resources (title, content, link, created_by) 
               VALUES (?, ?, ?, ?)""",
            (
                "Data Structures Guide", 
                "A comprehensive guide to understanding data structures and algorithms. This resource covers arrays, linked lists, trees, and graphs with practical examples.", 
                "https://www.geeksforgeeks.org/data-structures/", 
                "Admin"
            )
        )
        
        # Notify clients of new resources via Socket.IO
        socketio.emit('new_lab_resource', {
            'title': "Sample Resources Added",
            'content': "Sample resources have been added for testing",
            'link': "#",
            'created_by': "System",
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return "Sample resources created successfully. <a href='/student_dashboard'>Go to dashboard</a>"
    
    except Exception as e:
        print(f"Error creating sample resources: {str(e)}")
        return f"Failed to create sample resources: {str(e)}"

# Lab Management Routes
@app.route('/lab_management')
def lab_management():
    if 'admin_username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('admin_login'))
    
    # Get all labs
    labs = get_lab_names()
    
    return render_template('admin/lab_management.html', 
                          labs=labs,
                          admin_username=session.get('admin_username'),
                          admin_firstname=session.get('admin_firstname'),
                          current_page='lab_management')

@app.route('/api/lab_computers/<int:lab_id>', methods=['GET'])
def api_lab_computers(lab_id):
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    # Initialize computers if they don't exist
    initialize_lab_computers(lab_id)
    
    # Get computers for the lab
    computers = get_lab_computers(lab_id)
    
    # Get lab name
    lab_name = "Unknown Lab"
    labs = get_lab_names()
    for lab in labs:
        if lab['id'] == lab_id:
            lab_name = lab['lab_name']
            break
    
    return jsonify({
        "success": True, 
        "lab_id": lab_id,
        "lab_name": lab_name,
        "computers": computers
    })

@app.route('/api/computer_status/<int:computer_id>', methods=['PUT'])
def api_update_computer_status(computer_id):
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json()
    status = data.get('status')
    student_idno = data.get('student_idno')
    
    if not status or status not in ['Available', 'In Use', 'Unavailable']:
        return jsonify({"success": False, "message": "Invalid status"}), 400
    
    # Update computer status
    success = update_computer_status(computer_id, status, student_idno)
    
    if success:
        # Get updated computer info
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT lc.*, s.firstname, s.lastname
        FROM lab_computers lc
        LEFT JOIN students s ON lc.student_idno = s.idno
        WHERE lc.id = ?
        ''', (computer_id,))
        computer = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Computer status updated to {status}",
            "computer": dict(computer) if computer else None
        })
    else:
        return jsonify({"success": False, "message": "Failed to update computer status"}), 500

# Lab Schedule Routes
@app.route('/lab_schedule')
def lab_schedule():
    if 'admin_username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('admin_login'))
    
    # Get all labs
    labs = get_lab_names()
    
    return render_template('admin/lab_schedule.html', 
                          labs=labs,
                          admin_username=session.get('admin_username'),
                          admin_firstname=session.get('admin_firstname'),
                          current_page='lab_schedule')

@app.route('/api/lab_schedules/<int:lab_id>', methods=['GET'])
def api_lab_schedules(lab_id):
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        # Get day parameter if provided
        day_of_week = request.args.get('day')
        
        print(f"DEBUG: Fetching schedules for lab {lab_id}, day: {day_of_week if day_of_week else 'All days'}")
        
        # Get schedules for the lab
        schedules = get_lab_schedules(lab_id, day_of_week)
        
        if not schedules and day_of_week:
            print(f"DEBUG: No schedules found for lab {lab_id} on {day_of_week}")
        
        # Get lab name
        lab_name = "Unknown Lab"
        labs = get_lab_names()
        for lab in labs:
            if lab['id'] == lab_id:
                lab_name = lab['lab_name']
                break
        
        print(f"DEBUG: Returning {len(schedules)} schedules for lab {lab_id} ({lab_name})")
        
        return jsonify({
            "success": True, 
            "lab_id": lab_id,
            "lab_name": lab_name,
            "schedules": schedules,
            "day": day_of_week
        })
    except Exception as e:
        import traceback
        print(f"DEBUG: Error fetching lab schedules: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False, 
            "message": f"Error fetching schedules: {str(e)}"
        }), 500

@app.route('/api/lab_schedules', methods=['POST'])
def api_add_lab_schedule():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json()
    lab_id = data.get('lab_id')
    day_of_week = data.get('day_of_week')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    status = data.get('status')
    subject_code = data.get('subject_code')
    subject_name = data.get('subject_name')
    reason = data.get('reason')
    schedule_id = data.get('schedule_id')
    
    # Validate required fields
    if not all([lab_id, day_of_week, start_time, end_time, status]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Add or update schedule
    result_id = add_or_update_lab_schedule(
        lab_id, day_of_week, start_time, end_time, status, 
        subject_code, subject_name, reason, schedule_id
    )
    
    if result_id:
        return jsonify({
            "success": True, 
            "message": "Schedule saved successfully",
            "schedule_id": result_id
        })
    else:
        return jsonify({"success": False, "message": "Failed to save schedule"}), 500

@app.route('/api/lab_schedules/<int:schedule_id>', methods=['DELETE'])
def api_delete_lab_schedule(schedule_id):
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    # Delete schedule
    success = delete_lab_schedule(schedule_id)
    
    if success:
        return jsonify({
            "success": True, 
            "message": "Schedule deleted successfully"
        })
    else:
        return jsonify({"success": False, "message": "Failed to delete schedule"}), 500

@app.route('/import_default_schedules', methods=['POST'])
def import_default_schedules():
    if 'admin_username' not in session:
        print("DEBUG: Unauthorized access to import_default_schedules route")
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        print("DEBUG: Attempting to import default schedules")
        
        # First create or verify the laboratories table
        if not create_and_populate_laboratories():
            return jsonify({
                "success": False, 
                "message": "Failed to initialize laboratories table"
            }), 500
        
        # Check if labs with IDs used in default schedules exist
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Get all lab IDs and names
        cursor.execute('SELECT id, lab_name FROM laboratories')
        lab_records = cursor.fetchall()
        existing_lab_ids = [record[0] for record in lab_records]
        lab_name_to_id = {record[1].replace(' ', ''): record[0] for record in lab_records}
        
        print(f"DEBUG: Existing lab IDs: {existing_lab_ids}")
        print(f"DEBUG: Lab name to ID mapping: {lab_name_to_id}")
        
        # Clear existing schedules
        print("DEBUG: Clearing existing schedules")
        cursor.execute('DELETE FROM lab_schedules')
        conn.commit()
        conn.close()
        
        # Now import default schedules with corrected lab IDs
        # First, verify if specific lab IDs (542, 544, 524) exist
        # If not, we'll use the IDs from lab names (Lab542, Lab544, Lab524)
        
        # Map lab names to IDs if they exist
        lab_mappings = {}
        if 542 not in existing_lab_ids and 'Lab542' in lab_name_to_id:
            lab_mappings[542] = lab_name_to_id['Lab542']
        
        if 544 not in existing_lab_ids and 'Lab544' in lab_name_to_id:
            lab_mappings[544] = lab_name_to_id['Lab544']
            
        if 524 not in existing_lab_ids and 'Lab524' in lab_name_to_id:
            lab_mappings[524] = lab_name_to_id['Lab524']
            
        print(f"DEBUG: Lab ID mappings: {lab_mappings}")
        
        # Now import default schedules with potentially corrected lab IDs
        success = import_default_lab_schedules(lab_mappings)
        
        if success:
            print("DEBUG: Default schedules imported successfully")
            
            # Initialize computers for all labs to ensure they exist
            initialize_all_labs_computers()
            
            return jsonify({
                "success": True, 
                "message": "Default schedules imported successfully"
            })
        else:
            print("DEBUG: Failed to import default schedules")
            return jsonify({
                "success": False, 
                "message": "Failed to import default schedules. An error occurred during import."
            }), 500
    except Exception as e:
        import traceback
        print(f"DEBUG: Error in import_default_schedules: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False, 
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route('/api/lab_schedules/<int:schedule_id>', methods=['GET'])
def api_get_lab_schedule(schedule_id):
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        # Get database connection
        conn = sqlite3.connect('student.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get schedule by ID
        cursor.execute('''
        SELECT * FROM lab_schedules WHERE id = ?
        ''', (schedule_id,))
        
        schedule = cursor.fetchone()
        
        if not schedule:
            return jsonify({"success": False, "message": "Schedule not found"}), 404
        
        # Convert to dict
        schedule_dict = dict(schedule)
        
        # Get lab name
        cursor.execute('SELECT lab_name FROM laboratories WHERE id = ?', (schedule_dict['lab_id'],))
        lab = cursor.fetchone()
        
        if lab:
            schedule_dict['lab_name'] = lab['lab_name']
        else:
            schedule_dict['lab_name'] = "Unknown Lab"
        
        return jsonify({
            "success": True,
            "schedule": schedule_dict
        })
    except Exception as e:
        import traceback
        print(f"DEBUG: Error fetching lab schedule: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False, 
            "message": f"Error fetching schedule: {str(e)}"
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Route to get available time slots for a lab on a specific date
@app.route('/get_available_time_slots', methods=['GET'])
def get_available_time_slots_route():
    lab_id = request.args.get('lab_id')
    reservation_date = request.args.get('date')
    
    if not lab_id or not reservation_date:
        return jsonify({'success': False, 'message': 'Lab ID and date are required'}), 400
    
    try:
        # Convert reservation_date to datetime for validation
        date_obj = datetime.strptime(reservation_date, '%Y-%m-%d')
        
        # Check if the date is in the past
        if date_obj.date() < datetime.now().date():
            return jsonify({'success': False, 'message': 'Cannot make reservations for past dates'}), 400
        
        # Get available time slots
        time_slots = get_available_time_slots(lab_id, reservation_date)
        
        return jsonify({
            'success': True,
            'time_slots': time_slots
        })
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format (YYYY-MM-DD expected)'}), 400
    except Exception as e:
        print(f"Error getting available time slots: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Route to get available computers for a lab
@app.route('/get_available_computers', methods=['GET'])
def get_available_computers_route():
    lab_id = request.args.get('lab_id')
    
    if not lab_id:
        return jsonify({'success': False, 'message': 'Lab ID is required'}), 400
    
    try:
        # Get available computers
        computers = get_available_computers(lab_id)
        
        return jsonify({
            'success': True,
            'computers': computers
        })
    except Exception as e:
        print(f"Error getting available computers: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Route to create a student reservation
@app.route('/create_student_reservation', methods=['POST'])
def create_student_reservation_route():
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        data = request.json
        student_idno = session.get('student_idno')
        lab_id = data.get('lab_id')
        computer_number = data.get('computer_id')  # This is actually the computer number, not ID
        purpose = data.get('purpose')
        reservation_date = data.get('reservation_date')
        time_slot = data.get('time_slot')
        
        print(f"Received reservation data: {data}")
        
        # Validate required fields
        missing_fields = []
        if not lab_id:
            missing_fields.append("Laboratory")
        if not computer_number:
            missing_fields.append("Computer")
        if not purpose:
            missing_fields.append("Purpose")
        if not reservation_date:
            missing_fields.append("Reservation date")
        if not time_slot:
            missing_fields.append("Time slot")
            
        if missing_fields:
            error_message = f"Missing required fields: {', '.join(missing_fields)}"
            print(error_message)
            return jsonify({'success': False, 'message': error_message}), 400
        
        # Check if the student has enough sessions left
        student = get_student_by_idno(student_idno)
        if not student:
            return jsonify({'success': False, 'message': 'Student record not found'}), 404
            
        if student['sessions_left'] <= 0:
            return jsonify({'success': False, 'message': 'You have no sessions left'}), 400
        
        # Check if the student already has a pending reservation
        if has_pending_student_reservation(student_idno):
            return jsonify({'success': False, 'message': 'You already have a pending reservation'}), 400
        
        # Get the actual computer ID from the computer number
        computer = get_computer_by_number(lab_id, computer_number)
        if not computer:
            return jsonify({'success': False, 'message': f'Computer #{computer_number} not found in lab {lab_id}'}), 404
        
        computer_id = computer['id']
        
        # Create the reservation
        success = create_student_reservation(
            student_idno, lab_id, computer_id, purpose, reservation_date, time_slot
        )
        
        if success:
            # Get the student name for notification
            student_name = f"{student['firstname']} {student['midname'] if student['midname'] else ''} {student['lastname']}".strip()
            
            # Get lab name for notification
            lab = getprocess("SELECT lab_name FROM laboratories WHERE id = ?", (lab_id,))
            lab_name = lab[0]['lab_name'] if lab and len(lab) > 0 else "Unknown Lab"
            
            # Get computer number for notification - use the original computer number
            computer_number_display = computer_number  # Use the selected computer number
            
            # Emit a socket.io event for real-time update
            socketio.emit('new_student_reservation', {
                'student_idno': student_idno,
                'student_name': student_name,
                'lab_id': lab_id,
                'lab_name': lab_name,
                'computer_id': computer_id,
                'computer_number': computer_number_display,
                'purpose': purpose,
                'reservation_date': reservation_date,
                'time_slot': time_slot
            })
            
            return jsonify({
                'success': True,
                'message': 'Reservation created successfully'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to create reservation'}), 500
    except Exception as e:
        print(f"Error creating reservation: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Route to get student reservations
@app.route('/get_student_reservations', methods=['GET'])
def get_student_reservations_route():
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    student_idno = session.get('student_idno')
    
    try:
        # Get student reservations
        reservations = get_student_reservations(student_idno)
        
        return jsonify({
            'success': True,
            'reservations': reservations
        })
    except Exception as e:
        print(f"Error getting student reservations: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Student version of lab schedules API
@app.route('/api/student/lab_schedules/<int:lab_id>', methods=['GET'])
def api_student_lab_schedules(lab_id):
    try:
        # Get day parameter if provided
        day_of_week = request.args.get('day')
        
        # Get schedules for the lab
        schedules = get_lab_schedules(lab_id, day_of_week)
        
        # Get lab name
        lab_name = "Unknown Lab"
        labs = get_lab_names()
        for lab in labs:
            if lab['id'] == lab_id:
                lab_name = lab['lab_name']
                break
        
        return jsonify({
            "success": True, 
            "lab_id": lab_id,
            "lab_name": lab_name,
            "schedules": schedules,
            "day": day_of_week
        })
    except Exception as e:
        print(f"Error fetching lab schedules for student: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Error fetching schedules: {str(e)}"
        }), 500

@app.route('/get_points_history', methods=['GET'])
def get_points_history():
    # Dummy data for now
    return jsonify({
        'success': True,
        'history': []
    })

# Route to update student reservation
@app.route('/update_student_reservation', methods=['PUT'])
def update_student_reservation():
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        data = request.json
        reservation_id = data.get('reservation_id')
        purpose = data.get('purpose')
        
        if not reservation_id:
            return jsonify({'success': False, 'message': 'Reservation ID is required'}), 400
        
        # Check if the reservation exists and belongs to the student
        reservation = getprocess(
            "SELECT * FROM student_reservation WHERE id = ? AND student_idno = ?", 
            (reservation_id, session.get('student_idno'))
        )
        
        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found or unauthorized'}), 404
        
        # Check if the reservation is in Pending status (only pending can be updated)
        if reservation[0]['status'] != 'Pending':
            return jsonify({'success': False, 'message': 'Only pending reservations can be updated'}), 400
        
        # Update the reservation purpose
        if purpose:
            success = postprocess(
                "UPDATE student_reservation SET purpose = ? WHERE id = ?",
                (purpose, reservation_id)
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Reservation updated successfully'
                })
            else:
                return jsonify({'success': False, 'message': 'Failed to update reservation'}), 500
        else:
            return jsonify({'success': False, 'message': 'No fields to update'}), 400
            
    except Exception as e:
        print(f"Error updating reservation: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Route to delete student reservation
@app.route('/delete_student_reservation/<int:reservation_id>', methods=['DELETE'])
def delete_student_reservation(reservation_id):
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        # Check if the reservation exists and belongs to the student
        reservation = getprocess(
            "SELECT * FROM student_reservation WHERE id = ? AND student_idno = ?", 
            (reservation_id, session.get('student_idno'))
        )
        
        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found or unauthorized'}), 404
        
        # Check if the reservation is in Pending status (only pending can be deleted)
        if reservation[0]['status'] != 'Pending':
            return jsonify({'success': False, 'message': 'Only pending reservations can be deleted'}), 400
        
        # Delete the reservation
        success = postprocess(
            "DELETE FROM student_reservation WHERE id = ?",
            (reservation_id,)
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Reservation deleted successfully'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to delete reservation'}), 500
            
    except Exception as e:
        print(f"Error deleting reservation: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Route to get a single student reservation
@app.route('/get_reservation/<int:reservation_id>', methods=['GET'])
def get_single_reservation(reservation_id):
    if 'student_idno' not in session and 'admin_username' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        # If admin is requesting, allow any reservation
        if 'admin_username' in session:
            query = """
                SELECT r.*, l.lab_name, COALESCE(lc.computer_number, 'Unknown') as computer_name,
                s.idno as student_idno, s.firstname || ' ' || s.lastname as student_name
                FROM reservations r
                JOIN students s ON r.student_idno = s.idno
                JOIN laboratories l ON r.lab_id = l.id
                LEFT JOIN lab_computers lc ON r.computer_id = lc.id
                WHERE r.id = ?
            """
            params = (reservation_id,)
        else:
            # Check if the reservation exists and belongs to the student
            student_idno = session.get('student_idno')
            query = """
                SELECT r.*, l.lab_name, COALESCE(lc.computer_number, 'Unknown') as computer_name,
                s.idno as student_idno, s.firstname || ' ' || s.lastname as student_name
                FROM reservations r
                JOIN students s ON r.student_idno = s.idno
                JOIN laboratories l ON r.lab_id = l.id
                LEFT JOIN lab_computers lc ON r.computer_id = lc.id
                WHERE r.id = ? AND r.student_idno = ?
            """
            params = (reservation_id, student_idno)
        
        reservation = getprocess(query, params)
        
        if not reservation or len(reservation) == 0:
            return jsonify({'success': False, 'message': 'Reservation not found or unauthorized'}), 404
        
        return jsonify({
            'success': True,
            'reservation': reservation[0]
        })
            
    except Exception as e:
        print(f"Error getting reservation: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/get_pending_reservations', methods=['GET'])
def get_pending_reservations():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        query = """
            SELECT sr.id, sr.student_idno, s.firstname || ' ' || s.lastname as student_name,
                   l.lab_name, lc.computer_number, sr.reservation_date, sr.time_slot, 
                   sr.purpose, sr.created_at, sr.status
            FROM student_reservation sr
            JOIN students s ON sr.student_idno = s.idno
            JOIN laboratories l ON sr.lab_id = l.id
            JOIN lab_computers lc ON sr.computer_id = lc.id
            WHERE sr.status = 'Pending'
            ORDER BY sr.created_at DESC
        """
        
        reservations = getprocess(query)
        
        # Format created_at timestamps for easy display
        for reservation in reservations:
            if 'created_at' in reservation and reservation['created_at']:
                # Convert to more readable format
                try:
                    dt = datetime.strptime(reservation['created_at'], '%Y-%m-%d %H:%M:%S')
                    reservation['created_at'] = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
        
        return jsonify({
            'success': True,
            'reservations': reservations
        })
    except Exception as e:
        print(f"Error fetching pending reservations: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/update_reservation_status', methods=['POST'])
def update_reservation_status_endpoint():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        data = request.json
        reservation_id = data.get('reservation_id')
        status = data.get('status')
        
        if not reservation_id or not status:
            return jsonify({'success': False, 'message': 'Reservation ID and status are required'}), 400
        
        if status not in ['Approved', 'Rejected']:
            return jsonify({'success': False, 'message': 'Invalid status. Must be Approved or Rejected'}), 400
        
        # Update the reservation status
        success = postprocess(
            "UPDATE student_reservation SET status = ? WHERE id = ?",
            (status, reservation_id)
        )
        
        if success:
            # Get the updated reservation details for notification
            query = """
                SELECT sr.*, s.idno as student_idno, l.lab_name, lc.computer_number
                FROM student_reservation sr
                JOIN students s ON sr.student_idno = s.idno
                JOIN laboratories l ON sr.lab_id = l.id
                LEFT JOIN lab_computers lc ON sr.computer_id = lc.id
                WHERE sr.id = ?
            """
            reservation = getprocess(query, (reservation_id,))
            
            if reservation and len(reservation) > 0:
                # Create a notification for the student
                reservation_data = reservation[0]
                title = f"Reservation {status}"
                message = f"Your reservation for {reservation_data['lab_name']} on {reservation_data['reservation_date']} during {reservation_data['time_slot']} has been {status.lower()}."
                
                # Add notification to database
                add_reservation_notification(
                    reservation_data['student_idno'],
                    reservation_id,
                    title,
                    message,
                    'status_update'
                )
                
                # Emit socket event to notify the student
                socketio.emit(f'reservation_status_updated', {
                    'student_idno': reservation_data['student_idno'],
                    'reservation_id': reservation_id,
                    'status': status,
                    'title': title,
                    'message': message,
                    'type': 'status_update',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # If approved, update the computer status for the reservation date/time
                if status == 'Approved':
                    # We will handle the computer status separately in another function
                    pass
            
            return jsonify({
                'success': True,
                'message': f'Reservation {status.lower()} successfully'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to update reservation status'}), 500
    except Exception as e:
        print(f"Error updating reservation status: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/reset_lab_schedules', methods=['POST'])
def reset_lab_schedules():
    if 'admin_username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized. Admin login required.'}), 401
    
    try:
        # Import and use the new module
        from lab_scheduler import reset_all_lab_schedules
        result = reset_all_lab_schedules()
        
        if result["success"]:
            return jsonify({
                'success': True, 
                'message': result["message"]
            })
        else:
            return jsonify({
                'success': False, 
                'message': result["message"]
            }), 500
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error resetting lab schedules: {str(e)}'
        }), 500

@app.route('/api/import_lab_schedules', methods=['POST'])
def import_lab_schedules():
    if 'admin_username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized. Admin login required.'}), 401
    
    try:
        # Check if the request has the file part
        if 'schedule_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
        
        file = request.files['schedule_file']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        
        # Check if the file is an allowed file type
        allowed_extensions = {'csv', 'xlsx', 'xls'}
        if not file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
            return jsonify({'success': False, 'message': 'Invalid file type. Please upload a CSV or Excel file.'}), 400
        
        # Save the file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Process the file based on its type
        try:
            import pandas as pd
            
            if filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            else:  # Excel file
                df = pd.read_excel(temp_path)
            
            # Check required columns
            required_columns = ['lab_name', 'day_of_week', 'start_time', 'end_time', 'status']
            for col in required_columns:
                if col not in df.columns:
                    return jsonify({'success': False, 'message': f'Missing required column: {col}'}), 400
            
            # Get lab IDs
            conn = sqlite3.connect('student.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, lab_name FROM laboratories')
            labs = {lab_name: lab_id for lab_id, lab_name in cursor.fetchall()}
            
            # Parse the data and insert into the database
            schedules_added = 0
            schedules_failed = 0
            
            for _, row in df.iterrows():
                try:
                    # Get the lab_id from the lab_name
                    lab_name = row['lab_name'].strip()
                    if lab_name not in labs:
                        # Try to add the lab if it doesn't exist
                        cursor.execute('INSERT INTO laboratories (lab_name, status) VALUES (?, ?)', 
                                    (lab_name, 'Available'))
                        lab_id = cursor.lastrowid
                        labs[lab_name] = lab_id
                    else:
                        lab_id = labs[lab_name]
                    
                    # Parse the data
                    day_of_week = row['day_of_week'].strip()
                    start_time = row['start_time'].strip()
                    end_time = row['end_time'].strip()
                    status = row['status'].strip()
                    
                    # Optional fields
                    subject_code = row.get('subject_code', None)
                    subject_name = row.get('subject_name', None)
                    reason = row.get('reason', None)
                    
                    # Insert into database
                    cursor.execute('''
                        INSERT INTO lab_schedules 
                        (lab_id, day_of_week, start_time, end_time, subject_code, subject_name, status, reason)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (lab_id, day_of_week, start_time, end_time, subject_code, subject_name, status, reason))
                    
                    schedules_added += 1
                    
                except Exception as e:
                    schedules_failed += 1
                    print(f"Error processing row: {row}")
                    print(f"Error: {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Cleanup
            os.remove(temp_path)
            
            return jsonify({
                'success': True, 
                'message': f'Successfully imported {schedules_added} schedules. {schedules_failed} failed.'
            })
            
        except Exception as e:
            # Cleanup on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print(f"Error processing file: {str(e)}")
            return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'}), 500
        
    except Exception as e:
        print(f"Error in import_lab_schedules: {str(e)}")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500



# Route to get approved and rejected reservations for logs
@app.route('/api/get_processed_reservations', methods=['GET'])
def get_processed_reservations():
    if 'admin_username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        # Get query parameters for filtering
        status_filter = request.args.get('status', 'all')  # 'all', 'approved', 'rejected'
        date_filter = request.args.get('date', '')  # Date in YYYY-MM-DD format
        
        # Base query - excluding pending reservations from student_reservation table
        query = """
            SELECT 
                sr.id, 
                sr.student_idno,
                s.firstname || ' ' || s.lastname as student_name,
                l.lab_name,
                sr.purpose,
                sr.reservation_date,
                sr.time_slot,
                sr.status,
                s.course,
                s.year_level,
                lc.computer_number,
                sr.created_at
            FROM student_reservation sr
            JOIN laboratories l ON sr.lab_id = l.id
            JOIN students s ON sr.student_idno = s.idno
            JOIN lab_computers lc ON sr.computer_id = lc.id
            WHERE sr.status != 'Pending'
        """
        
        params = []
        
        # Add status filter
        if status_filter != 'all':
            query += " AND sr.status = ?"
            params.append(status_filter)
            
        # Add date filter
        if date_filter:
            query += " AND DATE(sr.reservation_date) = ?"
            params.append(date_filter)
            
        # Add final sorting
        query += " ORDER BY sr.reservation_date DESC, sr.created_at DESC"
        
        # Execute query
        reservations = getprocess(query, tuple(params)) if params else getprocess(query)
        
        # Format reservations for frontend
        formatted_reservations = []
        for res in reservations:
            formatted_res = dict(res)
            formatted_reservations.append(formatted_res)
            
        return jsonify({
            'success': True,
            'reservations': formatted_reservations,
            'totalCount': len(formatted_reservations)
        })
        
    except Exception as e:
        print(f"Error fetching processed reservations: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/lab_schedules/export', methods=['GET'])
def api_export_lab_schedules():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        # Get lab_id parameter if provided
        lab_id = request.args.get('lab_id')
        if lab_id:
            try:
                lab_id = int(lab_id)
            except ValueError:
                return jsonify({"success": False, "message": "Invalid lab ID"}), 400
        
        # Get all lab schedules
        if lab_id:
            schedules = get_lab_schedules(lab_id)
            # Get lab name
            lab_name = "Unknown Lab"
            labs = get_lab_names()
            for lab in labs:
                if lab['id'] == lab_id:
                    lab_name = lab['lab_name']
                    break
                    
            return jsonify({
                "success": True,
                "lab_id": lab_id,
                "lab_name": lab_name,
                "schedules": schedules
            })
        else:
            # Get all labs
            conn = sqlite3.connect('student.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, lab_name FROM laboratories')
            labs = [dict(lab) for lab in cursor.fetchall()]
            
            all_schedules = []
            for lab in labs:
                lab_schedules = get_lab_schedules(lab['id'])
                for schedule in lab_schedules:
                    all_schedules.append(schedule)
            
            return jsonify({
                "success": True,
                "labs": labs,
                "schedules": all_schedules
            })
            
    except Exception as e:
        import traceback
        print(f"DEBUG: Error exporting lab schedules: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False, 
            "message": f"Error exporting schedules: {str(e)}"
        }), 500

@app.route('/api/student/notifications', methods=['GET'])
def get_student_notifications_route():
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        student_idno = session.get('student_idno')
        notifications = get_student_notifications(student_idno)
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
    except Exception as e:
        print(f"Error fetching student notifications: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/student/notifications/read', methods=['POST'])
def mark_notification_read_route():
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        data = request.json
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return jsonify({'success': False, 'message': 'Notification ID is required'}), 400
        
        success = mark_notification_read(notification_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to mark notification as read'}), 500
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/student/notifications/read-all', methods=['POST'])
def mark_all_notifications_read_route():
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        student_idno = session.get('student_idno')
        success = mark_all_notifications_read(student_idno)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All notifications marked as read'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to mark notifications as read'}), 500
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/student/notifications/count', methods=['GET'])
def get_unread_notifications_count_route():
    if 'student_idno' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    try:
        student_idno = session.get('student_idno')
        count = get_unread_notifications_count(student_idno)
        
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        print(f"Error getting unread notifications count: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Add a scheduled task to check for upcoming reservations and send notifications
def check_upcoming_reservations():
    """Check for upcoming reservations and send notifications to students"""
    try:
        # Get reservations that are starting within the next 30 minutes
        thirty_mins_from_now = datetime.now() + timedelta(minutes=30)
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Query to find reservations that are coming up in the next 30 minutes
        query = """
            SELECT sr.*, s.idno as student_idno, s.firstname, s.lastname, l.lab_name, lc.computer_number
            FROM student_reservation sr
            JOIN students s ON sr.student_idno = s.idno
            JOIN laboratories l ON sr.lab_id = l.id
            LEFT JOIN lab_computers lc ON sr.computer_id = lc.id
            WHERE sr.reservation_date = ? 
            AND sr.status = 'Approved'
            AND sr.time_slot LIKE ? 
            AND NOT EXISTS (
                SELECT 1 FROM reservation_notifications rn 
                WHERE rn.reservation_id = sr.id AND rn.notification_type = 'upcoming'
            )
        """
        
        # Get the time component in format expected in the database
        time_to_check = thirty_mins_from_now.strftime('%H:%M')
        time_pattern = f"%{time_to_check}%"
        
        upcoming_reservations = getprocess(query, (current_date, time_pattern))
        
        for reservation in upcoming_reservations:
            # Create a notification for the upcoming reservation
            title = "Upcoming Reservation"
            message = f"Your reservation for {reservation['lab_name']} (PC #{reservation['computer_number']}) starts in 30 minutes."
            
            # Add notification to database
            add_reservation_notification(
                reservation['student_idno'],
                reservation['id'],
                title,
                message,
                'upcoming'
            )
            
            # Emit socket event to notify the student
            socketio.emit('reservation_upcoming', {
                'student_idno': reservation['student_idno'],
                'reservation_id': reservation['id'],
                'title': title,
                'message': message,
                'type': 'upcoming',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        return True
    except Exception as e:
        print(f"Error checking upcoming reservations: {e}")
        return False

# Run the check_upcoming_reservations function every minute
def start_reservation_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_upcoming_reservations, 'interval', minutes=1)
    scheduler.start()

# Function to monitor reservation time slots and auto logout/login when time slots start/end
def check_reservation_time_slots():
    """Check for reservations whose time slots have started/ended and update their status"""
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # 1. First, find approved reservations whose time slots have started
        start_query = """
            SELECT sr.*, s.idno as student_idno, l.lab_name, lc.computer_number
            FROM student_reservation sr
            JOIN students s ON sr.student_idno = s.idno
            JOIN laboratories l ON sr.lab_id = l.id
            LEFT JOIN lab_computers lc ON sr.computer_id = lc.id
            WHERE sr.reservation_date = ? 
            AND sr.status = 'Approved'
            AND time(substr(sr.time_slot, 1, 5)) <= time(?)
            AND time(substr(sr.time_slot, -5)) > time(?)
        """
        
        starting_reservations = getprocess(start_query, (current_date, current_time, current_time))
        
        for reservation in starting_reservations:
            # Update reservation status to In Use
            postprocess(
                "UPDATE student_reservation SET status = 'In Use' WHERE id = ?",
                (reservation['id'],)
            )
            
            # Update computer status to In Use
            if reservation['computer_id']:
                postprocess(
                    "UPDATE lab_computers SET status = 'In Use', student_idno = ? WHERE id = ?",
                    (reservation['student_idno'], reservation['computer_id'])
                )
            
            # Create a notification for the student
            title = "Reservation Started"
            message = f"Your reservation for {reservation['lab_name']} (PC #{reservation['computer_number']}) has started. You can now use the computer."
            
            # Add notification to database
            add_reservation_notification(
                reservation['student_idno'],
                reservation['id'],
                title,
                message,
                'system'
            )
            
            # Emit socket event to notify the student
            socketio.emit('reservation_started', {
                'student_idno': reservation['student_idno'],
                'reservation_id': reservation['id'],
                'title': title,
                'message': message,
                'type': 'system',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 2. Find reservations whose time slots have ended
        end_query = """
            SELECT sr.*, s.idno as student_idno, l.lab_name, lc.computer_number
            FROM student_reservation sr
            JOIN students s ON sr.student_idno = s.idno
            JOIN laboratories l ON sr.lab_id = l.id
            LEFT JOIN lab_computers lc ON sr.computer_id = lc.id
            WHERE sr.reservation_date = ? 
            AND sr.status = 'In Use'
            AND time(substr(sr.time_slot, -5)) <= time(?)
        """
        
        ended_reservations = getprocess(end_query, (current_date, current_time))
        
        for reservation in ended_reservations:
            # Update reservation status to Logged Out
            postprocess(
                "UPDATE student_reservation SET status = 'Logged Out' WHERE id = ?",
                (reservation['id'],)
            )
            
            # Update computer status to Available
            if reservation['computer_id']:
                postprocess(
                    "UPDATE lab_computers SET status = 'Available', student_idno = NULL WHERE id = ?",
                    (reservation['computer_id'],)
                )
            
            # Create a notification for the student
            title = "Reservation Ended"
            message = f"Your reservation for {reservation['lab_name']} has ended and you have been automatically logged out."
            
            # Add notification to database
            add_reservation_notification(
                reservation['student_idno'],
                reservation['id'],
                title,
                message,
                'system'
            )
            
            # Emit socket event to notify the student
            socketio.emit('reservation_ended', {
                'student_idno': reservation['student_idno'],
                'reservation_id': reservation['id'],
                'title': title,
                'message': message,
                'type': 'system',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return True
    except Exception as e:
        print(f"Error checking reservation time slots: {e}")
        return False

# Update the scheduler to also run check_reservation_time_slots
def start_all_schedulers():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(check_upcoming_reservations, 'interval', minutes=1)
        scheduler.add_job(check_reservation_time_slots, 'interval', minutes=1)
        scheduler.start()
        print("Schedulers started successfully")
    except Exception as e:
        print(f"Error starting schedulers: {e}")

# Call this function when the application starts
if __name__ == '__main__':
    # Initialize tables and start schedulers before running the app
    initialize_tables()
    start_all_schedulers()
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=True, host='0.0.0.0', port=port)