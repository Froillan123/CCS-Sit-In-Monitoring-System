from flask import Flask, render_template, redirect, url_for, session, request, flash
from dbhelper import *  # Import the dbhelper functions

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.secret_key = '%:%:'  # Secret key for session management



@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    
    if hasattr(session, 'username') and 'username' not in session:
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

        # Validate inputs
        if not username or not password:
            flash("Username and Password are required", 'error')
            return redirect(url_for('login'))

        # Check user credentials
        user = get_user_by_credentials(username, password)

        if user:
            session['username'] = username  # Store username in session
            flash("Login successful!", 'success')
            return redirect(url_for('student_list'))  # Redirect to student list page
        else:
            flash("Invalid username or password", 'error')
            return redirect(url_for('login'))

    return render_template('login.html', pagetitle=pagetitle)


@app.route('/student_list')
def student_list():
    if 'username' not in session:
        flash("You need to login first", 'error')
        return redirect(url_for('login'))
    return render_template('studentlist.html')  # Create this template for the student list page


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect form data
        idno = request.form.get('idno')
        lastname = request.form.get('lastname')
        firstname = request.form.get('firstname')
        midname = request.form.get('midname')
        course = request.form.get('course')
        year_level = request.form.get('year_level')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate inputs (you can add more validation here as needed)
        if not all([idno, lastname, firstname, course, username, password]):
            flash("All fields are required.", 'error')
            return redirect(url_for('register'))

        # Check if the ID number already exists
        existing_student = get_student_by_id(idno)
        if existing_student:
            flash("Student ID already exists.", 'error')
            return redirect(url_for('register'))

        # Prepare student data to insert
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

        # Add new student record
        if add_record('students', **student_data):
            flash("Registration successful!", 'success')
            return redirect(url_for('login'))
        else:
            flash("An error occurred during registration. Please try again.", 'error')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear session
    flash("You have been logged out.", 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)