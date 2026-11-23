from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import get_connection, hash_password, init_db

app = FastAPI(title="Library Book Booking System")

# Secret key for signing session cookies
app.add_middleware(SessionMiddleware, secret_key="simple-library-secret-key")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    init_db()


# --- Helper functions for Authentication & Authorization ---

def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        return None
    return user


def is_admin(user) -> bool:
    return user is not None and user["role"] == "admin"


# --- Home / Books Catalog (Read) ---

@app.get("/")
def home(request: Request, msg: str = ""):
    user = get_current_user(request)
    conn = get_connection()
    books = conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    conn.close()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": user, "books": books, "msg": msg},
    )


# --- Authentication Routes (Register, Login, Logout) ---

@app.get("/register")
def register_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"user": None, "error": ""},
    )


@app.post("/register")
def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(""),
    student_code: str = Form(""),
):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email.strip(),)).fetchone()
    if existing:
        conn.close()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"user": None, "error": "Email is already registered."},
        )

    conn.execute(
        "INSERT INTO users (name, email, password_hash, role, phone, student_code) VALUES (?, ?, ?, 'student', ?, ?)",
        (name.strip(), email.strip(), hash_password(password), phone.strip(), student_code.strip()),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/login?msg=Account+created+successfully.+Please+login.", status_code=303)


@app.get("/login")
def login_page(request: Request, msg: str = ""):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": None, "error": "", "msg": msg},
    )


@app.post("/login")
def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip(),)).fetchone()
    conn.close()

    if not user or user["password_hash"] != hash_password(password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"user": None, "error": "Invalid email or password.", "msg": ""},
        )

    request.session["user_id"] = user["id"]
    request.session["role"] = user["role"]
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login?msg=Logged+out+successfully.", status_code=303)


# --- Student Profile (Own Profile Read & Update) ---

@app.get("/profile")
def my_profile(request: Request, msg: str = ""):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_connection()
    bookings = conn.execute(
        """
        SELECT b.id, bk.title, bk.author, b.booking_date, b.due_date, b.status
        FROM bookings b
        JOIN books bk ON b.book_id = bk.id
        WHERE b.user_id = ?
        ORDER BY b.id DESC
        """,
        (user["id"],),
    ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user, "bookings": bookings, "msg": msg},
    )


@app.post("/profile/update")
def update_my_profile(
    request: Request,
    name: str = Form(...),
    phone: str = Form(""),
    student_code: str = Form(""),
):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_connection()
    conn.execute(
        "UPDATE users SET name = ?, phone = ?, student_code = ? WHERE id = ?",
        (name.strip(), phone.strip(), student_code.strip(), user["id"]),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile?msg=Profile+updated+successfully.", status_code=303)


# --- Admin Authorization: View All Customer (Student) Profiles ---

@app.get("/admin/profiles")
def admin_all_profiles(request: Request, msg: str = ""):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Access denied: Admins only.")

    conn = get_connection()
    customers = conn.execute(
        """
        SELECT u.*,
               COUNT(CASE WHEN b.status = 'booked' THEN 1 END) AS active_bookings,
               COUNT(b.id) AS total_bookings
        FROM users u
        LEFT JOIN bookings b ON u.id = b.user_id
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY u.id DESC
        """
    ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="admin_profiles.html",
        context={"user": user, "customers": customers, "msg": msg},
    )


@app.post("/admin/profiles/delete/{customer_id}")
def admin_delete_customer(request: Request, customer_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Access denied: Admins only.")

    conn = get_connection()
    conn.execute("DELETE FROM bookings WHERE user_id = ?", (customer_id,))
    conn.execute("DELETE FROM users WHERE id = ? AND role = 'student'", (customer_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/profiles?msg=Customer+profile+deleted.", status_code=303)


# --- Books CRUD (Admin Only for Create, Update, Delete) ---

@app.get("/books/add")
def add_book_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Access denied: Admins only.")
    return templates.TemplateResponse(
        request=request,
        name="book_form.html",
        context={"user": user, "book": None},
    )


@app.post("/books/add")
def add_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    total_copies: int = Form(...),
):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Access denied: Admins only.")

    copies = max(1, total_copies)
    conn = get_connection()
    conn.execute(
        "INSERT INTO books (title, author, category, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
        (title.strip(), author.strip(), category.strip(), copies, copies),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/?msg=Book+added+successfully.", status_code=303)


@app.get("/books/edit/{book_id}")
def edit_book_page(request: Request, book_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Access denied: Admins only.")

    conn = get_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    return templates.TemplateResponse(
        request=request,
        name="book_form.html",
        context={"user": user, "book": book},
    )


@app.post("/books/edit/{book_id}")
def edit_book(
    request: Request,
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    total_copies: int = Form(...),
):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Access denied: Admins only.")

    conn = get_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        conn.close()
        raise HTTPException(status_code=404, detail="Book not found.")

    diff = total_copies - book["total_copies"]
    new_available = max(0, book["available_copies"] + diff)

    conn.execute(
        "UPDATE books SET title = ?, author = ?, category = ?, total_copies = ?, available_copies = ? WHERE id = ?",
        (title.strip(), author.strip(), category.strip(), max(1, total_copies), new_available, book_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/?msg=Book+updated+successfully.", status_code=303)


@app.post("/books/delete/{book_id}")
def delete_book(request: Request, book_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Access denied: Admins only.")

    conn = get_connection()
    conn.execute("DELETE FROM bookings WHERE book_id = ?", (book_id,))
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/?msg=Book+deleted+successfully.", status_code=303)


# --- Bookings CRUD (Student books & returns; Admin views/manages all) ---

@app.get("/bookings")
def list_bookings(request: Request, msg: str = ""):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_connection()
    if is_admin(user):
        bookings = conn.execute(
            """
            SELECT b.id, u.name AS student_name, u.email AS student_email,
                   bk.title AS book_title, bk.author AS book_author,
                   b.booking_date, b.due_date, b.status
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN books bk ON b.book_id = bk.id
            ORDER BY b.id DESC
            """
        ).fetchall()
    else:
        bookings = conn.execute(
            """
            SELECT b.id, bk.title AS book_title, bk.author AS book_author,
                   b.booking_date, b.due_date, b.status
            FROM bookings b
            JOIN books bk ON b.book_id = bk.id
            WHERE b.user_id = ?
            ORDER BY b.id DESC
            """,
            (user["id"],),
        ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="bookings.html",
        context={"user": user, "bookings": bookings, "msg": msg},
    )


@app.post("/bookings/create/{book_id}")
def create_booking(request: Request, book_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login?msg=Please+login+to+book+a+book.", status_code=303)

    conn = get_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book or book["available_copies"] <= 0:
        conn.close()
        return RedirectResponse(url="/?msg=Book+is+not+available+right+now.", status_code=303)

    today = datetime.now().strftime("%Y-%m-%d")
    due = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    conn.execute(
        "INSERT INTO bookings (user_id, book_id, booking_date, due_date, status) VALUES (?, ?, ?, ?, 'booked')",
        (user["id"], book_id, today, due),
    )
    conn.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
        (book_id,),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/bookings?msg=Book+booked+successfully!+Due+in+14+days.", status_code=303)


@app.post("/bookings/return/{booking_id}")
def return_booking(request: Request, booking_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_connection()
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if not booking:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found.")

    if not is_admin(user) and booking["user_id"] != user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Access denied.")

    if booking["status"] == "booked":
        conn.execute("UPDATE bookings SET status = 'returned' WHERE id = ?", (booking_id,))
        conn.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (booking["book_id"],),
        )
        conn.commit()

    conn.close()
    return RedirectResponse(url="/bookings?msg=Book+returned+successfully.", status_code=303)


@app.post("/bookings/delete/{booking_id}")
def delete_booking(request: Request, booking_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_connection()
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if not booking:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found.")

    if not is_admin(user) and booking["user_id"] != user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Access denied.")

    if booking["status"] == "booked":
        conn.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (booking["book_id"],),
        )

    conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/bookings?msg=Booking+record+deleted.", status_code=303)
