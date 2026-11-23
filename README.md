# Library Books Booking Website

A simple fullstack web application built with **FastAPI**, **Jinja2**, **SQLite3**, **HTML**, **CSS**, and **JavaScript**.

## Features
- **Authentication**: Register, Login, and Logout using signed session cookies (`SessionMiddleware`) and SHA-256 password hashing.
- **Authorization (Role-Based Access)**:
  - **Student**: Can browse and book library books, view/update **their own profile** (`/profile`), and view/return their own bookings.
  - **Admin**: Can view **all customer (student) profiles** (`/admin/profiles`), manage books (Create, Read, Update, Delete), and view/manage all bookings.
- **CRUD Operations**: Full Create, Read, Update, Delete for Books, Bookings, and Student Profiles using `sqlite3`.

## Project Structure
```
library_booking_app/
├── main.py                # FastAPI app, routes, auth & authorization
├── database.py            # sqlite3 connection, schema & seed data
├── requirements.txt       # Python dependencies
├── static/
│   ├── style.css          # Styling
│   └── script.js          # Client-side search & confirmation dialogs
└── templates/
    ├── base.html          # Shared layout & navigation
    ├── index.html         # Book catalog
    ├── login.html         # Login page
    ├── register.html      # Student registration
    ├── profile.html       # Student's own profile & edit form
    ├── admin_profiles.html# Admin-only view of all student profiles
    ├── book_form.html     # Admin-only Add/Edit book form
    └── bookings.html      # Bookings list
```

## How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
3. Open your browser and visit `http://127.0.0.1:8000`

## Demo Accounts (Pre-seeded)
- **Admin**: `admin@library.com` / `admin123`
- **Student 1**: `rahul@student.com` / `student123`
- **Student 2**: `priya@student.com` / `student123`
