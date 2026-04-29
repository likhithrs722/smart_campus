from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "hackathon_secret"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # RESOURCES
    c.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        branch TEXT,
        type TEXT
    )
    """)

    # BOOKINGS
    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource TEXT,
        date TEXT,
        time TEXT,
        username TEXT,
        role TEXT
    )
    """)

    # DEMO USERS
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin','admin','admin')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('student1','123','student')")

    # ADD RESOURCES (only once)
    for branch in ["CSE", "ECE", "AIML"]:
        for i in range(1, 21):
            c.execute("INSERT OR IGNORE INTO resources (name, branch, type) VALUES (?, ?, ?)",
                      (f"{branch}-CR-{i}", branch, "Classroom"))

        for i in range(1, 6):
            c.execute("INSERT OR IGNORE INTO resources (name, branch, type) VALUES (?, ?, ?)",
                      (f"{branch}-LAB-{i}", branch, "Lab"))

        c.execute("INSERT OR IGNORE INTO resources (name, branch, type) VALUES (?, ?, ?)",
                  (f"{branch}-SEMINAR", branch, "Seminar Hall"))

        c.execute("INSERT OR IGNORE INTO resources (name, branch, type) VALUES (?, ?, ?)",
                  (f"{branch}-LIBRARY", branch, "Library"))

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        user = c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u, p)
        ).fetchone()

        conn.close()

        if user:
            session["user"] = u
            session["role"] = user[3]
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("home.html")

# ---------------- BOOKING PAGE ----------------
@app.route("/booking")
def booking():
    if "user" not in session:
        return redirect("/login")

    branch = request.args.get("branch", "CSE")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    resources = c.execute("SELECT * FROM resources WHERE branch=?", (branch,)).fetchall()
    bookings = c.execute("SELECT * FROM bookings").fetchall()

    conn.close()

    slots = ["9AM", "11AM", "1PM", "3PM", "5PM"]

    return render_template(
        "booking.html",
        branch=branch,
        resources=resources,
        bookings=bookings,
        slots=slots,
        user=session.get("user"),
        role=session.get("role")
    )

# ---------------- BOOK ACTION ----------------
@app.route("/book", methods=["POST"])
def book():
    if "user" not in session:
        return redirect("/login")

    resource = request.form["resource"]
    date = request.form["date"]
    time = request.form["time"]
    branch = request.form["branch"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # check if already booked
    exists = c.execute("""
        SELECT * FROM bookings
        WHERE resource=? AND date=? AND time=?
    """, (resource, date, time)).fetchone()

    if exists:
        conn.close()
        return redirect(url_for("booking", branch=branch))

    # insert booking
    c.execute("""
    INSERT INTO bookings (resource, date, time, username, role)
    VALUES (?, ?, ?, ?, ?)
    """, (resource, date, time, session["user"], session["role"]))

    conn.commit()
    conn.close()

    return redirect(url_for("booking", branch=branch))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)