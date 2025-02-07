from flask import Flask, render_template, redirect, url_for, session, request, flash
from dbhelperXampp import * 

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.secret_key = '%:%:'  


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

        if not username or not password:
            flash("Username and Password are required", 'error')
            return redirect(url_for('login'))
        user = get_user_by_credentials(username, password)

        if user:
            session['username'] = username  
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
    if 'username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('login'))
    student = get_student_by_username(session['username'])
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
            flash("An error occurred during registration. Please try again.", 'error')

    return render_template('client/register.html')






@app.route('/admin', methods=['GET', 'POST'])  
def admin_login():
    pagetitle = 'Administrator Login'
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Username and Password are required", 'error')
            return redirect(url_for('login'))

        admin = get_admin_user_by_credentials(username, password)

        if admin:
            session['username'] = username  
            flash("Login successful!", 'success')
            return redirect(url_for('dashboard'))  
        else:
            flash("Invalid username or password", 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin/adminlogin.html', pagetitle=pagetitle)


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("You need to login first", 'warning')
        return redirect(url_for('admin_login'))
    
    student_count = get_count_students()
    
    return render_template('admin/dashboard.html', student_count=student_count)

@app.route('/adminLogout')
def adminLogout():
    session.pop('username', None)
    flash("You have been logged out", 'info')
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.pop('username', None)  
    flash("You have been logged out.", 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)