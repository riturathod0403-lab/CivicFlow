"""
CivicFlow - Database Layer (database.py)
SQLite database initialization, role-based user management, password hashing,
and complaint lifecycle audit history.
"""

import sqlite3
import hashlib
import os
import uuid
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "civicflow.db")

def get_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hashes a password with SHA-256 and a unique salt."""
    if not salt:
        salt = uuid.uuid4().hex
    salted = f"{salt}{password}".encode("utf-8")
    pwd_hash = hashlib.sha256(salted).hexdigest()
    return pwd_hash, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a password against the stored salt and hash."""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash

def init_db():
    """Initializes tables and seeds initial administrative, staff, and citizen demo users."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('citizen', 'admin', 'staff')),
        department TEXT,
        email TEXT,
        phone TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Complaints table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        citizen_name TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        department TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Pending', 'Assigned', 'In Progress', 'Resolved', 'Rejected')),
        confidence_score REAL DEFAULT 0.0,
        needs_review INTEGER DEFAULT 0,
        duplicate_of TEXT,
        similarity_score REAL DEFAULT 0.0,
        location TEXT NOT NULL,
        ward TEXT NOT NULL,
        citizen_rating INTEGER,
        citizen_feedback TEXT,
        resolution_notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Status History table for audit trail
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT NOT NULL,
        updated_by_user_id INTEGER,
        updated_by_name TEXT NOT NULL,
        notes TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
    )
    """)

    # Department Assignments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS department_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        department TEXT NOT NULL,
        assigned_by_user_id INTEGER,
        assigned_to_user_id INTEGER,
        notes TEXT,
        assigned_at TEXT NOT NULL,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
    )
    """)

    conn.commit()

    # Seed Default Demonstration Users if none exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_users = [
            ("admin1", "admin123", "Chief Municipal Commissioner", "admin", "Central Municipal Administration", "commissioner@citygov.org", "+1-800-555-0101"),
            ("citizen1", "citizen123", "Aarav Sharma", "citizen", None, "aarav.sharma@example.com", "+1-800-555-0102"),
            ("citizen2", "citizen123", "Elena Rostova", "citizen", None, "elena.r@example.com", "+1-800-555-0103"),
            ("roads_staff", "staff123", "Vikram Patel", "staff", "Roads & Infrastructure", "vikram.roads@citygov.org", "+1-800-555-0104"),
            ("waste_staff", "staff123", "Maria Gonzalez", "staff", "Solid Waste Management", "maria.waste@citygov.org", "+1-800-555-0105"),
            ("water_staff", "staff123", "David Kim", "staff", "Water Works & Supply", "david.water@citygov.org", "+1-800-555-0106"),
            ("light_staff", "staff123", "Sarah Jenkins", "staff", "Electrical & Lighting", "sarah.light@citygov.org", "+1-800-555-0107"),
            ("drain_staff", "staff123", "Ahmed Al-Mansoor", "staff", "Drainage & Stormwater", "ahmed.drain@citygov.org", "+1-800-555-0108"),
            ("health_staff", "staff123", "Priya Nair", "staff", "Public Health & Sanitation", "priya.sanitation@citygov.org", "+1-800-555-0109")
        ]

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for username, pwd, name, role, dept, email, phone in seed_users:
            p_hash, salt = hash_password(pwd)
            cursor.execute("""
            INSERT INTO users (username, password_hash, salt, full_name, role, department, email, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, p_hash, salt, name, role, dept, email, phone, now))
        conn.commit()

        # Seed sample complaints
        sample_seed = [
            ("CF-1001", 2, "Aarav Sharma", "Massive pothole on Main Street", "Deep dangerous crater on 5th cross road damaging car axles and causing two-wheeler skids", "potholes", "Roads & Infrastructure", "High", "In Progress", 0.94, 0, None, 0.0, "5th Cross Road, Main Street", "Ward 4 - Downtown", None, None, "Work order WO-881 dispatched to road repair crew.", "2026-10-20 09:30:00", "2026-10-21 11:00:00"),
            ("CF-1002", 3, "Elena Rostova", "Overflowing waste dumpster near school", "Dumpster has not been cleared for 4 days, garbage spilling into sidewalk creating stench and stray dog hazard", "garbage", "Solid Waste Management", "High", "Assigned", 0.91, 0, None, 0.0, "Opposite St. Jude Primary School, 8th Ave", "Ward 7 - Westside", None, None, "Assigned to Morning Route Truck 3.", "2026-10-22 14:15:00", "2026-10-22 15:00:00"),
            ("CF-1003", 2, "Aarav Sharma", "Exposed wiring on streetlight pole", "Live electrical cable dangling from metal lamp post #42 after heavy storm, pedestrian electrocution risk", "streetlights", "Electrical & Lighting", "Critical", "Resolved", 0.96, 0, None, 0.0, "Corner of 14th St and Elm", "Ward 4 - Downtown", 5, "Repaired within 4 hours. Excellent response!", "Power isolated and wire safely insulated in tamper-proof conduit.", "2026-10-18 20:00:00", "2026-10-19 01:30:00"),
            ("CF-1004", 3, "Elena Rostova", "Sewage backing up into street drain", "Stagnant foul wastewater flooding road from clogged municipal sewer line", "drainage", "Drainage & Stormwater", "Critical", "In Progress", 0.89, 0, None, 0.0, "Lane 3, North Sector", "Ward 2 - Industrial", None, None, "Suction jetting machine operating on main sewer line.", "2026-10-23 08:45:00", "2026-10-23 10:15:00"),
            ("CF-1005", 2, "Aarav Sharma", "No drinking water supply in apartment", "Sector 9 tap water has ceased completely for 36 hours without announcement", "water_supply", "Water Works & Supply", "Critical", "Pending", 0.92, 0, None, 0.0, "Sector 9 Residential Enclave", "Ward 9 - East Hills", None, None, None, "2026-10-24 07:10:00", "2026-10-24 07:10:00"),
            ("CF-1006", 3, "Elena Rostova", "Unsanitary public toilet facility", "Central bus stand community toilet facility dirty with clogged basins and no sanitation", "sanitation", "Public Health & Sanitation", "Medium", "Assigned", 0.86, 0, None, 0.0, "Intercity Bus Stand, Central", "Ward 1 - Central", None, None, "Scheduled for deep disinfection and plumbing overhaul.", "2026-10-24 11:20:00", "2026-10-24 13:00:00")
        ]

        for item in sample_seed:
            cursor.execute("""
            INSERT INTO complaints (id, user_id, citizen_name, title, description, category, department, priority, status, confidence_score, needs_review, duplicate_of, similarity_score, location, ward, citizen_rating, citizen_feedback, resolution_notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, item)

            cursor.execute("""
            INSERT INTO status_history (complaint_id, previous_status, new_status, updated_by_user_id, updated_by_name, notes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item[0], None, item[8], 1, "System Admin", f"Initial submission recorded as {item[8]}", item[18]))

        conn.commit()

    conn.close()

def authenticate_user(username: str, password: str):
    """Verifies credentials and returns user dict if valid, else None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
    row = cursor.fetchone()
    conn.close()

    if row and verify_password(password, row["password_hash"], row["salt"]):
        return dict(row)
    return None

def register_citizen(username: str, password: str, full_name: str, email: str, phone: str):
    """Registers a new Citizen. Role is strictly hardcoded to 'citizen' to prevent privilege escalation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username.strip(),))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists. Please pick another."

    pwd_hash, salt = hash_password(password)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO users (username, password_hash, salt, full_name, role, department, email, phone, created_at)
    VALUES (?, ?, ?, ?, 'citizen', NULL, ?, ?, ?)
    """, (username.strip(), pwd_hash, salt, full_name.strip(), email.strip(), phone.strip(), now))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return True, new_id

def insert_complaint(complaint_data: dict) -> str:
    """Inserts a new complaint into SQLite with unique ID and logs initial status history."""
    conn = get_connection()
    cursor = conn.cursor()

    # Generate unique complaint ID CF-XXXX
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0] + 1
    complaint_id = f"CF-{1000 + count}"

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO complaints (
        id, user_id, citizen_name, title, description, category, department,
        priority, status, confidence_score, needs_review, duplicate_of,
        similarity_score, location, ward, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        complaint_data["user_id"],
        complaint_data["citizen_name"],
        complaint_data["title"],
        complaint_data["description"],
        complaint_data["category"],
        complaint_data["department"],
        complaint_data["priority"],
        complaint_data.get("status", "Pending"),
        complaint_data.get("confidence_score", 0.0),
        1 if complaint_data.get("needs_review") else 0,
        complaint_data.get("duplicate_of"),
        complaint_data.get("similarity_score", 0.0),
        complaint_data["location"],
        complaint_data["ward"],
        now,
        now
    ))

    # Audit history
    cursor.execute("""
    INSERT INTO status_history (complaint_id, previous_status, new_status, updated_by_user_id, updated_by_name, notes, timestamp)
    VALUES (?, NULL, 'Pending', ?, ?, 'Complaint registered by citizen', ?)
    """, (complaint_id, complaint_data["user_id"], complaint_data["citizen_name"], now))

    conn.commit()
    conn.close()
    return complaint_id

def get_complaints_by_user(user_id: int):
    """Fetches complaints belonging to a specific citizen."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaints_by_department(department: str):
    """Fetches complaints assigned to a staff member's department."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE department = ? ORDER BY created_at DESC", (department,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_complaints():
    """Fetches all complaints for Municipal Administrator."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaint_by_id(complaint_id: str):
    """Retrieves full complaint details."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_status_history(complaint_id: str):
    """Fetches full lifecycle history for a complaint."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM status_history WHERE complaint_id = ? ORDER BY id ASC", (complaint_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_complaint_status(complaint_id: str, new_status: str, user_id: int, user_name: str, notes: str):
    """Updates complaint status and adds entry to status_history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Complaint not found"

    prev_status = row["status"]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE complaints
    SET status = ?, resolution_notes = CASE WHEN ? != '' THEN ? ELSE resolution_notes END, updated_at = ?
    WHERE id = ?
    """, (new_status, notes, notes, now, complaint_id))

    cursor.execute("""
    INSERT INTO status_history (complaint_id, previous_status, new_status, updated_by_user_id, updated_by_name, notes, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (complaint_id, prev_status, new_status, user_id, user_name, notes, now))

    conn.commit()
    conn.close()
    return True, "Status updated successfully"

def update_department_assignment(complaint_id: str, new_department: str, admin_user_id: int, admin_name: str, notes: str):
    """Reassigns department for a complaint."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE complaints
    SET department = ?, status = 'Assigned', updated_at = ?
    WHERE id = ?
    """, (new_department, now, complaint_id))

    cursor.execute("""
    INSERT INTO department_assignments (complaint_id, department, assigned_by_user_id, notes, assigned_at)
    VALUES (?, ?, ?, ?, ?)
    """, (complaint_id, new_department, admin_user_id, notes, now))

    cursor.execute("""
    INSERT INTO status_history (complaint_id, previous_status, new_status, updated_by_user_id, updated_by_name, notes, timestamp)
    VALUES (?, 'Pending', 'Assigned', ?, ?, ?, ?)
    """, (complaint_id, admin_user_id, admin_name, f"Reassigned to {new_department}. {notes}", now))

    conn.commit()
    conn.close()
    return True

def add_citizen_feedback(complaint_id: str, user_id: int, rating: int, feedback: str):
    """Allows citizen to submit satisfaction feedback once resolved."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, status FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()
    if not row or row["user_id"] != user_id:
        conn.close()
        return False, "Unauthorized"

    cursor.execute("""
    UPDATE complaints
    SET citizen_rating = ?, citizen_feedback = ?
    WHERE id = ?
    """, (rating, feedback, complaint_id))
    conn.commit()
    conn.close()
    return True, "Feedback recorded"

def resolve_ai_review(complaint_id: str, verified_category: str, verified_priority: str, verified_department: str, is_duplicate: bool, duplicate_parent_id: str = None):
    """Administrator confirms or corrects AI-flagged review."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    status = "Rejected" if is_duplicate else "Assigned"
    notes = f"AI Review completed. Duplicate of {duplicate_parent_id}" if is_duplicate else "AI Review verified by administrator."

    cursor.execute("""
    UPDATE complaints
    SET category = ?, priority = ?, department = ?, needs_review = 0,
        duplicate_of = ?, status = ?, updated_at = ?
    WHERE id = ?
    """, (verified_category, verified_priority, verified_department, duplicate_parent_id if is_duplicate else None, status, now, complaint_id))

    cursor.execute("""
    INSERT INTO status_history (complaint_id, previous_status, new_status, updated_by_user_id, updated_by_name, notes, timestamp)
    VALUES (?, 'Pending', ?, 1, 'Municipal Administrator', ?, ?)
    """, (complaint_id, status, notes, now))

    conn.commit()
    conn.close()
    return True
