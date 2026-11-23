import sqlite3
import hashlib

DB_NAME = "library.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    #' Users table (students and admin) ' 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            phone TEXT DEFAULT '',
            student_code TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Books table 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'booked',
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    """)

    conn.commit()
    conn.close()
    seed_data()

def seed_data():
    conn = get_connection()
    cursor = conn.cursor()

    # Seed default admin and sample students if users table is empty
    user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        users = [
            ("Library Admin", "admin@library.com", hash_password("admin123"), "admin", "9876543210", "ADM-001"),
            ("Rahul Sharma", "rahul@student.com", hash_password("student123"), "student", "9123456780", "STU-101"),
            ("Priya Verma", "priya@student.com", hash_password("student123"), "student", "9988776655", "STU-102"),
        ]
        cursor.executemany(
            "INSERT INTO users (name, email, password_hash, role, phone, student_code) VALUES (?, ?, ?, ?, ?, ?)",
            users,
        )

    # Seed sample books if books table is empty
    book_count = cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if book_count == 0:
        books = [
            ("Python Crash Course", "Eric Matthes", "Programming", 5, 5),
            ("Clean Code", "Robert C. Martin", "Software Engineering", 3, 3),
            ("Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", 4, 4),
            ("Atomic Habits", "James Clear", "Self-Help", 6, 6),
            ("The Pragmatic Programmer", "Andrew Hunt", "Programming", 2, 2),
            ("Database System Concepts", "Abraham Silberschatz", "Databases", 4, 4),
        ]
        cursor.executemany(
            "INSERT INTO books (title, author, category, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
            books,
        )

    conn.commit()
    conn.close()

