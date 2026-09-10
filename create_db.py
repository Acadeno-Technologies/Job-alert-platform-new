import sqlite3
import os
from flask_bcrypt import Bcrypt

def init_database():
    try:
        bcrypt = Bcrypt()
        conn = sqlite3.connect("users.db", timeout=20)
        conn.execute("PRAGMA journal_mode=WAL;")
        c = conn.cursor()

        # ---------------- USERS TABLE ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            email TEXT
        )
        """)

        # Migration: Ensure email column exists in users table if table was created earlier
        try:
            c.execute("ALTER TABLE users ADD COLUMN email TEXT")
        except Exception:
            pass

        # ---------------- STUDENTS TABLE ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT
        )
        """)

        # ---------------- DEFAULT ADMIN ----------------
        admin_email = os.getenv(
            "ADMIN_EMAIL",
            "acadenocareers@gmail.com"
        ).strip().lower()

        admin_password = os.getenv(
            "ADMIN_PASSWORD",
            "Acadeno@123"
        )

        hashed = bcrypt.generate_password_hash(admin_password).decode()

        # Check if admin user already exists
        c.execute("SELECT id FROM users WHERE username=? OR email=? OR role='admin'", (admin_email, admin_email))
        admin_exists = c.fetchone()
        if not admin_exists:
            try:
                c.execute("""
                INSERT INTO users(username, password, role, email)
                VALUES (?, ?, 'admin', ?)
                """, (admin_email, hashed, admin_email))
            except Exception:
                c.execute("""
                INSERT INTO users(username, password, role)
                VALUES (?, ?, 'admin')
                """, (admin_email, hashed))

        # ---------------- FORMAT EXISTING STUDENTS (PROPER CASE NAME ONLY) ----------------
        c.execute("SELECT id, name, email FROM students")
        students_to_update = c.fetchall()
        for student_id, name, email in students_to_update:
            proper_name = name.strip().title() if name else ""
            if proper_name != name:
                c.execute("UPDATE students SET name = ? WHERE id = ?", (proper_name, student_id))

        conn.commit()
        conn.close()
        print("✅ Database initialized successfully. Proper case student names applied.")
    except Exception as e:
        print("Note: Database initialization warning:", e)

if __name__ == "__main__":
    init_database()