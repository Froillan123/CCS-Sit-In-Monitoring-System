from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from dbhelper import * 
from flask_caching import Cache
from flask_socketio import SocketIO, emit
import redis
import os

app = Flask(__name__)
REDIS_URL = "rediss://red-cuis0p23esus739lbi20:OtiJ6rapHQtFl5QMIVU6YBf9Rko3UW4I@singapore-redis.render.com:6379"

# Configure Flask Session to use Redis
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis.from_url(REDIS_URL)

# Configure Flask Caching to use Redis
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = REDIS_URL
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# Session Configuration
app.config["SESSION_COOKIE_NAME"] = "main_app_session"
app.secret_key = os.urandom(24)

# Initialize Redis Client
redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=False)  # Keep binary

cache = Cache(app)
socketio = SocketIO(app, cors_allowed_origins="*")

ACTIVE_USERS_KEY = "active_students"

# Shared active users dictionary
active_users_dict = {}

@socketio.on('connect')
def handle_connect():
    if 'user_username' in session:
        username = session['user_username']
        if not username.startswith('admin-'):  # Only track students
            sid = request.sid
            redis_client.hset(ACTIVE_USERS_KEY, username.encode('utf-8'), sid.encode('utf-8'))  # Store as binary
            
            # Emit updated count to all clients
            emit_active_users()

@socketio.on('disconnect')
def handle_disconnect():
    username = None
    for user, sid in redis_client.hgetall(ACTIVE_USERS_KEY).items():
        if sid == request.sid.encode('utf-8'):  # Compare binary data
            username = user
            break

    if username:
        redis_client.hdel(ACTIVE_USERS_KEY, username)  # Remove from Redis
        
        # Emit updated count to all clients
        emit_active_users()

def emit_active_users():
    """ Helper function to emit the active users count """
    active_users = redis_client.hkeys(ACTIVE_USERS_KEY)  # Get active users (binary keys)
    emit('update_active_users', active_users, broadcast=True)

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

    flash("Logout successful", 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    pagetitle = 'Dashboard'
    if 'admin_username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('admin_login'))

    # Fetch active students from Redis
    active_students = redis_client.hkeys(ACTIVE_USERS_KEY)
    active_students_count = redis_client.hlen(ACTIVE_USERS_KEY) 

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
    # Fetch active students from Redis
    active_students = redis_client.hkeys(ACTIVE_USERS_KEY)
    active_students_count = len(active_students)
    return jsonify(student_count=get_count_students(), active_students_count=active_students_count)

if __name__ == "__main__":
    socketio.run(app, debug=True)