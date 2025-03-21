import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify, Response
from dbhelper import *
from flask_socketio import SocketIO, emit
import os
import time
from datetime import timedelta, datetime
from flask_cors import CORS
import json
import openai
from threading import Thread
from prompts import get_response 
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64


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

app = Flask(__name__)
CORS(app)

app.config["SESSION_COOKIE_NAME"] = "main_app_session"
app.config['UPLOAD_FOLDER'] = 'static/images'
app.secret_key = os.urandom(24)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# client = openai.OpenAI(
#     api_key="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",
#     base_url="https://openrouter.ai/api/v1"
# )


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

@app.route('/close-reservation/<int:reservation_id>', methods=['POST'])
def close_reservation(reservation_id):
    try:
        print(f"Attempting to close reservation with ID: {reservation_id}")  # Print reservation ID
        
        # Fetch the reservation details
        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            print(f"Reservation with ID {reservation_id} not found")
            return jsonify({'success': False, 'message': 'Reservation not found'})
        
        print(f"Fetched reservation: {reservation}")  # Print reservation details
        
        # Check if 2 hours have passed since the reservation was made
        reservation_time = datetime.strptime(reservation['login_time'], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        time_difference = current_time - reservation_time
        
        print(f"Time difference (in seconds): {time_difference.total_seconds()}")  # Print time difference
        
        if time_difference.total_seconds() >= 7200:  # 2 hours = 7200 seconds
            # Delete the reservation
            print(f"Deleting reservation {reservation_id} as more than 2 hours have passed")
            delete_reservation(reservation_id)
            return jsonify({'success': True, 'message': 'Reservation deleted successfully (2 hours passed)'})
        else:
            print(f"Updating reservation {reservation_id} status to 'Disapproved'")  # Print action before updating status
            # Update the reservation status to "Disapproved"
            if update_reservation_status(reservation_id, 'Disapproved'):
                # Emit a Socket.IO event to notify both admin and student
                socketio.emit('reservation_updated', {
                    'reservation_id': reservation_id,
                    'status': 'Disapproved'
                })
                return jsonify({'success': True, 'message': 'Reservation disapproved successfully'})
            else:
                print(f"Failed to update reservation {reservation_id} status to 'Disapproved'")
                return jsonify({'success': False, 'message': 'Failed to update reservation status'})
    
    except Exception as e:
        print(f"Error in close reservation for {reservation_id}: {str(e)}")  # Print the exception message
        return jsonify({'success': False, 'message': str(e)})



@app.route('/logout-student/<int:reservation_id>', methods=['POST'])
def logout_student(reservation_id):
    try:
        print(f"Attempting to log out reservation with ID: {reservation_id}")  # Debug print

        # Fetch the reservation details
        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            print(f"Reservation with ID {reservation_id} not found")  # Debug print
            return jsonify({'success': False, 'message': 'Reservation not found'})

        # Record the logged-out time
        logout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Logout time recorded: {logout_time}")  # Debug print

        # Update the reservation with logged-out time (status remains unchanged)
        if update_reservation_logout(reservation_id, logout_time):
            print(f"Reservation {reservation_id} updated successfully")  # Debug print

            # Insert session history
            insert_session_history(
                student_idno=reservation['student_idno'],
                login_time=reservation['login_time'],
                logout_time=logout_time
            )

            # Deduct one session from the student's sessions_left
            student = get_student_by_idno(reservation['student_idno'])
            if student and student['sessions_left'] > 0:
                student['sessions_left'] -= 1
                update_student_sessions(student['idno'], student['sessions_left'])
                print(f"Updated sessions_left for student {student['idno']} to {student['sessions_left']}")  # Debug print

                # Emit a Socket.IO event to notify the student about the session update
                socketio.emit('update_session_count', {
                    'student_idno': student['idno'],
                    'sessions_left': student['sessions_left']
                }, room=student['idno'])  # Emit to the specific student's room

            # Emit a Socket.IO event to notify both admin and student
            socketio.emit('reservation_updated', {
                'reservation_id': reservation_id,
                'logout_time': logout_time,
                'sessions_left': student['sessions_left'] if student else 0
            })
            return jsonify({'success': True, 'message': 'Student logged out successfully'})
        else:
            print(f"Failed to update reservation {reservation_id}")  # Debug print
            return jsonify({'success': False, 'message': 'Failed to update reservation'})
    except Exception as e:
        print(f"Error in logout-student for {reservation_id}: {str(e)}")  # Debug print
        return jsonify({'success': False, 'message': str(e)})



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

@app.route('/get_reservation_history')
def get_reservation_history():
    if 'student_idno' not in session:
        print('Unauthorized access attempt. Student ID not in session.')
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    student_idno = session['student_idno']
    print(f"Fetching reservation history for student ID: {student_idno}")  # Log student ID fetching

    sql = """
    SELECT r.id, l.lab_name, r.purpose, r.reservation_date, r.status, r.logout_time
    FROM reservations r
    JOIN laboratories l ON r.lab_id = l.id
    WHERE r.student_idno = ? AND r.status IN ('Closed', 'Cancelled', 'Logged Out', 'Approved', 'Disapproved')
    ORDER BY r.reservation_date DESC
    """
    
    try:
        # Attempt to fetch reservations from the database
        reservations = getprocess(sql, (student_idno,))
        print(f"Found {len(reservations)} reservations for student ID: {student_idno}")  # Log number of reservations found

        return jsonify({"success": True, "data": reservations})  
    except Exception as e:
        # Catch any errors during the query process
        print(f"Error fetching reservation history: {e}")  # Log any errors during fetch
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
    if 'admin_username' not in session:
        print("Unauthorized access attempt. Admin not logged in.")  # Debug print
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        # Fetch reservations that are approved and have a login_time but no logout_time
        sql = """
        SELECT r.id, r.student_idno, r.student_name, l.lab_name, r.purpose, 
               r.reservation_date, r.login_time, r.logout_time, r.status
        FROM reservations r
        JOIN laboratories l ON r.lab_id = l.id
        WHERE r.status = 'Approved' AND r.logout_time IS NULL
        """
        reservations = getprocess(sql)
        print(f"Fetched {len(reservations)} current sit-in reservations.")  # Debug print

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
                "lab_name": reservation['lab_name'],
                "purpose": reservation['purpose'],
                "reservation_date": reservation['reservation_date'],
                "login_time": reservation['login_time'],
                "logout_time": reservation['logout_time'],
                "status": reservation['status'],
                "sessions_left": sessions_left
            })

        return jsonify({"success": True, "data": reservation_list})
    except Exception as e:
        print(f"Error fetching current sit-in reservations: {e}")  # Debug print
        return jsonify({"success": False, "message": "Error fetching current sit-in reservations"}), 500



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


@socketio.on('submit_feedback')
def handle_feedback(data):
    print('Received feedback:', data)  # Debug: Log received feedback
    lab = data['lab']
    feedback_text = data['feedback_text']
    rating = data['rating']
    student_idno = data['student_idno']  # Get student_idno from the data

    # Save feedback to the database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO feedback (lab, student_idno, feedback_text, rating) VALUES (?, ?, ?, ?)',
        (lab, student_idno, feedback_text, rating)
    )
    conn.commit()
    conn.close()

    # Broadcast the new feedback to all connected admin clients
    emit('new_feedback', {
        'lab': lab,
        'student_idno': student_idno,  # Use idno instead of student_name
        'feedback_text': feedback_text,
        'rating': rating
    }, broadcast=True)
    print('Broadcasted feedback to admin clients')  # Debug: Log broadcast



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

    admin_username = session.get('admin_username')
    active_students = list(active_users_dict.keys())
    laboratories = get_count_laboratories()
    student_count = get_count_students()
    active_students_count = len(active_students)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    admin_firstname = session.get('admin_firstname')
    students = get_paginated_students(offset, per_page)
    total_students = get_count_students()
    total_pages = (total_students + per_page - 1) // per_page
    reservations = get_all_reservations()
    today = datetime.now().strftime('%Y-%m-%d')

    return render_template('admin/dashboard.html',
                           student_count=student_count,
                           active_students=active_students,
                           laboratories=laboratories,
                           admin_username=admin_username,
                           pagetitle=pagetitle,
                           active_students_count=active_students_count,
                           students=students,
                           page=page,
                           total_pages=total_pages,
                           reservations=reservations,
                           today=today,
                           admin_firstname=admin_firstname
                           )

@app.route('/get_students')
def get_students():
    if 'admin_username' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    students = get_all_students()  # Replace with your function to fetch students
    student_list = []
    for student in students:
        student_list.append({
            "idno": student['idno'],  # Access dictionary keys
            "lastname": student['lastname'],
            "firstname": student['firstname'],
            "course": student['course'],
            "year_level": student['year_level'],
            "sessions_left": student['sessions_left']
        })
    return jsonify({"success": True, "data": student_list})
    
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)