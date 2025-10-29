import os
from datetime import datetime, timedelta

import gspread
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify, flash
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management


# --- Google Sheets Setup ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", SCOPE)
CLIENT = gspread.authorize(CREDS)

SHEET_NAME = "Student_DB"
WORKSHEET_ATTENDANCE = CLIENT.open(SHEET_NAME).worksheet("Attendence")
WORKSHEET_FEES = CLIENT.open(SHEET_NAME).worksheet("Fees")
WORKSHEET_TIMETABLE = CLIENT.open(SHEET_NAME).worksheet("Timetable")
WORKSHEET_MCQ = CLIENT.open(SHEET_NAME).worksheet("MCQ")
WORKSHEET_PARENTS = CLIENT.open(SHEET_NAME).worksheet("Parents")
WORKSHEET_STUDENTS = CLIENT.open(SHEET_NAME).worksheet("Students")
WORKSHEET_Teachers = CLIENT.open(SHEET_NAME).worksheet("Teachers")
WORKSHEET_MARKS = CLIENT.open(SHEET_NAME).worksheet("Marks")
WORKSHEET_USERS = CLIENT.open(SHEET_NAME).worksheet("Users")

# IMAGE_FOLDER = r"C:\Users\Ashwin Kumar N S\OneDrive\Desktop\projects\web_page\templates"

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER = os.path.join(BASE_DIR, "Templates")  # Folder containing syllabus PDFs

# --- Sample user database (for login demo) ---
# users = {
#     "parent1": {"password": "parent123", "role": "parent", "email": "parent1@gmail.com"},
#     "parent2": {"password": "parent124", "role": "parent", "email": "parent2@gmail.com"},
#     "student1": {"password": "234567", "role": "student", "email": "ashwinkumarnsrao@gmail.com"},
#     "student2": {"password": "23456", "role": "student", "email": "student2@gmail.com"},
#     "staff1": {"password": "abcde", "role": "staff", "email": "staff1@gmail.com"},
#     "staff2": {"password": "bcdef", "role": "staff", "email": "staff2@gmail.com"},
#     "staff3": {"password": "cdefg", "role": "staff", "email": "staff3@gmail.com"},
#     "staff4": {"password": "defgh", "role": "staff", "email": "staff4@gmail.com"},
#     "staff5": {"password": "efghi", "role": "staff", "email": "staff5@gmail.com"},
#     "staff6": {"password": "fghij", "role": "staff", "email": "staff6@gmail.com"},
#     "staff7": {"password": "ghijk", "role": "staff", "email": "staff7@gmail.com"}
# }

def get_user_from_sheet(username):
    """Fetch user record from Users sheet"""
    users_data = WORKSHEET_USERS.get_all_records()
    return next((u for u in users_data if u["Username"] == username), None)

# --- Subjects and Time Slots ---
subjects = ["RM", "CN", "TOC", "AI", "SE", "EVS", "WTL"]
time_slots = ["9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"]

# -------------------- ROUTES --------------------

# --- Login Page ---
@app.route('/')
def login_page():
    return render_template('login.html')



# @app.route('/login', methods=['POST'])
# def login():
#     user_id = request.form['username']
#     password = request.form['password']
#     role_selected = request.form['role']
#
#     if user_id in users and users[user_id]['password'] == password:
#         user_role = users[user_id]['role']
#         if user_role != role_selected:
#             return "<h3>Role mismatch. Please choose the correct role.</h3>"
#
#         # Save session
#         session['user_id'] = user_id
#         session['role'] = user_role
#
#         # --- For students, fetch USN & info from Google Sheet ---
#         if user_role == "student":
#             all_students = WORKSHEET_FEES.get_all_records()
#             student_info = next((s for s in all_students if s["USN"] == user_id), None)
#
#             if student_info:
#                 session['usn'] = student_info["USN"]
#                 session['student_name'] = student_info["Student Name"]
#                 session['course'] = student_info["Course"]
#             else:
#                 # fallback if not found
#                 session['usn'] = user_id
#                 session['student_name'] = user_id
#                 session['course'] = "B.E CSE"
#
#         # --- For staff, fetch their subject from Staff sheet ---
#         if user_role == "staff":
#             all_staff = WORKSHEET_Teachers.get_all_records()
#             staff_info = next((s for s in all_staff if s["Staff ID"] == user_id), None)
#             if staff_info:
#                 session['staff_name'] = staff_info["Professor Name"]
#                 session['subject'] = staff_info["Subject"]
#             else:
#                 session['staff_name'] = user_id
#                 session['subject'] = None  # fallback if not found
#
#         # Redirect to dashboard
#         if user_role == 'student':
#             return redirect(url_for('student_dashboard'))
#         elif user_role == 'staff':
#             return redirect(url_for('staff_dashboard'))
#         elif user_role == 'parent':
#             return redirect(url_for('parent_dashboard'))
#     else:
#         return "<h3>Invalid ID or Password! Please try again.</h3>"

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['username']
    password = request.form['password']
    role_selected = request.form['role']

    # --- Fetch all users from Google Sheet ---
    all_users = WORKSHEET_USERS.get_all_records()  # your Google Sheet tab name: "users"

    # --- Find matching user from sheet ---
    user = next((u for u in all_users if u['Username'] == user_id and u['Password'] == password), None)

    if user:
        user_role = user['Role']

        # --- Check if selected role matches role in sheet ---
        if user_role.lower() != role_selected.lower():
            return "<h3>Role mismatch. Please choose the correct role.</h3>"

        # --- Save user info to session ---
        session['user_id'] = user_id
        session['role'] = user_role

        # --- If student, fetch student info from student sheet ---
        if user_role.lower() == "student":
            all_students = WORKSHEET_FEES.get_all_records()
            student_info = next((s for s in all_students if s["USN"] == user_id), None)

            if student_info:
                session['usn'] = student_info["USN"]
                session['student_name'] = student_info["Student Name"]
                session['course'] = student_info["Course"]
            else:
                session['usn'] = user_id
                session['student_name'] = user_id
                session['course'] = "B.E CSE"

        # --- If staff, fetch subject info from Staff sheet ---
        elif user_role.lower() == "staff":
            all_staff = WORKSHEET_Teachers.get_all_records()
            staff_info = next((s for s in all_staff if s["Staff ID"] == user_id), None)

            if staff_info:
                session['staff_name'] = staff_info["Professor Name"]
                session['subject'] = staff_info["Subject"]
            else:
                session['staff_name'] = user_id
                session['subject'] = None

        # --- Redirect based on role ---
        if user_role.lower() == 'student':
            return redirect(url_for('student_dashboard'))
        elif user_role.lower() == 'staff':
            return redirect(url_for('staff_dashboard'))
        elif user_role.lower() == 'parent':
            return redirect(url_for('parent_dashboard'))
    else:
        return "<h3>Invalid ID or Password! Please try again.</h3>"



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username'].strip()
        new_password = request.form['new_password'].strip()

        users = WORKSHEET_USERS.get_all_records()
        for idx, u in enumerate(users, start=2):  # +2 because headers are in row 1
            if u['Username'].lower() == username.lower():
                WORKSHEET_USERS.update_cell(idx, 2, new_password)  # Password is column 2
                flash(f"✅ Password updated successfully for {username}!", "success")
                return redirect(url_for('reset_password'))

        flash("❌ Username not found. Please try again.", "error")
        return redirect(url_for('reset_password'))

    return render_template('reset_password.html')



@app.route('/student')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login_page'))

    # Fetch student data
    all_students = WORKSHEET_STUDENTS.get_all_records()
    student_info = next((s for s in all_students if s["USN"] == session['user_id']), None)

    default_image = '/static/images/default.jpg'

    if student_info:
        print(f"[DEBUG] Student info: {student_info}")

        photo_url = student_info.get('PhotoURL', '').strip()
        if photo_url:
            student_image_url = drive_link_to_direct(photo_url)
        else:
            student_image_url = default_image

        print(f"[DEBUG] Final student_image_url: {student_image_url}")

        return render_template(
            'student_dashboard.html',
            student=student_info,
            student_image_url=student_image_url
        )
    else:
        return render_template(
            'student_dashboard.html',
            student={
                "Student Name": session['user_id'],
                "USN": session['user_id'],
                "Course": "B.E CSE",
                "Section": ""
            },
            student_image_url=default_image
        )


def drive_link_to_direct(url):
    """
    Converts Google Drive share link to direct-view or thumbnail URL.
    """
    try:
        if not url:
            return '/static/images/default.jpg'

        file_id = None
        if '/d/' in url:
            file_id = url.split('/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
        else:
            print(f"[DEBUG] Not a valid Drive link: {url}")
            return url

        # Use Drive thumbnail API — works best for <img> embeds
        direct_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w500"
        print(f"[DEBUG] Final Drive thumbnail URL → {direct_url}")
        return direct_url

    except Exception as e:
        print(f"[ERROR] drive_link_to_direct(): {e}")
        return '/static/images/default.jpg'


# @app.route('/staff')
# def staff_dashboard():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#     return render_template('staff_dashboard.html')

#

@app.route('/staff')
def staff_dashboard():
    # Check login and role
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_id = session.get('user_id')

    # Fetch staff info from Google Sheet
    staff_data = WORKSHEET_Teachers.get_all_records()  # Make sure STAFF_SHEET is defined
    staff_info = next((s for s in staff_data if s.get('Staff ID') == staff_id), None)

    if not staff_info:
        return render_template('staff_dashboard.html',
                               error_message="Staff details not found in the sheet.")

    # Use your helper for Drive link conversion
    photo_url = drive_link_to_direct(staff_info.get('PhotoURL', ''))

    return render_template(
        'staff_dashboard.html',
        staff_name=staff_info.get('Professor Name'),
        staff_id=staff_info.get('Staff ID'),
        subject=staff_info.get('Subject'),
        department=staff_info.get('Department'),
        photo_url=photo_url
    )



@app.route('/parent')
def parent_dashboard():
    if 'user_id' not in session or session.get('role') != 'parent':
        return redirect(url_for('login_page'))
    parent_id = session['user_id']
    # --- Fetch parent info from Parents sheet ---
    all_parents = WORKSHEET_PARENTS.get_all_records()
    parent_info = next((p for p in all_parents if p["ParentID"] == parent_id), None)
    if not parent_info: return "<h3>No parent record found!</h3>"

    # --- Get linked students USNs ---
    linked_usns = [usn.strip()
                   for usn in parent_info.get("Linked Students (USN)", "").split(",")
                   if usn.strip()]
    if not linked_usns: return "<h3>No students linked to this parent!</h3>"
    # --- Fetch student info from Students sheet ---
    all_students = WORKSHEET_STUDENTS.get_all_records()
    students_info = [s for s in all_students if s["USN"] in linked_usns]
    if not students_info: return "<h3>No students linked to this parent!</h3>"

    # --- Selected student (default to first linked student) ---
    selected_usn = request.args.get("student_usn") or students_info[0]["USN"]
    selected_student = next((s for s in students_info if s["USN"] == selected_usn), students_info[0])

    # --- Student photo URL ---
    default_image = '/static/images/default.jpg'
    photo_url = selected_student.get('PhotoURL', '').strip()
    if photo_url:
        student_image_url = drive_link_to_direct(photo_url)
    else:
        student_image_url = default_image
    return render_template('parent_dashboard.html', parent_name=parent_info.get("Parent Name"),
                               students=students_info, selected_student=selected_student,
                               student_image_url=student_image_url, year=datetime.now().year)

@app.route('/syllabus', methods=['GET', 'POST'])
def syllabus_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    syllabus_files = {
        'BECSE-1': 'syllabus_becse1.pdf',
        'BECSE-2': 'syllabus_becse2.pdf',
        'BECSE-3': 'syllabus_becse3.pdf'
    }

    if request.method == 'POST':
        course = request.form.get('course')
        filename = syllabus_files.get(course)
        if not filename:
            return "❌ Invalid course selected", 400

        file_path = os.path.join(PDF_FOLDER, filename)
        if os.path.exists(file_path):
            return send_from_directory(PDF_FOLDER, filename)
        else:
            return f"❌ File not found: {file_path}", 404

    return render_template('syllabus.html')

@app.route('/assessment')
def assessment_page():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login_page'))

    # Fetch all test records from MCQ sheet
    all_tests = WORKSHEET_MCQ.get_all_records()  # List of dicts

    # Optional: sort by Date
    all_tests.sort(key=lambda x: x.get('Date', ''))

    return render_template('assessment.html', tests=all_tests)

# @app.route('/upload_mcq', methods=['GET', 'POST'])
# def upload_mcq():
#     # Check if logged in and staff
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     lecturer_name = session.get('user_id')  # Assuming staff ID or name is stored
#
#     if request.method == 'POST':
#         subject = request.form['subject']
#         date = request.form['date']
#         time_limit = request.form['time_limit']
#         test_link = request.form['test_link']
#         button_text = request.form.get('button_text', 'Take Test')
#
#         # Create a test record
#         new_test = {
#             'Subject': subject,
#             'Lecturer': lecturer_name,
#             'Date': date,
#             'Time Limit': f"{time_limit} mins",
#             'Test Link': test_link,
#             'Button Text': button_text
#         }
#
#         # Append to Google Sheet
#         WORKSHEET_MCQ.append_row(list(new_test.values()))
#
#         return render_template('upload_mcq.html',
#                                message="Test uploaded successfully!",
#                                success=True)
#
#     return render_template('upload_mcq.html')

@app.route('/upload_mcq', methods=['GET', 'POST'])
def upload_mcq():
    # Ensure user is logged in and is staff
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    lecturer_id = session.get('user_id')

    # Fetch teacher data from Google Sheet
    teachers_data = WORKSHEET_Teachers.get_all_records()
    lecturer_subject = None
    lecturer_name = None

    # Find the logged-in teacher’s subject
    for t in teachers_data:
        if t.get('Staff ID') == lecturer_id:
            lecturer_subject = t.get('Subject')
            lecturer_name = t.get('Professor Name')
            break

    if not lecturer_subject:
        return render_template('upload_mcq.html',
                               message="No subject assigned to your account.",
                               success=False)

    if request.method == 'POST':
        date = request.form['date']
        time_limit = request.form['time_limit']
        test_link = request.form['test_link']
        button_text = request.form.get('button_text', 'Take Test')

        # Create a test record
        new_test = {
            'Subject': lecturer_subject,
            'Lecturer': lecturer_name,
            'Date': date,
            'Time Limit': f"{time_limit} mins",
            'Test Link': test_link,
            'Button Text': button_text
        }

        # Append to Google Sheet
        WORKSHEET_MCQ.append_row(list(new_test.values()))

        return render_template('upload_mcq.html',
                               message="Test uploaded successfully!",
                               success=True,
                               subject=lecturer_subject)

    return render_template('upload_mcq.html',
                           subject=lecturer_subject)




@app.route('/attendance')
def attendance_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    # Determine student_id:
    # - For students: use session['user_id']
    # - For parents: use query param ?student_id=
    if session.get('role') == 'parent':
        student_id = request.args.get('student_id')
        if not student_id:
            return "<h3>Please select a student!</h3>"
    else:
        student_id = session.get('user_id')

    # Fetch all attendance records for the student
    all_records = WORKSHEET_ATTENDANCE.get_all_records()
    student_records = [r for r in all_records if r['StudentID'] == student_id]

    # Determine default date (latest attendance date)
    if student_records:
        latest_date = max(datetime.strptime(r['Date'], "%Y-%m-%d") for r in student_records)
        default_date = latest_date.strftime("%Y-%m-%d")
    else:
        default_date = datetime.today().strftime("%Y-%m-%d")

    # Get student name (optional)
    all_students = WORKSHEET_STUDENTS.get_all_records()
    student_info = next((s for s in all_students if s['USN'] == student_id), {})
    student_name = student_info.get("Student Name", student_id)

    return render_template(
        'attendance.html',
        student_id=student_id,
        student_name=student_name,
        default_date=default_date,
        role=session.get('role')
    )



@app.route('/grievance')
def grievance_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('grievance.html')


# --- ATTENDANCE: Get Weekly Records ---
@app.route('/get_attendance_week/<date_str>', methods=['GET'])
def get_attendance_week(date_str):
    """Return weekly attendance for logged-in student"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    student_id = session['user_id']
    all_records = WORKSHEET_ATTENDANCE.get_all_records()

    student_records = [r for r in all_records if r['StudentID'] == student_id]

    start_date = datetime.strptime(date_str, "%Y-%m-%d")
    end_date = start_date + timedelta(days=6)

    week_records = [
        {
            "date": r['Date'],
            "time": r['Time'],
            "subject": r['Subject'],
            "status": r['Status']
        }
        for r in student_records
        if start_date <= datetime.strptime(r['Date'], "%Y-%m-%d") <= end_date
    ]

    return jsonify({"records": week_records})

# --- ATTENDANCE: Update Existing Record ---
@app.route('/update_attendance', methods=['POST'])
def update_attendance():
    data = request.get_json()
    student_id = data['student_id']
    date = data['date']
    time = data['time']
    status = data['status']

    all_records = WORKSHEET_ATTENDANCE.get_all_records()
    for i, record in enumerate(all_records, start=2):  # header is row 1
        if record['StudentID'] == student_id and record['Date'] == date and record['Time'] == time:
            WORKSHEET_ATTENDANCE.update_cell(i, 6, status)  # Status column
            WORKSHEET_ATTENDANCE.update_cell(i, 7, datetime.now().isoformat())  # Timestamp
            return jsonify({'message': 'Attendance updated!'}), 200

    return jsonify({'error': 'Record not found'}), 404

# --- ATTENDANCE: Add New Record ---
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    student_id = data.get('student_id')
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    time = data.get('time')
    subject = data.get('subject')
    status = data.get('status', 'Present')

    all_records = WORKSHEET_ATTENDANCE.get_all_records()
    for r in all_records:
        if r['StudentID'] == student_id and r['Date'] == date and r['Time'] == time:
            return jsonify({'error': 'Attendance already marked'}), 400

    new_id = len(all_records) + 1
    WORKSHEET_ATTENDANCE.append_row([new_id, student_id, date, time, subject, status, datetime.now().isoformat()])
    return jsonify({'message': 'Attendance recorded successfully!'}), 201

# --- FEES: Fetch from Google Sheet ---
def get_fees_from_sheet(student_id):
    """Fetch all fee details for a specific student from Google Sheet."""
    all_records = WORKSHEET_FEES.get_all_records()
    student_records = [r for r in all_records if r['student_id'] == student_id]
    return student_records


# @app.route("/fees")
# def show_fees():
#     usn = session.get("usn")
#     print(f"USN {usn}")
#     if not usn:
#         return redirect(url_for("login_page"))
#
#     current_year = "2025-26"  # Set this dynamically if needed
#
#     # Get selected year from query parameter
#     selected_year = request.args.get("year", current_year)
#
#     # Fetch all fee records for the student
#     all_records = WORKSHEET_FEES.get_all_records()
#     student_records = [r for r in all_records if r.get("USN") == usn]
#
#     if not student_records:
#         return f"No fee records found for USN: {usn}"
#
#     # Get unique years/semesters for dropdown
#     years = sorted(list(set(r.get("Semester", current_year) for r in student_records)))
#
#     # Filter records for selected year
#     filtered_records = [r for r in student_records if r.get("Semester") == selected_year]
#
#     # Calculate totals
#     total_fees = sum(int(r["Amount"]) for r in filtered_records if str(r["Amount"]).isdigit())
#     paid_fees = sum(int(r["Amount"]) for r in filtered_records if
#                     str(r["Amount"]).isdigit() and r["Status"].strip().lower() == "done")
#     pending_fees = total_fees - paid_fees
#
#     # Prepare demands for template
#     demands = []
#     for i, r in enumerate(filtered_records, start=1):
#         amount = int(r["Amount"]) if str(r["Amount"]).isdigit() else 0
#         demands.append({
#             "id": i,
#             "ref_date": r["Ref Date"],
#             "ref_no": r["Ref No"],
#             "title": r["Title"],
#             "amount": amount,
#             "status": r["Status"]
#         })
#
#     return render_template(
#         "fees.html",
#         student_name=session.get("student_name", student_records[0]["Student Name"]),
#         course=session.get("course", student_records[0]["Course"]),
#         demands=demands,
#         total_fees=total_fees,
#         paid_fees=paid_fees,
#         pending_fees=pending_fees,
#         sem_or_year=selected_year,
#         years=years,
#         year=datetime.now().year
#     )

# @app.route("/fees")
# def show_fees():
#     # Use URL USN if provided (from parent dashboard), otherwise fall back to session USN (student login)
#     usn = request.args.get("usn") or session.get("usn")
#     print(f"USN --> {usn}")
#
#     if not usn:
#         return redirect(url_for("login_page"))
#
#     current_year = "2025-26"  # or dynamic
#     selected_year = request.args.get("year", current_year)
#
#     # Fetch all fee records for the student
#     all_records = WORKSHEET_FEES.get_all_records()
#     student_records = [r for r in all_records if r.get("USN") == usn]
#
#     if not student_records:
#         return f"No fee records found for USN: {usn}"
#
#     # Unique years/semesters
#     years = sorted(list(set(r.get("Semester", current_year) for r in student_records)))
#
#     # Filter records for selected year
#     filtered_records = [r for r in student_records if r.get("Semester") == selected_year]
#
#     # Totals
#     total_fees = sum(int(r["Amount"]) for r in filtered_records if str(r["Amount"]).isdigit())
#     paid_fees = sum(int(r["Amount"]) for r in filtered_records if str(r["Amount"]).isdigit() and r["Status"].strip().lower() == "done")
#     pending_fees = total_fees - paid_fees
#
#     # Prepare demands
#     demands = []
#     for i, r in enumerate(filtered_records, start=1):
#         amount = int(r["Amount"]) if str(r["Amount"]).isdigit() else 0
#         demands.append({
#             "id": i,
#             "ref_date": r["Ref Date"],
#             "ref_no": r["Ref No"],
#             "title": r["Title"],
#             "amount": amount,
#             "status": r["Status"]
#         })
#
#     # Student info for template
#     student_name = request.args.get("student_name") or session.get("student_name", student_records[0]["Student Name"])
#     course = request.args.get("course") or session.get("course", student_records[0]["Course"])
#
#     return render_template(
#         "fees.html",
#         student_name=student_name,
#         course=course,
#         demands=demands,
#         total_fees=total_fees,
#         paid_fees=paid_fees,
#         pending_fees=pending_fees,
#         sem_or_year=selected_year,
#         years=years,
#         year=datetime.now().year
#     )

@app.route("/fees")
def show_fees():
    # Determine USN
    usn = request.args.get("usn") or session.get("usn")

    if not usn:
        return redirect(url_for("login_page"))

    # Determine user role
    role = request.args.get("role") or session.get("role") or "student"
    print(f"USN & Role--{usn}  & {role}")


    current_year = "2025-26"  # or dynamic
    selected_year = request.args.get("year", current_year)

    # Fetch all fee records for the student
    all_records = WORKSHEET_FEES.get_all_records()
    student_records = [r for r in all_records if r.get("USN") == usn]

    if not student_records:
        return f"No fee records found for USN: {usn}"

    # Unique years/semesters
    years = sorted(list(set(r.get("Semester", current_year) for r in student_records)))

    # Filter records for selected year
    filtered_records = [r for r in student_records if r.get("Semester") == selected_year]

    # Totals
    total_fees = sum(int(r["Amount"]) for r in filtered_records if str(r["Amount"]).isdigit())
    paid_fees = sum(int(r["Amount"]) for r in filtered_records if str(r["Amount"]).isdigit() and r["Status"].strip().lower() == "done")
    pending_fees = total_fees - paid_fees

    # Prepare demands
    demands = []
    for i, r in enumerate(filtered_records, start=1):
        amount = int(r["Amount"]) if str(r["Amount"]).isdigit() else 0
        demands.append({
            "id": i,
            "ref_date": r["Ref Date"],
            "ref_no": r["Ref No"],
            "title": r["Title"],
            "amount": amount,
            "status": r["Status"]
        })

    # Student info for template
    student_name = request.args.get("student_name") or session.get("student_name", student_records[0]["Student Name"])
    course = request.args.get("course") or session.get("course", student_records[0]["Course"])

    return render_template(
        "fees.html",
        student_name=student_name,
        course=course,
        demands=demands,
        total_fees=total_fees,
        paid_fees=paid_fees,
        pending_fees=pending_fees,
        sem_or_year=selected_year,
        years=years,
        year=datetime.now().year,
        role=role,  # pass role to template
        usn=usn  # pass USN for back link
    )


# @app.route("/timetable")
# def timetable():
#     # Fetch all records from Google Sheet
#     all_records = WORKSHEET_TIMETABLE.get_all_records()
#
#     if not all_records:
#         return "No timetable data found."
#
#     # Build set of weekdays and timeslots
#     weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
#     timeslots = sorted(list({rec["Time"] for rec in all_records if rec.get("Time")}))
#
#     # Initialize timetable as empty grid
#     timetable_data = {day: {t: "-" for t in timeslots} for day in weekdays}
#
#     for rec in all_records:
#         date_str = rec.get("Date")
#         time = rec.get("Time")
#         subject = rec.get("Subject", "")
#         lecturer = rec.get("Lecturer", "")
#
#         # Validate data
#         if not date_str or not time:
#             continue
#
#         # Try converting date → weekday
#         try:
#             # Works for both "2025-10-25" and "25-Oct-2025"
#             try:
#                 date_obj = datetime.strptime(date_str, "%d-%b-%Y")
#             except ValueError:
#                 date_obj = datetime.strptime(date_str, "%Y-%m-%d")
#
#             day_name = date_obj.strftime("%A")
#         except Exception:
#             continue
#
#         if day_name in timetable_data:
#             timetable_data[day_name][time] = f"{subject} ({lecturer})" if lecturer else subject
#
#     # Render page
#     return render_template(
#         "timetable.html",
#         student_name="JSS Student",
#         course="CSE",
#         timetable=timetable_data,
#         timeslots=timeslots,
#         days=weekdays,
#         year=datetime.now().year
#     )

@app.route("/timetable")
def timetable():
    # Fetch fixed timetable from Google Sheet
    all_records = WORKSHEET_TIMETABLE.get_all_records()

    if not all_records:
        return "No timetable data found."

    # Expected columns
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    # Extract timeslots directly from the sheet (the first column)
    timeslots = [row.get("Day/Time") for row in all_records if row.get("Day/Time")]

    # Initialize timetable data
    timetable_data = {day: {} for day in weekdays}

    for row in all_records:
        time = row.get("Day/Time")
        if not time:
            continue
        for day in weekdays:
            subject = row.get(day, "").strip()
            timetable_data[day][time] = subject if subject else "-"

    return render_template(
        "timetable.html",
        student_name=session.get("student_name", "JSS Student"),
        course=session.get("course", "CSE"),
        timetable=timetable_data,
        timeslots=timeslots,
        days=weekdays,
        year=datetime.now().year
    )

@app.route('/get_attendance_till/<date_str>', methods=['GET'])
def get_attendance_till(date_str):
    """Return all attendance records till the selected date for given student"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    # Get student_id from query param if parent, else session
    student_id = request.args.get('student_id', session.get('user_id'))

    all_records = WORKSHEET_ATTENDANCE.get_all_records()
    student_records = [r for r in all_records if r['StudentID'] == student_id]

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    filtered_records = [
        {
            "date": r['Date'],
            "time": r['Time'],
            "subject": r['Subject'],
            "status": r['Status']
        }
        for r in student_records
        if datetime.strptime(r['Date'], "%Y-%m-%d") <= selected_date
    ]

    return jsonify({"records": filtered_records})

@app.route('/staff/attendance', methods=['GET', 'POST'])
def update_student_attendance():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_subject = session.get('subject')
    all_records = WORKSHEET_ATTENDANCE.get_all_records()
    records = [r for r in all_records if r['Subject'] == staff_subject]

    # Track updated IDs in session
    updated_ids = session.get('updated_ids', set())
    if isinstance(updated_ids, list):
        updated_ids = set(updated_ids)

    if request.method == 'POST':
        try:
            row_id = int(request.form.get('row_id'))
            new_status = request.form.get('status')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Debug
            print("DEBUG: row_id", row_id, "new_status", new_status)

            record_to_update = records[row_id]
            record_id = record_to_update['ID']

            all_ids = [r['ID'] for r in all_records]
            sheet_row = all_ids.index(record_id) + 2  # +2 for header row

            # Update Status and Timestamp in Google Sheet
            WORKSHEET_ATTENDANCE.update(f'F{sheet_row}:G{sheet_row}', [[new_status, timestamp]])

            updated_ids.add(record_id)
            session['updated_ids'] = list(updated_ids)

            # Return JSON if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'row_id': row_id, 'UpdateStatus': '✅ Updated', 'Timestamp': timestamp})

            flash(f"Attendance updated for StudentID {record_to_update['StudentID']}", 'success')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)})
            flash(f"Error updating attendance: {str(e)}", 'error')

        return redirect(url_for('update_student_attendance'))

    # Mark each record "Updated" or "Not Updated"
    for r in records:
        r['UpdateStatus'] = "✅ Updated" if r['ID'] in updated_ids else "⏳ Not Updated"

    return render_template('update_student_attendance.html', records=records, subject=staff_subject)




# # --- STAFF UPLOAD/UPDATE MARKS ---
# @app.route('/staff/upload_marks', methods=['GET', 'POST'])
# def upload_marks():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     staff_id = session.get('user_id')
#
#     all_marks = WORKSHEET_MARKS.get_all_records()  # list of dicts
#
#     if request.method == 'POST':
#         student_usn = request.form['usn'].strip()
#         student_name = request.form['name'].strip()
#         subject = request.form['subject'].strip()
#         marks = request.form['marks'].strip()
#
#         # Validate numeric marks
#         if not marks.isdigit():
#             flash("Marks must be a number", "error")
#             return redirect(url_for('upload_marks'))
#
#         # Check if entry exists for same student + subject
#         existing = next((r for r in all_marks if r['Student USN'] == student_usn and r['Subject'] == subject), None)
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#         if existing:
#             # Update existing row
#             row_idx = all_marks.index(existing) + 2  # +2 because header row
#             WORKSHEET_MARKS.update(f'E{row_idx}:G{row_idx}', [[marks, staff_id, timestamp]])
#             flash(f"Updated marks for {student_usn} ({subject})", "success")
#         else:
#             # Append new row
#             new_id = len(all_marks) + 1
#             WORKSHEET_MARKS.append_row([new_id, student_usn, student_name, subject, marks, staff_id, timestamp])
#             flash(f"Added marks for {student_usn} ({subject})", "success")
#
#         return redirect(url_for('upload_marks'))
#
#     return render_template('upload_marks.html', marks=all_marks)


@app.route('/staff/upload_marks', methods=['GET', 'POST'])
def upload_marks():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_id = session.get('user_id')

    # Get staff subject from Teachers sheet
    teacher_records = WORKSHEET_Teachers.get_all_records()
    staff_record = next((t for t in teacher_records if t['Staff ID'] == staff_id), None)
    if not staff_record:
        flash("Staff record not found", "error")
        return redirect(url_for('login_page'))
    subject = staff_record['Subject']

    # Get all marks and all students
    all_marks = WORKSHEET_MARKS.get_all_records()
    student_records = WORKSHEET_STUDENTS.get_all_records()

    if request.method == 'POST':
        student_usn = request.form['usn'].strip()

        # Get student name automatically
        student = next((s for s in student_records if s['USN'] == student_usn), None)
        if not student:
            flash(f"Student USN {student_usn} not found", "error")
            return redirect(url_for('upload_marks'))
        student_name = student['Student Name']

        marks = request.form['marks'].strip()
        if not marks.isdigit():
            flash("Marks must be a number", "error")
            return redirect(url_for('upload_marks'))

        # Check if entry exists for same student + subject
        existing = next((r for r in all_marks if r['Student USN'] == student_usn and r['Subject'] == subject), None)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing:
            # Update existing row
            row_idx = all_marks.index(existing) + 2  # +2 for header row
            WORKSHEET_MARKS.update(f'E{row_idx}:G{row_idx}', [[marks, staff_id, timestamp]])
            flash(f"Updated marks for {student_usn} ({subject})", "success")
        else:
            # Append new row
            new_id = len(all_marks) + 1
            WORKSHEET_MARKS.append_row([new_id, student_usn, student_name, subject, marks, staff_id, timestamp])
            flash(f"Added marks for {student_usn} ({subject})", "success")

        return redirect(url_for('upload_marks'))

    # Filter marks to only show this subject
    subject_marks = [m for m in all_marks if m['Subject'] == subject]

    return render_template('upload_marks.html', marks=subject_marks, subject=subject, student_records=student_records)
@app.route('/marks')
def view_marks():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    all_marks = WORKSHEET_MARKS.get_all_records()

    # For students, filter only their marks
    if session.get('role') == 'student':
        student_usn = session.get('usn')
        all_marks = [r for r in all_marks if r['Student USN'] == student_usn]

    # For parents, filter linked students
    elif session.get('role') == 'parent':
        parent_id = session.get('user_id')
        all_parents = WORKSHEET_PARENTS.get_all_records()
        parent_info = next((p for p in all_parents if p["ParentID"] == parent_id), None)
        linked_usns = [usn.strip() for usn in parent_info.get("Linked Students (USN)", "").split(",") if usn.strip()]
        all_marks = [r for r in all_marks if r['Student USN'] in linked_usns]

    # Staff sees all marks
    return render_template('view_marks.html', marks=all_marks, role=session.get('role'))

@app.route('/staff/edit_marks/<int:row_id>', methods=['GET', 'POST'])
def edit_marks(row_id):
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_id = session.get('user_id')
    all_marks = WORKSHEET_MARKS.get_all_records()
    student_records = WORKSHEET_STUDENTS.get_all_records()
    teacher_records = WORKSHEET_Teachers.get_all_records()
    staff_record = next((t for t in teacher_records if t['Staff ID'] == staff_id), None)
    subject = staff_record['Subject']

    # Find the row by index
    if row_id < 1 or row_id > len(all_marks):
        flash("Invalid mark record", "error")
        return redirect(url_for('upload_marks'))

    mark_entry = all_marks[row_id - 1]  # zero-indexed

    if request.method == 'POST':
        new_marks = request.form['marks'].strip()
        if not new_marks.isdigit():
            flash("Marks must be a number", "error")
            return redirect(url_for('edit_marks', row_id=row_id))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Update marks in sheet
        sheet_row = row_id + 1  # +1 because Google Sheet header
        WORKSHEET_MARKS.update(f'E{sheet_row}:G{sheet_row}', [[new_marks, staff_id, timestamp]])
        flash(f"Marks updated for {mark_entry['Student USN']}", "success")
        return redirect(url_for('upload_marks'))

    return render_template('edit_marks.html', mark=mark_entry)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
