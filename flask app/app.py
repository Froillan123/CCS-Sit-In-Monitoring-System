from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify, Response
from dbhelper import *
from flask_socketio import SocketIO, emit
import os
import time
from datetime import timedelta, datetime
import json
app = Flask(__name__)


app.config["SESSION_COOKIE_NAME"] = "main_app_session"
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/images'
socketio = SocketIO(app, cors_allowed_origins="https://css-sit-in-monitoring-system.onrender.com")
socketio = SocketIO(app, async_mode='eventlet') 


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

            session['user_username'] = username
            session['student_idno'] = user['idno']
            session['student_firstname'] = user['firstname']
            session['student_lastname'] = user['lastname']
            session['student_midname'] = user['midname']

            # Add user to active_users_dict
            active_users_dict[username] = True
            socketio.emit('update_active_users', list(active_users_dict.keys()))  # Emit active users update

            # Insert login time into session_history
            login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            insert_session_history(user['idno'], login_time)

            # Decrease the student's sessions left by 1
            if user['sessions_left'] > 0:
                user['sessions_left'] -= 1
                update_student_sessions(user['idno'], user['sessions_left'])
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
        # Handle the request for session extension
        student_idno = session.get('student_idno')
        if student_idno:
            # Logic to handle the extension request (e.g., send an email, save to database, etc.)
            flash("Your request for a session extension has been submitted.", 'info')
            return redirect(url_for('login'))  # Redirect back to login after submission

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

    # Construct the full name
    student_name = f"{student_firstname} {student_midname} {student_lastname}".strip()

    print(f"Session Data - Student ID: {student_idno}, Student Name: {student_name}")

    # Retrieve form data safely
    lab_id = request.form.get('lab_id', '').strip()
    purpose = request.form.get('purpose_select', '').strip()
    reservation_date = request.form.get('reservation_date', '').strip()
    time_in = request.form.get('time_in', '').strip()
    time_out = request.form.get('time_out', '').strip()

    print(f"Received Form Data - Lab ID: {lab_id}, Purpose: {purpose}, Reservation Date: {reservation_date}, Time In: {time_in}, Time Out: {time_out}")

    # Ensure required fields are present
    if not all([student_idno, student_name, lab_id, purpose, reservation_date, time_in, time_out]):
        print("Error: Missing required fields")
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

    # Validate date format
    try:
        datetime.strptime(reservation_date, '%Y-%m-%d')
        print("Date format is valid")
    except ValueError:
        print("Error: Invalid date format")
        return jsonify({'status': 'error', 'message': 'Invalid date format (YYYY-MM-DD expected)'}), 400

    # Insert into database
    try:
        db = sqlite3.connect('student.db')
        cursor = db.cursor()
        print("Database connected successfully")

        cursor.execute("""
            INSERT INTO reservations(student_idno, student_name, lab_id, purpose, reservation_date, time_in, time_out) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_idno, student_name, lab_id, purpose, reservation_date, time_in, time_out))
        
        db.commit()
        print("Reservation inserted successfully")

        return jsonify({'status': 'success', 'message': 'Reservation created successfully'}), 200

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': 'Database error'}), 500

    finally:
        db.close()



@app.route('/student_dashboard')
def student_dashboard():
    pagetitle = "Student Dashboard"
    
    if 'user_username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('login'))

    student = get_student_by_username(session['user_username'])
    if not student:
        flash("Student not found", 'danger')
        return redirect(url_for('login'))

    labs = get_lab_names()  # Fetch the list of lab names with IDs
    current_session = get_total_session(student['idno'])

    # Fetch reservations for the student
    reservations = get_reservations_by_student_id(student['idno'])

    return render_template(
        'client/studentdashboard.html',
        student=student,
        pagetitle=pagetitle,
        labs=labs,
        idno=student['idno'],
        current_session=current_session,
        reservations=reservations  # Pass reservations to the template
    )

@app.route('/cancel-reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    try:
        # Delete the reservation from the database
        success = delete_record('reservations', id=reservation_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete reservation'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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

        # Update the student's details in the database
        update_record('students', username=username, firstname=data['firstname'], lastname=data['lastname'], midname=data['midname'], course=data['course'], year_level=data['year_level'], email=data['email'])

        # Handle profile picture upload
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

        # Check if student ID already exists
        existing_student = get_student_by_id(idno)
        if existing_student:
            flash("Student ID already exists.", 'error')
            return redirect(url_for('register'))

        # Check if email already exists
        existing_email = get_student_by_email(email)
        if existing_email:
            flash("Email already exists.", 'error')
            return redirect(url_for('register'))

        # Prepare student data with default profile picture
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
            'profile_picture': 'default.png'  # Assign default profile picture
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

    # Remove user from active users dictionary
    if username in active_users_dict:
        del active_users_dict[username]
        socketio.emit('update_active_users', list(active_users_dict.keys()))  # Emit active users update

    # Update session_history with logout time and duration
    student_idno = session.get('student_idno')
    if student_idno:
        logout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_session_history(student_idno, logout_time)

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
    sql = """
        SELECT * FROM session_history
        WHERE student_idno = ?
        ORDER BY id  -- Order by the primary key (id) to ensure insertion order
        LIMIT 30
    """
    history = getprocess(sql, (student_idno,))
    return jsonify(history)



@app.route('/get_weekly_usage/<student_idno>', methods=['GET'])
def get_weekly_usage(student_idno):
    sql = """
        SELECT strftime('%w', login_time) AS day, COUNT(*) AS session_count
        FROM session_history
        WHERE student_idno = ? AND strftime('%w', login_time) BETWEEN '0' AND '6' -- Sunday to Saturday
        GROUP BY day
        ORDER BY day;
    """
    usage_data = getprocess(sql, (student_idno,))

    # Map SQLite weekday numbers to readable names
    day_mapping = {
        '0': 'Sunday',  # Sunday
        '1': 'Monday',
        '2': 'Tuesday',
        '3': 'Wednesday',
        '4': 'Thursday',
        '5': 'Friday',
        '6': 'Saturday'
    }

    # Format data as JSON
    formatted_data = {day_mapping.get(row['day'], 0): row['session_count'] for row in usage_data}

    print("Formatted Data:", formatted_data)  # Debugging: Print the data

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

    # Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    students = get_paginated_students(offset, per_page)
    total_students = get_count_students()
    total_pages = (total_students + per_page - 1) // per_page

    return render_template('admin/dashboard.html',
                           student_count=student_count,
                           active_students=active_students,
                           laboratories=laboratories,
                           admin_username=admin_username,
                           pagetitle=pagetitle,
                           active_students_count=active_students_count,
                           students=students,
                           page=page,
                           total_pages=total_pages)

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
            session['admin_username'] = username  
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

        # Validate secret key
        if secret_key != "kimperor123":
            flash("Unauthorized access!", 'error')
            return render_template('admin/adminregister.html')

        # Validate admin username format
        if not admin_username.startswith("admin-"):
            flash("Invalid admin username format!", 'error')
            return render_template('admin/adminregister.html')

        # Check if admin username already exists
        existing_admin = get_admin_by_username(admin_username)
        if existing_admin:
            flash("Admin username already exists!", 'error')
            return render_template('admin/adminregister.html')

        # Split the full name into first name and last name
        name_parts = name.strip().split(maxsplit=1)  # Split into 2 parts
        admin_firstname = name_parts[0] if len(name_parts) > 0 else ""
        admin_lastname = name_parts[1] if len(name_parts) > 1 else ""

        if add_record('admin_users', 
                      admin_username=admin_username, 
                      password=password, 
                      email=email, 
                      name=name,  # Add this line
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

@app.route('/create_announcement', methods=['POST'])
def create_announcement():
    data = request.get_json()
    announcement_text = data.get('announcement_text')

    # Get the admin's username from the session
    admin_username = session.get('admin_username')

    if not admin_username:
        return jsonify({"success": False, "message": "Admin not logged in"})

    if not announcement_text:
        return jsonify({"success": False, "message": "Missing announcement text"})

    try:
        # Use the add_record function to insert the announcement
        success = add_record(
            table="announcements",
            admin_username=admin_username,
            announcement_text=announcement_text,
            announcement_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to add announcement"})
    except Exception as e:
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
        announcements = get_all_announcements()  # Ensure this function exists and works
        return jsonify(announcements)  # Return the announcements as JSON
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
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to update announcement"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/delete_announcement/<int:announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    try:
        success = delete_record(table="announcements", id=announcement_id)  # Ensure this function exists
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to delete announcement"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    

@app.route('/activity_breakdown', methods=['GET'])
def activity_breakdown():
    # Ensure the user is logged in
    if 'student_idno' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    # Get the logged-in student's ID
    student_idno = session['student_idno']

    # Connect to the database
    db = sqlite3.connect('student.db')
    cursor = db.cursor()

    # Fetch activity breakdown for the logged-in student
    cursor.execute("""
        SELECT purpose, COUNT(*) as count 
        FROM reservations 
        WHERE student_idno = ?
        GROUP BY purpose
    """, (student_idno,))
    results = cursor.fetchall()
    db.close()

    # Convert the results into a dictionary
    activity_data = {purpose: count for purpose, count in results}

    return jsonify(activity_data)


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    emit('update_active_users', list(active_users_dict.keys()))


@app.route('/get_user_count')
def get_user_count():
    active_students = list(active_users_dict.keys())
    active_students_count = len(active_students)
    return jsonify(student_count=get_count_students(), active_students_count=active_students_count)

def emit_active_users():
    """ Helper function to emit the active users count """
    active_users = list(active_users_dict.keys()) 
    print(f"Emitting active users: {active_users}") 
    socketio.emit('update_active_users', active_users)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')