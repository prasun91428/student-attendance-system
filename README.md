# 🎓 Student Attendance System — EduTrack

A full-stack **Student Attendance Management System** built with **Python + Flask + SQLite**, featuring a modern dark-mode dashboard UI.

## 🚀 Features

- 📊 **Dashboard** — Real-time KPIs, 7-day attendance trend chart, donut breakdown, class-wise progress bars
- 👥 **Students** — Add/delete students, search, filter by BTech/BCA course, attendance % per student
- ✅ **Mark Attendance** — Present / Absent / Late per student with AJAX save, grouped by Course → Semester → Section
- 📋 **Reports** — Monthly summary, automatic A/B/C/D grade system, print-ready layout

## 🏫 Courses & Subjects

| Course | Branch | Subjects |
|---|---|---|
| **BTech** | CSE | Data Structures, OS, DBMS, Computer Networks, Machine Learning, Cloud Computing |
| **BTech** | ECE | Digital Signal Processing, Microprocessors |
| **BTech** | IT | Web Technologies, Software Engineering |
| **BTech** | Mech | Engineering Mechanics, Engineering Mathematics |
| **BCA** | CS | C++, Python, RDBMS, Advanced Java, Mobile App Dev |

## 🛠 Tech Stack

- **Backend**: Python 3 + Flask 3
- **Database**: SQLite (auto-created & seeded)
- **Frontend**: Vanilla HTML/CSS/JS + Chart.js
- **Design**: Dark glassmorphism, Inter font, gradient accents

## ⚡ Quick Start

```bash
# 1. Install dependency
pip install flask

# 2. Run the app
python app.py

# 3. Open browser
# → http://127.0.0.1:5000
```

> The database is **auto-created with demo data** on first launch — no setup needed!

## 📁 Project Structure

```
student-attendance-system/
├── app.py                  ← Flask app + SQLite logic + all routes
├── requirements.txt
├── templates/
│   ├── base.html           ← Sidebar navigation layout
│   ├── dashboard.html      ← KPI cards + Chart.js graphs
│   ├── students.html       ← Student management + add modal
│   ├── attendance.html     ← Mark attendance per class
│   └── reports.html        ← Monthly report with grades
└── static/
    ├── css/style.css       ← Premium dark-mode design system
    └── js/main.js          ← Modal helpers + animations
```

## 👨‍💻 Author

**Prasun Kumar** — [@prasun91428](https://github.com/prasun91428)
