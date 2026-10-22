from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import os
from datetime import date, timedelta
import json
import random

app = Flask(__name__)
app.secret_key = 'edutrack_india_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'attendance.db')

# ─────────────────────────────────────────────
#  Database Helpers
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # ── Tables ──────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            course   TEXT NOT NULL,        -- BTech / BCA
            branch   TEXT NOT NULL,        -- CSE / IT / ECE / MCA …
            semester INTEGER NOT NULL,     -- 1-8 (BTech), 1-6 (BCA)
            section  TEXT NOT NULL,        -- A / B / C
            subject  TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(course, branch, semester, section, subject)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no    TEXT NOT NULL UNIQUE,
            name       TEXT NOT NULL,
            class_id   INTEGER NOT NULL,
            email      TEXT,
            phone      TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (class_id) REFERENCES classes(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            class_id   INTEGER NOT NULL,
            date       TEXT NOT NULL,
            status     TEXT NOT NULL CHECK(status IN ('Present','Absent','Late')),
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(student_id, date),
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (class_id)   REFERENCES classes(id)
        )
    ''')

    # ── Seed only if empty ───────────────────
    c.execute("SELECT COUNT(*) FROM classes")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    # ── Classes (course, branch, sem, section, subject) ──
    classes_data = [
        # ─── BTech – CSE (Sem 3, Sec A & B) ───
        ('BTech', 'CSE', 3, 'A', 'Data Structures & Algorithms'),
        ('BTech', 'CSE', 3, 'B', 'Data Structures & Algorithms'),
        # ─── BTech – CSE (Sem 5, Sec A) ───────
        ('BTech', 'CSE', 5, 'A', 'Operating Systems'),
        ('BTech', 'CSE', 5, 'A', 'Database Management Systems'),
        ('BTech', 'CSE', 5, 'A', 'Computer Networks'),
        # ─── BTech – CSE (Sem 7, Sec A) ───────
        ('BTech', 'CSE', 7, 'A', 'Machine Learning'),
        ('BTech', 'CSE', 7, 'A', 'Cloud Computing'),
        # ─── BTech – ECE (Sem 4, Sec A) ───────
        ('BTech', 'ECE', 4, 'A', 'Digital Signal Processing'),
        ('BTech', 'ECE', 4, 'A', 'Microprocessors & Microcontrollers'),
        # ─── BTech – IT  (Sem 4, Sec A) ───────
        ('BTech', 'IT',  4, 'A', 'Web Technologies'),
        ('BTech', 'IT',  4, 'A', 'Software Engineering'),
        # ─── BTech – Mech (Sem 2, Sec A) ──────
        ('BTech', 'Mech', 2, 'A', 'Engineering Mechanics'),
        ('BTech', 'Mech', 2, 'A', 'Engineering Mathematics II'),
        # ─── BCA (Sem 2, 4, 6) ────────────────
        ('BCA',  'CS',  2, 'A', 'Programming in C++'),
        ('BCA',  'CS',  4, 'A', 'Python Programming'),
        ('BCA',  'CS',  4, 'A', 'RDBMS'),
        ('BCA',  'CS',  6, 'A', 'Advanced Java'),
        ('BCA',  'CS',  6, 'A', 'Mobile Application Development'),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO classes (course, branch, semester, section, subject) VALUES (?,?,?,?,?)",
        classes_data
    )
    conn.commit()

    # ── Fetch class IDs ──────────────────────
    all_classes = {
        (r['course'], r['branch'], r['semester'], r['section'], r['subject']): r['id']
        for r in conn.execute("SELECT * FROM classes").fetchall()
    }

    # ── Indian Student Names ─────────────────
    indian_names = [
        # Male
        "Aarav Sharma", "Arjun Verma", "Rohan Gupta", "Karan Patel",
        "Vikram Singh", "Aditya Kumar", "Rahul Mehta", "Siddharth Joshi",
        "Nikhil Yadav", "Pranav Nair", "Harsh Agarwal", "Vivek Tiwari",
        "Akash Mishra", "Sumit Pandey", "Mohit Chauhan", "Deepak Rajput",
        "Gaurav Bhatt", "Ritesh Srivastava", "Yash Dubey", "Sachin Thakur",
        "Ankit Rawat", "Shubham Rao", "Ravi Chandra", "Ajay Malhotra",
        "Tarun Bose", "Rishabh Kapoor", "Manish Pillai", "Tushar Saxena",
        "Suraj Reddy", "Kartik Ghosh",
        # Female
        "Priya Sharma", "Anjali Gupta", "Sneha Patel", "Divya Singh",
        "Pooja Mehta", "Neha Verma", "Kavya Nair", "Shreya Joshi",
        "Ananya Kumar", "Ritu Yadav", "Swati Agarwal", "Meera Tiwari",
        "Kritika Mishra", "Simran Pandey", "Nisha Chauhan", "Sana Rajput",
        "Tanvi Bhatt", "Pallavi Srivastava", "Ishita Dubey", "Meenal Thakur",
        "Aparna Rawat", "Aishwarya Rao", "Lakshmi Chandra", "Deepika Malhotra",
        "Varsha Bose", "Aarti Kapoor", "Madhuri Pillai", "Gauri Saxena",
        "Suchitra Reddy", "Bhavana Ghosh",
    ]
    random.shuffle(indian_names)

    # ── Assign students to classes ───────────
    # Key:  (course, branch, sem, sec, subject) → class_id
    class_groups = {
        'BTech_CSE_3A': all_classes[('BTech','CSE',3,'A','Data Structures & Algorithms')],
        'BTech_CSE_3B': all_classes[('BTech','CSE',3,'B','Data Structures & Algorithms')],
        'BTech_CSE_5A_OS':   all_classes[('BTech','CSE',5,'A','Operating Systems')],
        'BTech_CSE_5A_DBMS': all_classes[('BTech','CSE',5,'A','Database Management Systems')],
        'BTech_CSE_5A_CN':   all_classes[('BTech','CSE',5,'A','Computer Networks')],
        'BTech_CSE_7A_ML':   all_classes[('BTech','CSE',7,'A','Machine Learning')],
        'BTech_CSE_7A_CC':   all_classes[('BTech','CSE',7,'A','Cloud Computing')],
        'BTech_ECE_4A_DSP':  all_classes[('BTech','ECE',4,'A','Digital Signal Processing')],
        'BTech_ECE_4A_MP':   all_classes[('BTech','ECE',4,'A','Microprocessors & Microcontrollers')],
        'BTech_IT_4A_WT':    all_classes[('BTech','IT',4,'A','Web Technologies')],
        'BTech_IT_4A_SE':    all_classes[('BTech','IT',4,'A','Software Engineering')],
        'BTech_Mech_2A_EM':  all_classes[('BTech','Mech',2,'A','Engineering Mechanics')],
        'BTech_Mech_2A_MA':  all_classes[('BTech','Mech',2,'A','Engineering Mathematics II')],
        'BCA_CS_2A_CPP': all_classes[('BCA','CS',2,'A','Programming in C++')],
        'BCA_CS_4A_PY':  all_classes[('BCA','CS',4,'A','Python Programming')],
        'BCA_CS_4A_RDB': all_classes[('BCA','CS',4,'A','RDBMS')],
        'BCA_CS_6A_JAV': all_classes[('BCA','CS',6,'A','Advanced Java')],
        'BCA_CS_6A_MOB': all_classes[('BCA','CS',6,'A','Mobile Application Development')],
    }

    # Students per group: roll_prefix, name_slice, primary_class_id
    student_groups = [
        # BTech CSE Sem 3 Sec A – 8 students
        ('BCSE3A', indian_names[0:8],   class_groups['BTech_CSE_3A']),
        # BTech CSE Sem 3 Sec B – 7 students
        ('BCSE3B', indian_names[8:15],  class_groups['BTech_CSE_3B']),
        # BTech CSE Sem 5 Sec A – 7 students
        ('BCSE5A', indian_names[15:22], class_groups['BTech_CSE_5A_OS']),
        # BTech CSE Sem 7 Sec A – 5 students
        ('BCSE7A', indian_names[22:27], class_groups['BTech_CSE_7A_ML']),
        # BTech ECE Sem 4 Sec A – 5 students
        ('BECE4A', indian_names[27:32], class_groups['BTech_ECE_4A_DSP']),  # wrap-around safe since we have 60
        # BTech IT Sem 4 Sec A – 5 students
        ('BIT4A',  indian_names[32:37], class_groups['BTech_IT_4A_WT']),
        # BTech Mech Sem 2 Sec A – 4 students
        ('BME2A',  indian_names[37:41], class_groups['BTech_Mech_2A_EM']),
        # BCA Sem 2 Sec A – 5 students
        ('BCA2A',  indian_names[41:46], class_groups['BCA_CS_2A_CPP']),
        # BCA Sem 4 Sec A – 5 students
        ('BCA4A',  indian_names[46:51], class_groups['BCA_CS_4A_PY']),
        # BCA Sem 6 Sec A – 5 students
        ('BCA6A',  indian_names[51:56], class_groups['BCA_CS_6A_JAV']),
    ]

    student_rows = []
    for prefix, names, cid in student_groups:
        for i, name in enumerate(names, 1):
            roll = f"{prefix}{i:03d}"
            email = name.lower().replace(' ', '.') + "@college.edu.in"
            phone = f"9{random.randint(100000000,999999999)}"
            student_rows.append((roll, name, cid, email, phone))

    c.executemany(
        "INSERT OR IGNORE INTO students (roll_no, name, class_id, email, phone) VALUES (?,?,?,?,?)",
        student_rows
    )
    conn.commit()

    # ── Seed 14 days attendance ──────────────
    c.execute("SELECT id, class_id FROM students")
    all_students = c.fetchall()
    statuses = ['Present', 'Present', 'Present', 'Present', 'Absent', 'Late']
    for days_ago in range(14, 0, -1):
        d = (date.today() - timedelta(days=days_ago)).isoformat()
        for s in all_students:
            st = random.choice(statuses)
            try:
                c.execute(
                    "INSERT INTO attendance (student_id, class_id, date, status) VALUES (?,?,?,?)",
                    (s['id'], s['class_id'], d, st)
                )
            except Exception:
                pass

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.route('/')
def dashboard():
    conn  = get_db()
    today = date.today().isoformat()

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_classes  = conn.execute("SELECT COUNT(DISTINCT course||branch||semester||section) FROM classes").fetchone()[0]
    present_today  = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Present'", (today,)).fetchone()[0]
    absent_today   = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Absent'",  (today,)).fetchone()[0]
    late_today     = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Late'",    (today,)).fetchone()[0]
    marked_today   = conn.execute("SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date=?",    (today,)).fetchone()[0]

    # 7-day trend
    seven_days_data = []
    for i in range(6, -1, -1):
        d   = (date.today() - timedelta(days=i)).isoformat()
        row = conn.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present "
            "FROM attendance WHERE date=?", (d,)
        ).fetchone()
        rate = round((row['present'] / row['total'] * 100), 1) if row['total'] else 0
        seven_days_data.append({'date': d, 'rate': rate})

    # Course-wise today
    class_stats = conn.execute('''
        SELECT c.course, c.branch, c.semester, c.section, c.subject,
               COUNT(a.id) as total,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as present
        FROM classes c
        LEFT JOIN attendance a ON c.id=a.class_id AND a.date=?
        GROUP BY c.id
        ORDER BY c.course, c.branch, c.semester, c.section
    ''', (today,)).fetchall()

    # Recent activity
    recent = conn.execute('''
        SELECT a.date, a.status,
               s.name as student_name, s.roll_no,
               c.course, c.branch, c.semester, c.section, c.subject
        FROM attendance a
        JOIN students s ON a.student_id=s.id
        JOIN classes  c ON a.class_id=c.id
        ORDER BY a.created_at DESC LIMIT 10
    ''').fetchall()

    conn.close()
    return render_template('dashboard.html',
        total_students=total_students,
        total_classes=total_classes,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        marked_today=marked_today,
        seven_days_data=json.dumps(seven_days_data),
        class_stats=class_stats,
        recent=recent,
        today=today
    )


@app.route('/students')
def students():
    conn         = get_db()
    class_filter = request.args.get('class_id', '')
    course_filter= request.args.get('course', '')
    search       = request.args.get('search', '')

    query = '''
        SELECT s.*, c.course, c.branch, c.semester, c.section, c.subject,
               COUNT(CASE WHEN a.status='Present' THEN 1 END) as present_count,
               COUNT(a.id) as total_count
        FROM students s
        JOIN classes c ON s.class_id=c.id
        LEFT JOIN attendance a ON s.id=a.student_id
    '''
    params, conds = [], []
    if class_filter:
        conds.append("s.class_id=?"); params.append(class_filter)
    if course_filter:
        conds.append("c.course=?");   params.append(course_filter)
    if search:
        conds.append("(s.name LIKE ? OR s.roll_no LIKE ?)"); params += [f'%{search}%', f'%{search}%']
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " GROUP BY s.id ORDER BY c.course, c.branch, c.semester, s.roll_no"

    students_list = conn.execute(query, params).fetchall()
    classes       = conn.execute(
        "SELECT * FROM classes ORDER BY course, branch, semester, section, subject"
    ).fetchall()
    courses       = conn.execute("SELECT DISTINCT course FROM classes ORDER BY course").fetchall()
    conn.close()
    return render_template('students.html',
        students=students_list, classes=classes, courses=courses,
        class_filter=class_filter, course_filter=course_filter, search=search
    )


@app.route('/students/add', methods=['POST'])
def add_student():
    data = request.form
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO students (roll_no, name, class_id, email, phone) VALUES (?,?,?,?,?)",
            (data['roll_no'], data['name'], data['class_id'],
             data.get('email', ''), data.get('phone', ''))
        )
        conn.commit()
        flash('Student added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Roll number already exists!', 'error')
    finally:
        conn.close()
    return redirect(url_for('students'))


@app.route('/students/delete/<int:sid>', methods=['POST'])
def delete_student(sid):
    conn = get_db()
    conn.execute("DELETE FROM attendance WHERE student_id=?", (sid,))
    conn.execute("DELETE FROM students WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    flash('Student removed.', 'info')
    return redirect(url_for('students'))


@app.route('/attendance')
def attendance():
    conn     = get_db()
    sel_date = request.args.get('date', date.today().isoformat())
    class_id = request.args.get('class_id', '')

    classes = conn.execute(
        "SELECT * FROM classes ORDER BY course, branch, semester, section, subject"
    ).fetchall()

    students_att = []
    sel_class = None
    if class_id:
        students_att = conn.execute('''
            SELECT s.id, s.roll_no, s.name,
                   COALESCE(a.status,'Not Marked') as status
            FROM students s
            LEFT JOIN attendance a ON s.id=a.student_id AND a.date=?
            WHERE s.class_id=?
            ORDER BY s.roll_no
        ''', (sel_date, class_id)).fetchall()
        sel_class = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()

    conn.close()
    return render_template('attendance.html',
        classes=classes, students=students_att,
        sel_date=sel_date, class_id=class_id, sel_class=sel_class
    )


@app.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    data     = request.json
    sel_date = data.get('date')
    records  = data.get('records', [])
    conn     = get_db()
    for rec in records:
        conn.execute('''
            INSERT INTO attendance (student_id, class_id, date, status)
            VALUES (?,?,?,?)
            ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status
        ''', (rec['student_id'], rec['class_id'], sel_date, rec['status']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Attendance saved for {len(records)} students.'})


@app.route('/reports')
def reports():
    conn     = get_db()
    classes  = conn.execute(
        "SELECT * FROM classes ORDER BY course, branch, semester, section, subject"
    ).fetchall()
    class_id = request.args.get('class_id', '')
    month    = request.args.get('month', date.today().strftime('%Y-%m'))

    report_data = []
    sel_class   = None
    if class_id and month:
        year, mon = month.split('-')
        report_data = conn.execute('''
            SELECT s.roll_no, s.name,
                   COUNT(CASE WHEN a.status='Present' THEN 1 END) as present,
                   COUNT(CASE WHEN a.status='Absent'  THEN 1 END) as absent,
                   COUNT(CASE WHEN a.status='Late'    THEN 1 END) as late,
                   COUNT(a.id) as total
            FROM students s
            LEFT JOIN attendance a
                ON s.id=a.student_id
                AND strftime('%Y',a.date)=?
                AND strftime('%m',a.date)=?
            WHERE s.class_id=?
            GROUP BY s.id
            ORDER BY s.roll_no
        ''', (year, mon, class_id)).fetchall()
        sel_class = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()

    conn.close()
    return render_template('reports.html',
        classes=classes, report_data=report_data,
        class_id=class_id, month=month, sel_class=sel_class
    )


# ─── API ─────────────────────────────────────
@app.route('/api/stats')
def api_stats():
    conn  = get_db()
    today = date.today().isoformat()
    data  = {
        'present': conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Present'", (today,)).fetchone()[0],
        'absent':  conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Absent'",  (today,)).fetchone()[0],
        'late':    conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Late'",    (today,)).fetchone()[0],
    }
    conn.close()
    return jsonify(data)


@app.route('/api/classes_by_course')
def classes_by_course():
    """Return classes filtered by course for dynamic dropdowns."""
    course = request.args.get('course', '')
    conn   = get_db()
    rows   = conn.execute(
        "SELECT * FROM classes WHERE course=? ORDER BY branch, semester, section, subject",
        (course,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
