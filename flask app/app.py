from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from dbhelper import *
from flask_socketio import SocketIO, emit, disconnect
import os

app = Flask(__name__)

# Session Configuration
app.config["SESSION_COOKIE_NAME"] = "main_app_session"
app.secret_key = os.urandom(24)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory dictionary to store active users
active_users_dict = {}

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
            flash("Login successful!", 'success')
            
            # Emit active users after successful login
            emit_active_users()
            
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
    return render_template('client/studentdashboard.html', student=student, pagetitle=pagetitle)

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

@app.route('/logout')
def logout():
    username = session.get('user_username')

    if not username:
        flash("Error: No user is logged in", 'error')
        return redirect(url_for('login'))

    session.pop('user_username', None)  

    # Emit active users after successful logout
    emit_active_users()

    flash("Logout successful", 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    pagetitle = 'Dashboard'
    if 'admin_username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('admin_login'))

    # Fetch active students from the in-memory dictionary
    active_students = list(active_users_dict.keys())
    active_students_count = len(active_students)

    student_count = get_count_students()
    return render_template('admin/dashboard.html', student_count=student_count, active_students=active_students, pagetitle=pagetitle)

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

        if add_record('admin_users', admin_username=admin_username, password=password, email=email, name=name):
            flash("Admin registered successfully!", 'success')
            return redirect(url_for('admin_login')) 
        else:
            flash("Error registering admin. Please try again.", 'error')
            return render_template('admin/adminregister.html') 
    
    return render_template('admin/adminregister.html')

@app.route('/adminLogout')
def adminLogout():
    if 'admin_username' in session:
        session.pop('admin_username', None)  # Logs out only the admin
        flash("Admin has been logged out.", 'info')
    return redirect(url_for('admin_login'))

@app.route('/get_user_count')
def get_user_count():
    # Fetch active students from the in-memory dictionary
    active_students = list(active_users_dict.keys())
    active_students_count = len(active_students)
    return jsonify(student_count=get_count_students(), active_students_count=active_students_count)

# SocketIO Events
from flask_socketio import disconnect

@socketio.on('connect')
def handle_connect():
    sid = request.sid  # Get the session ID
    if 'user_username' in session:
        username = session['user_username']
        if not username.startswith('admin-'):  # Only track students
            active_users_dict[username] = sid
            emit_active_users()
            print(f"User {username} connected with SID {sid}")  # Debugging
    else:
        disconnect()  # Disconnect if user session is missing
        print("Disconnected user with no session")  # Debugging


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    username = next((user for user, user_sid in active_users_dict.items() if user_sid == sid), None)

    if username:
        del active_users_dict[username]  # Remove user from active list
        emit_active_users()
        print(f"User {username} disconnected with SID {sid}")  # Debugging


def emit_active_users():
    """ Helper function to emit the active users count """
    active_users = list(active_users_dict.keys())  # Get active users
    print(f"Emitting active users: {active_users}")  # Debugging
    socketio.emit('update_active_users', active_users)

if __name__ == "__main__":
    socketio.run(app, debug=True)