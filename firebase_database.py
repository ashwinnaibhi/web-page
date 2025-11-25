
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("firebase_admin.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ------------------ USERS ------------------
def get_user(username: str):
    doc_ref = db.collection("Users").document(username)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None

# ------------------ STUDENTS ------------------
def get_student(usn: str):
    doc_ref = db.collection("Students").document(usn)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None


# ------------------ STAFF ------------------
def get_staff(staff_id: str):
    doc_ref = db.collection("Teachers").document(staff_id)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None


def get_time_slots_for_subject(weekday, subject):
    """
    Returns list of time slots for a given weekday and subject.
    Works with Firestore timetable where Day can be a field or document ID.
    """
    weekday = weekday.strip().lower()
    subject = subject.strip().lower()
    print(f"[DEBUG] Looking for timetable for weekday: '{weekday}', subject: '{subject}'")

    slots_map = {}
    docs = db.collection("Timetables").stream()
    for d in docs:
        data = d.to_dict() or {}
        # Day from field or fallback to document ID
        doc_day = (data.get("Day", "") or d.id).strip().lower()
        if doc_day == weekday:
            slots_map = data.get("Slots", {})
            break

    if not slots_map:
        print(f"[DEBUG] ❌ No timetable slots found for weekday '{weekday}'")
        return []

    print(f"[DEBUG] Found slots map: {slots_map}")

    matching_slots = []
    for time_slot, sub in slots_map.items():
        if not sub:
            continue
        if str(sub).strip().lower() == subject:
            matching_slots.append(time_slot.strip())

    print(f"[DEBUG] Matching slots for subject '{subject}': {matching_slots}")
    return matching_slots


def list_students_by_subject(subject, fallback=True):
    """
    Return list of students enrolled in the given subject.
    If fallback=True, includes students with missing 'Subjects' field.
    """
    subject = subject.strip().lower()
    print(f"[DEBUG] Listing students for subject: '{subject}'")

    students = []
    docs = db.collection("Students").stream()
    for d in docs:
        data = d.to_dict() or {}
        student_id = data.get("USN")
        student_name = data.get("Student Name", "Unknown")
        subs = data.get("Subjects")

        if subs:
            subs_lower = [s.strip().lower() for s in subs if s.strip()]
            if subject in subs_lower:
                students.append({"StudentID": student_id, "StudentName": student_name})
                print(f"[DEBUG] Added student {student_id} ({student_name}) for subject '{subject}'")
        elif fallback:
            students.append({"StudentID": student_id, "StudentName": student_name})
            print(f"[DEBUG] Added student {student_id} ({student_name}) (fallback)")

    print(f"[DEBUG] Total students returned for '{subject}': {len(students)}")
    return students

def list_all_students():
    """
    Return all student records.
    """
    students = []
    docs = db.collection("Students").stream()
    for d in docs:
        data = d.to_dict() or {}
        students.append({
            "USN": data.get("USN"),
            "Student Name": data.get("Student Name"),
            "Course": data.get("Course"),
            "Section": data.get("Section")
        })
    return students


# ------------------ ATTENDANCE HELPERS ------------------

def generate_doc_id(student_id: str, date: str, time: str, subject: str) -> str:
    """
    Generates a unique and readable document ID for attendance.
    Format: studentID_date_time_subject
    """
    time_safe = time.replace(":", "-") if time else "NA"
    subject_safe = subject.replace(" ", "_") if subject else "NA"
    return f"{student_id}_{date}_{time_safe}_{subject_safe}"

def get_attendance(student_id: str):
    """
    Returns all attendance records for a given student.
    Each record includes document ID as 'RecordID'.
    """
    records = []
    docs = db.collection("Attendance") \
             .where("StudentID", "==", student_id).stream()
    for doc in docs:
        data = doc.to_dict()
        data["RecordID"] = doc.id
        records.append(data)
    return records

def get_attendance_by_date_subject(date: str, subject: str):
    """
    Return list of attendance records for a given date and subject.
    Each record includes document ID as 'RecordID'
    """
    records = []
    docs = db.collection("Attendance") \
        .where("Date", "==", date) \
        .where("Subject", "==", subject).stream()
    for doc in docs:
        data = doc.to_dict()
        data["RecordID"] = doc.id
        records.append(data)
    return records

def get_attendance_record_id(student_id: str, date: str, time_slot: str, subject: str):
    """
    Return the document ID of an existing attendance record, or None.
    """
    docs = db.collection("Attendance") \
        .where("StudentID", "==", student_id) \
        .where("Date", "==", date) \
        .where("Time", "==", time_slot) \
        .where("Subject", "==", subject).stream()
    for doc in docs:
        return doc.id
    return None

def mark_attendance(student_id: str, date: str, time: str, subject: str, status="Present") -> bool:
    """
    Marks attendance for a student. Creates or updates the record.
    """
    doc_id = generate_doc_id(student_id, date, time, subject)
    doc_ref = db.collection("Attendance").document(doc_id)
    doc_ref.set({
        "StudentID": student_id,
        "Date": date,
        "Time": time,
        "Subject": subject,
        "Status": status
    })
    return True

def update_attendance(student_id: str, date: str, time: str, subject: str, status: str) -> bool:
    """
    Updates an existing attendance record. Returns False if record not found.
    """
    doc_id = generate_doc_id(student_id, date, time, subject)
    doc_ref = db.collection("Attendance").document(doc_id)
    if doc_ref.get().exists:
        doc_ref.update({"Status": status})
        return True
    return False

def create_attendance(student_id: str, date: str, time: str, subject: str, status: str, timestamp: str):
    """
    Create a new attendance record with deterministic document ID.
    """
    doc_id = generate_doc_id(student_id, date, time, subject)
    db.collection("Attendance").document(doc_id).set({
        "StudentID": student_id,
        "Date": date,
        "Time": time,
        "Subject": subject,
        "Status": status,
        "Timestamp": timestamp
    })