# # app.py
#
# import os
# from datetime import datetime, timedelta
# from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify, flash
# import firebase_database as fdb  # <-- Our firebase_database module
#
# app = Flask(__name__)
# app.secret_key = "supersecretkey"
#
# # ---------------- PATHS ----------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# PDF_FOLDER = os.path.join(BASE_DIR, "Templates")  # Folder containing syllabus PDFs
#
# subjects = ["RM", "CN", "TOC", "AI", "SE", "EVS", "WTL"]
# time_slots = ["9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"]
#
#
# # ---------------- HELPERS ----------------
# def drive_link_to_direct(url):
#     """Converts Google Drive share link to direct-view or thumbnail URL."""
#     try:
#         if not url:
#             return '/static/images/default.jpg'
#
#         file_id = None
#         if '/d/' in url:
#             file_id = url.split('/d/')[1].split('/')[0]
#         elif 'id=' in url:
#             file_id = url.split('id=')[1].split('&')[0]
#         else:
#             return url
#
#         direct_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w500"
#         return direct_url
#     except:
#         return '/static/images/default.jpg'
#
#
# # ---------------- ROUTES ----------------
#
# # --- Login Page ---
# @app.route('/')
# def login_page():
#     return render_template('login.html')
#
#
# @app.route('/login', methods=['POST'])
# def login():
#     user_id = request.form['username']
#     password = request.form['password']
#     role_selected = request.form['role']
#
#     user = fdb.get_user(user_id)
#     if not user or user.get("Password") != password:
#         return "<h3>Invalid ID or Password! Please try again.</h3>"
#
#     if user.get("Role", "").lower() != role_selected.lower():
#         return "<h3>Role mismatch. Please choose the correct role.</h3>"
#
#     session['user_id'] = user_id
#     session['role'] = user.get("Role")
#
#     # Student
#     if session['role'].lower() == "student":
#         student_info = fdb.get_student(user_id)
#         if student_info:
#             session['usn'] = student_info.get("USN")
#             session['student_name'] = student_info.get("Student Name")
#             session['course'] = student_info.get("Course")
#             session['student_id'] = user_id
#         else:
#             session['usn'] = user_id
#             session['student_name'] = user_id
#             session['course'] = "B.E CSE"
#
#     # Staff
#     elif session['role'].lower() == "staff":
#         staff_info = fdb.get_staff(user_id)
#         session['staff_id'] = user_id
#         if staff_info:
#             session['staff_name'] = staff_info.get("Professor Name")
#             session['subject'] = staff_info.get("Subject")
#         else:
#             session['staff_name'] = user_id
#             session['subject'] = None
#
#     # Redirect based on role
#     if session['role'].lower() == 'student':
#         return redirect(url_for('student_dashboard'))
#     elif session['role'].lower() == 'staff':
#         return redirect(url_for('staff_dashboard'))
#     elif session['role'].lower() == 'parent':
#         return redirect(url_for('parent_dashboard'))
#
#
# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login_page'))
#
#
# @app.route('/reset_password', methods=['GET', 'POST'])
# def reset_password():
#     if request.method == 'POST':
#         username = request.form['username'].strip()
#         new_password = request.form['new_password'].strip()
#         user = fdb.get_user(username)
#         if user:
#             fdb.update_password(username, new_password)
#             flash(f"✅ Password updated successfully for {username}!", "success")
#             return redirect(url_for('reset_password'))
#         flash("❌ Username not found. Please try again.", "error")
#         return redirect(url_for('reset_password'))
#     return render_template('reset_password.html')
#
#
# # ---------------- STUDENT DASHBOARD ----------------
# @app.route('/student')
# def student_dashboard():
#     if 'user_id' not in session or session.get('role') != 'student':
#         return redirect(url_for('login_page'))
#
#     student_info = fdb.get_student(session['user_id'])
#     default_image = '/static/images/default.jpg'
#     if student_info:
#         photo_url = student_info.get('PhotoURL', '').strip()
#         student_image_url = drive_link_to_direct(photo_url) if photo_url else default_image
#         return render_template('student_dashboard.html',
#                                student=student_info,
#                                student_image_url=student_image_url)
#     else:
#         return render_template('student_dashboard.html',
#                                student={
#                                    "Student Name": session['user_id'],
#                                    "USN": session['user_id'],
#                                    "Course": "B.E CSE",
#                                    "Section": ""
#                                },
#                                student_image_url=default_image)
#
#
# # ---------------- STAFF DASHBOARD ----------------
# @app.route('/staff')
# def staff_dashboard():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     staff_info = fdb.get_staff(session['user_id'])
#     if not staff_info:
#         return render_template('staff_dashboard.html', error_message="Staff details not found.")
#
#     photo_url = drive_link_to_direct(staff_info.get('PhotoURL', ''))
#     return render_template('staff_dashboard.html',
#                            staff_name=staff_info.get("Professor Name"),
#                            staff_id=staff_info.get("Staff ID"),
#                            subject=staff_info.get("Subject"),
#                            department=staff_info.get("Department"),
#                            photo_url=photo_url)
#
#
# # ---------------- PARENT DASHBOARD ----------------
# @app.route('/parent')
# def parent_dashboard():
#     if 'user_id' not in session or session.get('role') != 'parent':
#         return redirect(url_for('login_page'))
#
#     parent_info = fdb.get_parent(session['user_id'])
#     if not parent_info:
#         return "<h3>No parent record found!</h3>"
#
#     linked_usns = [usn.strip() for usn in parent_info.get("Linked Students (USN)", "").split(",") if usn.strip()]
#     if not linked_usns:
#         return "<h3>No students linked to this parent!</h3>"
#
#     students_info = [fdb.get_student(usn) for usn in linked_usns]
#     selected_usn = request.args.get("student_usn") or linked_usns[0]
#     selected_student = next((s for s in students_info if s["USN"] == selected_usn), students_info[0])
#     default_image = '/static/images/default.jpg'
#     student_image_url = drive_link_to_direct(selected_student.get('PhotoURL', '')) if selected_student.get('PhotoURL') else default_image
#
#     return render_template('parent_dashboard.html',
#                            parent_name=parent_info.get("Parent Name"),
#                            students=students_info,
#                            selected_student=selected_student,
#                            student_image_url=student_image_url,
#                            year=datetime.now().year)
#
#
# # ---------------- SYLLABUS ----------------
# @app.route('/syllabus', methods=['GET', 'POST'])
# def syllabus_page():
#     if 'user_id' not in session:
#         return redirect(url_for('login_page'))
#
#     syllabus_files = {
#         'BECSE-1': 'syllabus_becse1.pdf',
#         'BECSE-2': 'syllabus_becse2.pdf',
#         'BECSE-3': 'syllabus_becse3.pdf'
#     }
#
#     if request.method == 'POST':
#         course = request.form.get('course')
#         filename = syllabus_files.get(course)
#         if not filename:
#             return "❌ Invalid course selected", 400
#         file_path = os.path.join(PDF_FOLDER, filename)
#         if os.path.exists(file_path):
#             return send_from_directory(PDF_FOLDER, filename)
#         else:
#             return f"❌ File not found: {file_path}", 404
#
#     return render_template('syllabus.html')
#
#
# @app.route('/staff_syllabus', methods=['GET', 'POST'])
# def staff_syllabus_page():
#     return syllabus_page()  # same logic
#
#
# # ---------------- ASSESSMENT ----------------
# @app.route('/assessment')
# def assessment_page():
#     if 'user_id' not in session or session.get('role') != 'student':
#         return redirect(url_for('login_page'))
#
#     all_tests = fdb.get_mcq_tests()
#     all_tests.sort(key=lambda x: x.get('Date', ''))
#     return render_template('assessment.html', tests=all_tests)
#
#
# @app.route('/upload_mcq', methods=['GET', 'POST'])
# def upload_mcq():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     staff_id = session['user_id']
#     staff_info = fdb.get_staff(staff_id)
#     subject = staff_info.get('Subject') if staff_info else None
#     lecturer_name = staff_info.get("Professor Name") if staff_info else staff_id
#
#     if request.method == 'POST':
#         date = request.form['date']
#         time_limit = request.form['time_limit']
#         test_link = request.form['test_link']
#         button_text = request.form.get('button_text', 'Take Test')
#
#         fdb.upload_mcq_test(subject, lecturer_name, date, time_limit, test_link, button_text)
#         return render_template('upload_mcq.html', message="Test uploaded successfully!", success=True, subject=subject)
#
#     return render_template('upload_mcq.html', subject=subject)
#
# @app.route("/fees")
# def show_fees():
#     usn = request.args.get("usn") or session.get("usn")
#     role = request.args.get("role") or session.get("role") or "student"
#
#     if not usn:
#         return redirect(url_for("login_page"))
#
#     student_records = fdb.get_fees(usn)
#     if not student_records:
#         return f"No fee records found for USN: {usn}"
#
#     current_year = "2025-26"
#     selected_year = request.args.get("year", current_year)
#     filtered_records = [r for r in student_records if r.get("Semester") == selected_year]
#
#     total_fees = sum(int(r.get("Amount", 0)) for r in filtered_records if str(r.get("Amount", "0")).isdigit())
#     paid_fees = sum(int(r.get("Amount", 0)) for r in filtered_records if str(r.get("Amount", "0")).isdigit() and r.get("Status", "").strip().lower() == "done")
#     pending_fees = total_fees - paid_fees
#
#     demands = []
#     for i, r in enumerate(filtered_records, start=1):
#         amount = int(r.get("Amount", 0)) if str(r.get("Amount", 0)).isdigit() else 0
#         demands.append({
#             "id": i,
#             "ref_date": r.get("Ref Date"),
#             "ref_no": r.get("Ref No"),
#             "title": r.get("Title"),
#             "amount": amount,
#             "status": r.get("Status")
#         })
#
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
#         years=[selected_year],
#         year=datetime.now().year,
#         role=role,
#         usn=usn
#     )
#
# # ---------------- TIMETABLE ----------------
# @app.route("/timetable")
# def timetable():
#     all_records = fdb.get_timetable()
#     if not all_records:
#         return "No timetable data found."
#
#     first_row = all_records[0]
#     timeslots = [col for col in first_row.keys() if col != "Day/Time"]
#     days = [row["Day/Time"] for row in all_records if row.get("Day/Time")]
#
#     timetable_data = {}
#     for row in all_records:
#         day = row.get("Day/Time")
#         if not day:
#             continue
#         timetable_data[day] = {time: row.get(time, "-") or "-" for time in timeslots}
#
#     return render_template(
#         "timetable.html",
#         student_name=session.get("student_name", "JSS Student"),
#         course=session.get("course", "CSE"),
#         timetable=timetable_data,
#         timeslots=timeslots,
#         days=days,
#         year=datetime.now().year
#     )
#
# @app.route("/staff_timetable")
# def staff_timetable():
#     return timetable()  # same logic
#
# @app.route('/attendance')
# def attendance_page():
#     if 'user_id' not in session:
#         return redirect(url_for('login_page'))
#
#     student_id = session.get('user_id')
#     if session.get('role') == 'parent':
#         student_id = request.args.get("student_id")
#         if not student_id:
#             return "<h3>Please select a student!</h3>"
#
#     all_students = fdb.list_all_students()
#     student_info = next((s for s in all_students if s['USN'] == student_id), {})
#     student_name = student_info.get("Student Name", student_id)
#     default_date = datetime.today().strftime("%Y-%m-%d")
#
#     return render_template(
#         'attendance.html',
#         student_id=student_id,
#         student_name=student_name,
#         default_date=default_date,
#         role=session.get('role')
#     )
#
#
# @app.route('/get_attendance_week/<date_str>', methods=['GET'])
# def get_attendance_week(date_str):
#     # Read student_id from query param OR session
#     student_id = request.args.get("student_id")
#
#     # Fallback: use session only if no student_id provided
#     if not student_id:
#         if 'user_id' not in session:
#             return jsonify({'error': 'Not logged in'}), 401
#         student_id = session['user_id']
#
#     # Fetch from Firestore
#     all_records = fdb.get_attendance(student_id)
#
#     start_date = datetime.strptime(date_str, "%Y-%m-%d")
#     end_date = start_date + timedelta(days=6)
#
#     week_records = [
#         {
#             "date": r['Date'],
#             "time": r['Time'],
#             "subject": r['Subject'],
#             "status": r['Status']
#         }
#         for r in all_records
#         if start_date <= datetime.strptime(r['Date'], "%Y-%m-%d") <= end_date
#     ]
#
#     return jsonify({"records": week_records})
#
# @app.route('/update_attendance', methods=['POST'])
# def update_attendance():
#     data = request.get_json()
#     success = fdb.update_attendance(data['student_id'], data['date'], data['time'], data['subject'], data['status'])
#     if success:
#         return jsonify({'message': 'Attendance updated!'}), 200
#     return jsonify({'error': 'Record not found'}), 404
#
#
# @app.route('/mark_attendance', methods=['POST'])
# def mark_attendance():
#     data = request.get_json()
#     success = fdb.mark_attendance(data['student_id'], data.get('date', datetime.now().strftime('%Y-%m-%d')),
#                                   data['time'], data['subject'], data.get('status', 'Present'))
#     if success:
#         return jsonify({'message': 'Attendance recorded successfully!'}), 201
#     return jsonify({'error': 'Attendance already marked'}), 400
#
# # ---------------- MARKS ----------------
# @app.route('/marks')
# def view_marks():
#     if 'user_id' not in session:
#         return redirect(url_for('login_page'))
#
#     role = session.get('role')
#     all_marks = fdb.get_marks()
#     if role == 'student':
#         all_marks = fdb.get_marks(session.get('usn'))
#     elif role == 'parent':
#         parent_info = fdb.get_parent(session.get('user_id'))
#         linked_usns = [usn.strip() for usn in parent_info.get("Linked Students (USN)", "").split(",") if usn.strip()]
#         all_marks = [m for m in all_marks if m['Student USN'] in linked_usns]
#
#     return render_template('view_marks.html', marks=all_marks, role=role)
#
#
# # ---------------- STAFF ATTENDANCE ----------------
# @app.route('/staff_attendance', methods=['GET', 'POST'])
# def staff_attendance():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     staff_id = session['user_id']
#     staff_info = fdb.get_staff(staff_id)
#     subject = staff_info.get('Subject') if staff_info else None
#
#     students_list = fdb.list_students_by_subject(subject)
#     if request.method == 'POST':
#         date = request.form['date']
#         time_slot = request.form['time_slot']
#         updates = request.form.getlist('attendance_status')  # List of 'Present'/'Absent'
#         usns = request.form.getlist('student_usn')
#
#         for usn, status in zip(usns, updates):
#             fdb.update_attendance(usn, date, time_slot, status)
#
#         return render_template('staff_attendance.html',
#                                subject=subject,
#                                students=students_list,
#                                message="Attendance updated successfully!",
#                                date=date,
#                                time_slot=time_slot)
#
#     return render_template('staff_attendance.html',
#                            subject=subject,
#                            students=students_list)
#
#
# # ---------------- STAFF MARKS UPLOAD ----------------
# @app.route('/upload_marks', methods=['GET', 'POST'])
# def upload_marks():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     staff_id = session['user_id']
#     staff_info = fdb.get_staff(staff_id)
#     subject = staff_info.get('Subject') if staff_info else None
#
#     students_list = fdb.list_students_by_subject(subject)
#     if request.method == 'POST':
#         exam_type = request.form['exam_type']
#         date = request.form['date']
#         usns = request.form.getlist('student_usn')
#         marks = request.form.getlist('marks')
#
#         for usn, mark in zip(usns, marks):
#             fdb.upload_marks(usn, subject, exam_type, date, mark)
#
#         return render_template('upload_marks.html',
#                                subject=subject,
#                                students=students_list,
#                                message="Marks uploaded successfully!")
#
#     return render_template('upload_marks.html', subject=subject, students=students_list)
#
#
# # ---------------- EDIT MARKS ----------------
# @app.route('/edit_marks', methods=['GET', 'POST'])
# def edit_marks():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     staff_id = session['user_id']
#     staff_info = fdb.get_staff(staff_id)
#     subject = staff_info.get('Subject') if staff_info else None
#
#     marks_records = fdb.get_marks_by_subject(subject)
#
#     if request.method == 'POST':
#         record_ids = request.form.getlist('record_id')
#         updated_marks = request.form.getlist('marks')
#
#         for rec_id, mark in zip(record_ids, updated_marks):
#             fdb.update_marks(rec_id, mark)
#
#         return render_template('edit_marks.html',
#                                subject=subject,
#                                marks=marks_records,
#                                message="Marks updated successfully!")
#
#     return render_template('edit_marks.html', subject=subject, marks=marks_records)
#
#
# # ---------------- MCQ MANAGEMENT FOR STAFF ----------------
# @app.route('/mcq_list')
# def mcq_list():
#     if 'user_id' not in session or session.get('role') != 'staff':
#         return redirect(url_for('login_page'))
#
#     staff_id = session['user_id']
#     staff_info = fdb.get_staff(staff_id)
#     subject = staff_info.get('Subject') if staff_info else None
#
#     mcq_tests = fdb.get_mcq_tests(subject)
#     return render_template('mcq_list.html', subject=subject, tests=mcq_tests)
#
#
#
#
#
# #--------------------- Attendance route ---------------------
# @app.route("/staff/attendance", methods=["GET", "POST"])
# def update_student_attendance():
#     staff_id = session.get("user_id")
#     is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
#
#     # ---------------- Session / Role check -----------------------
#     if not staff_id or session.get("role", "").lower() != "staff":
#         if is_ajax:
#             return jsonify({"success": False, "error": "Session expired. Please login again."}), 401
#         flash("Please login first.", "error")
#         return redirect(url_for('login_page'))
#
#     # ---------------- POST (update attendance or No Class) -----------------------
#     if request.method == "POST":
#         if request.form.get("no_class"):
#             flash(f"Marked 'No Class Today' for {session.get('subject','')}", "info")
#             return redirect(url_for('update_student_attendance', date=request.form.get("date")))
#
#         student_id = request.form.get("student")
#         date = request.form.get("date")
#         time_slot = request.form.get("time")
#         subject = request.form.get("subject")
#         status = request.form.get("status") or ""
#
#         if not (student_id and date and time_slot and subject):
#             return jsonify({"success": False, "error": "Missing required fields"}), 400
#
#         timestamp = datetime.now().isoformat()
#         record_id = fdb.get_attendance_record_id(student_id, date, time_slot, subject)
#
#         try:
#             if record_id:
#                 fdb.update_attendance(student_id, date, time_slot, subject, status)
#                 return jsonify({"success": True, "message": "Updated"})
#             else:
#                 fdb.create_attendance(student_id, date, time_slot, subject, status, timestamp)
#                 return jsonify({"success": True, "message": "Row created"})
#         except Exception as e:
#             return jsonify({"success": False, "error": str(e)}), 500
#
#     # ---------------- GET (page load) -----------------------
#     subject = session.get("subject", "")
#     if not subject:
#         staff = fdb.get_staff(staff_id)
#         subject = (staff.get("Subject") or "").strip() if staff else ""
#         session['subject'] = subject
#
#     if not subject:
#         flash("Could not determine your subject.", "error")
#         return redirect(url_for('login_page'))
#
#     current_date = request.args.get('date') or datetime.today().strftime("%Y-%m-%d")
#     weekday = datetime.strptime(current_date, "%Y-%m-%d").strftime("%A")
#
#     # 1️⃣ Get time slots for this staff subject
#     time_slots = fdb.get_time_slots_for_subject(weekday, subject)
#     if not time_slots:
#         flash(f"No timetable found for {weekday}. Attendance cannot be marked.", "warning")
#         records = []
#         return render_template(
#             "update_student_attendance.html",
#             records=records,
#             subject=subject,
#             current_date=current_date,
#             prev_date=(datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d"),
#             next_date=(datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
#             weekday=weekday,
#             timeslots=[]
#         )
#
#     # 2️⃣ Get students enrolled in this subject
#     students = fdb.list_students_by_subject(subject, fallback=True)
#     records = []
#
#     # 3️⃣ Fetch existing attendance
#     existing_attendance = {
#         f"{r['StudentID']}|{r['Date']}|{r['Time']}|{r['Subject'].lower()}": r
#         for r in fdb.get_attendance_by_date_subject(current_date, subject)
#     }
#
#     # 4️⃣ Build records for table
#     for s in students:
#         for slot in time_slots:
#             key = f"{s['StudentID']}|{current_date}|{slot}|{subject.lower()}"
#             if key in existing_attendance:
#                 att = existing_attendance[key]
#                 status = att.get("Status", "")
#                 timestamp = att.get("Timestamp", "")
#             else:
#                 status = ""
#                 timestamp = ""
#                 fdb.create_attendance(s['StudentID'], current_date, slot, subject, status, timestamp)
#
#             records.append({
#                 "StudentID": s['StudentID'],
#                 "StudentName": s['StudentName'],
#                 "Date": current_date,
#                 "Time": slot,
#                 "Subject": subject,
#                 "Status": status,
#                 "Timestamp": timestamp,
#                 "SheetRow": len(records) + 1,
#                 "UpdateStatus": ""
#             })
#
#     return render_template(
#         "update_student_attendance.html",
#         records=records,
#         subject=subject,
#         current_date=current_date,
#         prev_date=(datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d"),
#         next_date=(datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
#         weekday=weekday,
#         timeslots=time_slots
#     )
#
#
#
#
#
#
#
# if __name__ == '__main__':
#     app.run(debug=True)


# app.py
import os
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_from_directory, session, jsonify, flash
)
import firebase_database as fdb  # <-- Our firebase_database module

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER = os.path.join(BASE_DIR, "Templates")  # Folder containing syllabus PDFs

subjects = ["RM", "CN", "TOC", "AI", "SE", "EVS", "WTL"]
time_slots = ["9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"]


# ---------------- HELPERS ----------------
def drive_link_to_direct(url):
    """Converts Google Drive share link to direct-view or thumbnail URL."""
    try:
        if not url:
            return '/static/images/default.jpg'

        file_id = None
        if '/d/' in url:
            file_id = url.split('/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
        else:
            return url

        direct_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w500"
        return direct_url
    except:
        return '/static/images/default.jpg'


def _normalize_time_for_frontend(ts: str) -> str:
    """
    Normalize time string so frontend times array matches backend times.
    Example: "09:00-10:00" -> "9:00-10:00"
    If malformed, return original.
    """
    if not ts or "-" not in ts:
        return ts or ""
    try:
        start, end = ts.split("-", 1)
        sh, sm = start.split(":", 1)
        eh, em = end.split(":", 1)
        start_n = f"{int(sh)}:{sm}"
        end_n = f"{int(eh)}:{em}"
        return f"{start_n}-{end_n}"
    except Exception:
        return ts


def _normalize_status_for_frontend(st: str) -> str:
    """Capitalize status consistently: 'present' -> 'Present'."""
    if not st:
        return ""
    return str(st).strip().capitalize()


# ---------------- ROUTES ----------------

# --- Login Page ---
@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['username']
    password = request.form['password']
    role_selected = request.form['role']

    user = fdb.get_user(user_id)
    if not user or user.get("Password") != password:
        return "<h3>Invalid ID or Password! Please try again.</h3>"

    if user.get("Role", "").lower() != role_selected.lower():
        return "<h3>Role mismatch. Please choose the correct role.</h3>"

    session['user_id'] = user_id
    session['role'] = user.get("Role")

    # Student
    if session['role'].lower() == "student":
        student_info = fdb.get_student(user_id)
        if student_info:
            session['usn'] = student_info.get("USN")
            session['student_name'] = student_info.get("Student Name")
            session['course'] = student_info.get("Course")
            session['student_id'] = user_id
        else:
            session['usn'] = user_id
            session['student_name'] = user_id
            session['course'] = "B.E CSE"
            session['student_id'] = user_id

    # Staff
    elif session['role'].lower() == "staff":
        staff_info = fdb.get_staff(user_id)
        session['staff_id'] = user_id
        if staff_info:
            session['staff_name'] = staff_info.get("Professor Name")
            session['subject'] = staff_info.get("Subject")
        else:
            session['staff_name'] = user_id
            session['subject'] = None

    # Redirect based on role
    if session['role'].lower() == 'student':
        return redirect(url_for('student_dashboard'))
    elif session['role'].lower() == 'staff':
        return redirect(url_for('staff_dashboard'))
    elif session['role'].lower() == 'parent':
        return redirect(url_for('parent_dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username'].strip()
        new_password = request.form['new_password'].strip()
        user = fdb.get_user(username)
        if user:
            fdb.update_password(username, new_password)
            flash(f"✅ Password updated successfully for {username}!", "success")
            return redirect(url_for('reset_password'))
        flash("❌ Username not found. Please try again.", "error")
        return redirect(url_for('reset_password'))
    return render_template('reset_password.html')


# ---------------- STUDENT DASHBOARD ----------------
@app.route('/student')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login_page'))

    student_info = fdb.get_student(session['user_id'])
    default_image = '/static/images/default.jpg'
    if student_info:
        photo_url = student_info.get('PhotoURL', '').strip()
        student_image_url = drive_link_to_direct(photo_url) if photo_url else default_image
        return render_template('student_dashboard.html',
                               student=student_info,
                               student_image_url=student_image_url)
    else:
        return render_template('student_dashboard.html',
                               student={
                                   "Student Name": session['user_id'],
                                   "USN": session['user_id'],
                                   "Course": "B.E CSE",
                                   "Section": ""
                               },
                               student_image_url=default_image)


# ---------------- STAFF DASHBOARD ----------------
@app.route('/staff')
def staff_dashboard():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_info = fdb.get_staff(session['user_id'])
    if not staff_info:
        return render_template('staff_dashboard.html', error_message="Staff details not found.")

    photo_url = drive_link_to_direct(staff_info.get('PhotoURL', ''))
    return render_template('staff_dashboard.html',
                           staff_name=staff_info.get("Professor Name"),
                           staff_id=staff_info.get("Staff ID"),
                           subject=staff_info.get("Subject"),
                           department=staff_info.get("Department"),
                           photo_url=photo_url)


# ---------------- PARENT DASHBOARD ----------------
@app.route('/parent')
def parent_dashboard():
    if 'user_id' not in session or session.get('role') != 'parent':
        return redirect(url_for('login_page'))

    parent_info = fdb.get_parent(session['user_id'])
    if not parent_info:
        return "<h3>No parent record found!</h3>"

    linked_usns = [usn.strip() for usn in parent_info.get("Linked Students (USN)", "").split(",") if usn.strip()]
    if not linked_usns:
        return "<h3>No students linked to this parent!</h3>"

    students_info = [fdb.get_student(usn) for usn in linked_usns]
    selected_usn = request.args.get("student_usn") or linked_usns[0]
    selected_student = next((s for s in students_info if s["USN"] == selected_usn), students_info[0])
    default_image = '/static/images/default.jpg'
    student_image_url = drive_link_to_direct(selected_student.get('PhotoURL', '')) if selected_student.get('PhotoURL') else default_image

    return render_template('parent_dashboard.html',
                           parent_name=parent_info.get("Parent Name"),
                           students=students_info,
                           selected_student=selected_student,
                           student_image_url=student_image_url,
                           year=datetime.now().year)


# ---------------- SYLLABUS ----------------
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


@app.route('/staff_syllabus', methods=['GET', 'POST'])
def staff_syllabus_page():
    return syllabus_page()  # same logic


# ---------------- ASSESSMENT ----------------
@app.route('/assessment')
def assessment_page():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login_page'))

    all_tests = fdb.get_mcq_tests()
    all_tests.sort(key=lambda x: x.get('Date', ''))
    return render_template('assessment.html', tests=all_tests)


@app.route('/upload_mcq', methods=['GET', 'POST'])
def upload_mcq():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_id = session['user_id']
    staff_info = fdb.get_staff(staff_id)
    subject = staff_info.get('Subject') if staff_info else None
    lecturer_name = staff_info.get("Professor Name") if staff_info else staff_id

    if request.method == 'POST':
        date = request.form['date']
        time_limit = request.form['time_limit']
        test_link = request.form['test_link']
        button_text = request.form.get('button_text', 'Take Test')

        fdb.upload_mcq_test(subject, lecturer_name, date, time_limit, test_link, button_text)
        return render_template('upload_mcq.html', message="Test uploaded successfully!", success=True, subject=subject)

    return render_template('upload_mcq.html', subject=subject)

@app.route("/fees")
def show_fees():
    # Determine USN
    usn = request.args.get("usn") or session.get("usn")

    if not usn:
        return redirect(url_for("login_page"))

    # Determine user role
    role = request.args.get("role") or session.get("role") or "student"

    # Fetch all fee records for the student from Firestore
    student_records = fdb.get_fees(usn)

    if not student_records:
        return f"No fee records found for USN: {usn}"

    # 🔥 Build list of year/semester values (MULTIPLE YEARS)
    years = sorted(
        list(set(r.get("Semester", "").strip() for r in student_records if r.get("Semester")))
    )

    # Default selected year = first year OR request value
    default_year = years[0] if years else ""
    selected_year = request.args.get("year", default_year)

    # Filter records for selected year
    filtered_records = [
        r for r in student_records
        if r.get("Semester", "").strip() == selected_year
    ]

    # Totals
    total_fees = sum(
        int(r.get("Amount", 0))
        for r in filtered_records
        if str(r.get("Amount", "0")).isdigit()
    )

    paid_fees = sum(
        int(r.get("Amount", 0))
        for r in filtered_records
        if str(r.get("Amount", "0")).isdigit() and r.get("Status", "").strip().lower() == "done"
    )

    pending_fees = total_fees - paid_fees

    # Prepare demands
    demands = []
    for i, r in enumerate(filtered_records, start=1):
        amount = int(r.get("Amount", 0)) if str(r.get("Amount", 0)).isdigit() else 0
        demands.append({
            "id": i,
            "ref_date": r.get("Ref Date"),
            "ref_no": r.get("Ref No"),
            "title": r.get("Title"),
            "amount": amount,
            "status": r.get("Status")
        })

    # Student info
    student_name = request.args.get("student_name") or \
                   session.get("student_name", student_records[0].get("Student Name"))

    course = request.args.get("course") or \
             session.get("course", student_records[0].get("Course"))

    return render_template(
        "fees.html",
        student_name=student_name,
        course=course,
        demands=demands,
        total_fees=total_fees,
        paid_fees=paid_fees,
        pending_fees=pending_fees,
        sem_or_year=selected_year,
        years=years,                 # 🔥 MULTI-YEAR SUPPORT FIXED
        year=datetime.now().year,
        role=role,
        usn=usn
    )


@app.route("/timetable")
def timetable():
    all_records = fdb.get_timetable()

    if not all_records:
        return "No timetable data found."

    # Extract all unique timeslots from the "Slots" maps
    timeslots = sorted({time for row in all_records for time in row.get("Slots", {}).keys()})

    # Extract all days
    days = [row["Day"] for row in all_records]

    # Build timetable with day → timeslot → subject
    timetable_data = {}

    for row in all_records:
        day = row["Day"]
        slots = row.get("Slots", {})

        timetable_data[day] = {}
        for time in timeslots:
            value = slots.get(time, "NO CLASS")
            timetable_data[day][time] = value

    return render_template(
        "timetable.html",
        student_name=session.get("student_name", "JSS Student"),
        course=session.get("course", "CSE"),
        timetable=timetable_data,
        timeslots=timeslots,
        days=days
    )


@app.route("/staff_timetable")
def staff_timetable():
    return timetable()  # same logic

# ---------------- STUDENT ATTENDANCE PAGE ----------------
@app.route('/attendance')
def attendance_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    # Prefer explicit student_id query param (for parent view), else session
    student_id = request.args.get("student_id") or session.get('user_id')

    # If parent role, require student_id param
    if session.get('role') == 'parent':
        if not request.args.get("student_id"):
            return "<h3>Please select a student!</h3>"

    all_students = fdb.list_all_students()
    student_info = next((s for s in all_students if s['USN'] == student_id), {})
    student_name = student_info.get("Student Name", student_id)
    default_date = datetime.today().strftime("%Y-%m-%d")

    # NOTE: do NOT cache attendance in session. Student page fetches via AJAX from /get_attendance_week
    return render_template(
        'attendance.html',
        student_id=student_id,
        student_name=student_name,
        default_date=default_date,
        role=session.get('role')
    )


@app.route('/get_attendance_week/<date_str>', methods=['GET'])
def get_attendance_week(date_str):
    """
    Returns normalized attendance records for the 7-day window ending on date_str.
    Accepts query param student_id (preferred) or falls back to session user_id.
    """
    student_id = request.args.get("student_id")
    if not student_id:
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        student_id = session['user_id']

    # Fetch fresh attendance from Firestore
    all_records = fdb.get_attendance(student_id)

    end_date = datetime.strptime(date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=6)

    week_records = []
    for r in all_records:
        rd = r.get('Date')
        try:
            record_date = datetime.strptime(rd, "%Y-%m-%d")
        except Exception:
            # skip bad dates
            continue
        if not (start_date <= record_date <= end_date):
            continue

        time_slot = _normalize_time_for_frontend(r.get('Time', ''))
        status = _normalize_status_for_frontend(r.get('Status', ''))
        subject = r.get('Subject') or '-'

        week_records.append({
            "date": record_date.strftime("%Y-%m-%d"),
            "time": time_slot,
            "subject": subject,
            "status": status
        })

    # Sort by date then time (string sort ok because times normalized to H:MM-H:MM)
    week_records.sort(key=lambda x: (x['date'], x['time']))
    return jsonify({"records": week_records})


@app.route('/update_attendance', methods=['POST'])
def update_attendance():
    """
    Generic JSON API to update a record (used by other UIs if needed).
    Expects JSON body: { student_id, date, time, subject, status }
    """
    data = request.get_json() or {}
    required = ('student_id', 'date', 'time', 'subject', 'status')
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400

    # Normalize status before saving
    status = _normalize_status_for_frontend(data['status'])
    success = fdb.update_attendance(data['student_id'], data['date'], data['time'], data['subject'], status)
    if success:
        return jsonify({'message': 'Attendance updated!'}), 200
    return jsonify({'error': 'Record not found'}), 404


@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """
    Generic JSON API to mark attendance (creates or overwrites deterministic doc)
    Expects JSON: { student_id, date, time, subject, status? }
    """
    data = request.get_json() or {}
    if not data.get('student_id') or not data.get('time') or not data.get('subject'):
        return jsonify({'error': 'Missing fields'}), 400

    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    status = _normalize_status_for_frontend(data.get('status', 'Present'))
    success = fdb.mark_attendance(data['student_id'], date, data['time'], data['subject'], status)
    if success:
        return jsonify({'message': 'Attendance recorded successfully!'}), 201
    return jsonify({'error': 'Attendance could not be recorded'}), 400



@app.route('/marks')
def view_marks():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    role = session.get('role')

    if role == 'student':
        usn = session.get('usn')   # FIXED
        marks = fdb.get_marks(usn)

    elif role == 'parent':
        parent_info = fdb.get_parent(session.get('user_id'))

        linked_usns = [
            u.strip()
            for u in parent_info.get("Linked Students (USN)", "").split(",")
            if u.strip()
        ]

        marks = []
        for u in linked_usns:
            marks.extend(fdb.get_marks(u))

    else:
        # staff / admin → view all
        marks = fdb.get_marks()

    return render_template('view_marks.html', marks=marks, role=role)

@app.route("/staff/attendance", methods=["GET", "POST"])
def update_student_attendance():
    staff_id = session.get("user_id")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # ---------------- Session / Role check -----------------------
    if not staff_id or session.get("role", "").lower() != "staff":
        if is_ajax:
            return jsonify({"success": False, "error": "Session expired. Please login again."}), 401
        flash("Please login first.", "error")
        return redirect(url_for('login_page'))

    # ---------------- POST (update attendance or No Class) -----------------------
    if request.method == "POST":
        if request.form.get("no_class"):
            flash(f"Marked 'No Class Today' for {session.get('subject','')}", "info")
            return redirect(url_for('update_student_attendance', date=request.form.get("date")))

        student_id = request.form.get("student")
        date = request.form.get("date")
        time_slot = request.form.get("time")
        subject = request.form.get("subject")
        status = request.form.get("status") or ""

        if not (student_id and date and time_slot and subject):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        timestamp = datetime.now().isoformat()
        # Normalize status before saving
        status = _normalize_status_for_frontend(status)

        record_id = fdb.get_attendance_record_id(student_id, date, time_slot, subject)

        try:
            if record_id:
                fdb.update_attendance(student_id, date, time_slot, subject, status)
                return jsonify({"success": True, "message": "Updated"})
            else:
                fdb.create_attendance(student_id, date, time_slot, subject, status, timestamp)
                return jsonify({"success": True, "message": "Row created"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ---------------- GET (page load) -----------------------
    subject = session.get("subject", "")
    if not subject:
        staff = fdb.get_staff(staff_id)
        subject = (staff.get("Subject") or "").strip() if staff else ""
        session['subject'] = subject

    if not subject:
        flash("Could not determine your subject.", "error")
        return redirect(url_for('login_page'))

    current_date = request.args.get('date') or datetime.today().strftime("%Y-%m-%d")
    weekday = datetime.strptime(current_date, "%Y-%m-%d").strftime("%A")

    # 1️⃣ Get time slots for this staff subject
    time_slots_for_staff = fdb.get_time_slots_for_subject(weekday, subject)
    if not time_slots_for_staff:
        flash(f"No timetable found for {weekday}. Attendance cannot be marked.", "warning")
        records = []
        return render_template(
            "update_student_attendance.html",
            records=records,
            subject=subject,
            current_date=current_date,
            prev_date=(datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d"),
            next_date=(datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
            weekday=weekday,
            timeslots=[]
        )

    # 2️⃣ Get students enrolled in this subject
    students = fdb.list_students_by_subject(subject, fallback=True)
    records = []

    # 3️⃣ Fetch existing attendance
    existing_attendance = {
        f"{r['StudentID']}|{r['Date']}|{r['Time']}|{r['Subject'].lower()}": r
        for r in fdb.get_attendance_by_date_subject(current_date, subject)
    }

    # 4️⃣ Build records for table (ensures at least one doc exists for UI)
    for s in students:
        for slot in time_slots_for_staff:
            key = f"{s['StudentID']}|{current_date}|{slot}|{subject.lower()}"
            if key in existing_attendance:
                att = existing_attendance[key]
                status = att.get("Status", "")
                timestamp = att.get("Timestamp", "")
            else:
                status = ""
                timestamp = ""
                # create deterministic doc so later updates use same doc id
                fdb.create_attendance(s['StudentID'], current_date, slot, subject, status, timestamp)

            records.append({
                "StudentID": s['StudentID'],
                "StudentName": s['StudentName'],
                "Date": current_date,
                "Time": slot,
                "Subject": subject,
                "Status": status,
                "Timestamp": timestamp,
                "SheetRow": len(records) + 1,
                "UpdateStatus": ""
            })

    return render_template(
        "update_student_attendance.html",
        records=records,
        subject=subject,
        current_date=current_date,
        prev_date=(datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d"),
        next_date=(datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
        weekday=weekday,
        timeslots=time_slots_for_staff
    )


# ---------------- STAFF MARKS UPLOAD ----------------
@app.route('/upload_marks', methods=['GET', 'POST'])
def upload_marks():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_id = session['user_id']
    staff_info = fdb.get_staff(staff_id)
    subject = staff_info.get('Subject') if staff_info else None

    students_list = fdb.list_students_by_subject(subject)
    if request.method == 'POST':
        exam_type = request.form['exam_type']
        date = request.form['date']
        usns = request.form.getlist('student_usn')
        marks = request.form.getlist('marks')

        for usn, mark in zip(usns, marks):
            fdb.upload_marks(usn, subject, exam_type, date, mark)

        return render_template('upload_marks.html',
                               subject=subject,
                               students=students_list,
                               message="Marks uploaded successfully!")

    return render_template('upload_marks.html', subject=subject, students=students_list)


# ---------------- EDIT MARKS ----------------
@app.route('/edit_marks', methods=['GET', 'POST'])
def edit_marks():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_id = session['user_id']
    staff_info = fdb.get_staff(staff_id)
    subject = staff_info.get('Subject') if staff_info else None

    marks_records = fdb.get_marks_by_subject(subject)

    if request.method == 'POST':
        record_ids = request.form.getlist('record_id')
        updated_marks = request.form.getlist('marks')

        for rec_id, mark in zip(record_ids, updated_marks):
            fdb.update_marks(rec_id, mark)

        return render_template('edit_marks.html',
                               subject=subject,
                               marks=marks_records,
                               message="Marks updated successfully!")

    return render_template('edit_marks.html', subject=subject, marks=marks_records)


# ---------------- MCQ MANAGEMENT FOR STAFF ----------------
@app.route('/mcq_list')
def mcq_list():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))

    staff_id = session['user_id']
    staff_info = fdb.get_staff(staff_id)
    subject = staff_info.get('Subject') if staff_info else None

    mcq_tests = fdb.get_mcq_tests(subject)
    return render_template('mcq_list.html', subject=subject, tests=mcq_tests)


# --------------------- End ---------------------
if __name__ == '__main__':
    app.run(debug=True)
