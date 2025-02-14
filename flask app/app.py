from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify, Response
from dbhelper import *
from flask_socketio import SocketIO, emit, disconnect
import os
import time
import json
app = Flask(__name__)


app.config["SESSION_COOKIE_NAME"] = "main_app_session"
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/images'
socketio = SocketIO(app, cors_allowed_origins="*")


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
            session['user_username'] = username
            session['student_idno'] = user['idno']  # Use idno instead of id
            flash("Login successful!", 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid username or password", 'error')
            return redirect(url_for('login'))

    return render_template('client/login.html', pagetitle=pagetitle)


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
    if request.method == 'POST':
        # Ensure the student is logged in
        if 'student_idno' not in session:
            return jsonify({"status": "error", "message": "Student not logged in"}), 401

        # Get form data
        student_idno = session['student_idno']  # Use student_idno from session
        lab_name = request.form.get('lab_name')
        purpose = request.form.get('purpose')
        reservation_date = request.form.get('reservation_date')
        time_in = request.form.get('time_in')
        time_out = request.form.get('time_out')

        # Validate form data
        if not all([lab_name, purpose, reservation_date, time_in, time_out]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400

        # Query to get the student's name (firstname, lastname) based on idno
        student = get_student_by_idno(student_idno)  # Fetch student by idno
        if not student:
            return jsonify({"status": "error", "message": "Student not found"}), 404

        student_name = f"{student['firstname']} {student['lastname']}"

        # Prepare data for insertion
        data = {
            "student_idno": student_idno,  # Use student_idno here
            "student_name": student_name,
            "lab_name": lab_name,
            "purpose": purpose,
            "reservation_date": reservation_date,
            "time_in": time_in,
            "time_out": time_out
        }

        # Add record to the database
        try:
            success = add_record("reservations", **data)
            if success:
                return jsonify({"status": "success", "message": f"Reservation added successfully by {student_name}!"}), 200
            else:
                return jsonify({"status": "error", "message": "Error adding reservation."}), 500
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500


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

    # Get available laboratories
    labs = get_laboratories()

    return render_template('client/studentdashboard.html', student=student, pagetitle=pagetitle, labs=labs)

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
        update_record('students', username=username, firstname=data['firstname'], lastname=data['lastname'], course=data['course'], year_level=data['year_level'], email=data['email'])

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
        # Save the file to the upload folder
        filename = f"student_{session['user_username']}.png"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Update the student's profile picture in the database
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
            'password': password
        }

        if add_record('students', **student_data):
            flash("Registration successful!", 'success')
            return redirect(url_for('login'))
        else:
            flash("Registration failed. Try again.", 'error')

    return render_template('client/register.html')



@app.route('/get_labs', methods=['GET'])
def get_labs():
    try:
        cursor = db.execute('SELECT lab_name FROM laboratories')
        labs = cursor.fetchall()
        lab_list = [lab[0] for lab in labs]  # Extract lab names
        return jsonify({"success": True, "labs": lab_list})
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

@app.route('/logout')
def logout():
    username = session.get('user_username')

    if not username:
        flash("Error: No user is logged in", 'error')
        return redirect(url_for('login'))

    session.pop('user_username', None)  

    # Remove user from active users dictionary
    if username in active_users_dict:
        del active_users_dict[username]
        notify_active_users_update()

    flash("Logout successful", 'info')
    return redirect(url_for('login'))


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
    return render_template('admin/dashboard.html', student_count=student_count, active_students=active_students, laboratories=laboratories, admin_username=admin_username, pagetitle=pagetitle)

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

        # Add the new admin to the database
        if add_record('admin_users', 
                      admin_username=admin_username, 
                      password=password, 
                      email=email, 
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

# Route to fetch all announcements
@app.route('/get_announcements', methods=['GET'])
def get_announcements():
    try:
        announcements = get_all_announcements()  # Ensure this function exists and works
        return jsonify(announcements)  # Return the announcements as JSON
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


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

if __name__ == "__main__":
    app.run(debug=True)