import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-private-secret"

# Database connection function
def get_db():
    return sqlite3.connect("planner.db")

# Create database tables automatically
def create_database():
    conn = get_db()
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Tasks table for Daily Planner
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            task TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        conn = get_db()
        user = conn.execute(
            "SELECT name FROM users WHERE email = ?",
            (session['email'],)
        ).fetchone()
        conn.close()
        username = user[0] if user else ""
        return render_template('dashboard.html', name=username)
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute(
            "SELECT password FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session['email'] = email
            return redirect(url_for('dashboard'))
        flash("Invalid email or password")
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            conn.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered.")
        finally:
            conn.close()
    return render_template('register.html')

# Daily Planner route (renders daily.html)
@app.route('/daily', methods=['GET', 'POST'])
def daily_planner():
    if 'email' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    if request.method == 'POST':
        task_text = request.form['task']
        if task_text.strip():
            conn.execute(
                "INSERT INTO tasks (email, task) VALUES (?, ?)",
                (session['email'], task_text)
            )
            conn.commit()
            flash("Task added!")
            
    tasks = conn.execute(
        "SELECT task FROM tasks WHERE email = ?",
        (session['email'],)
    ).fetchall()
    conn.close()
    
    return render_template('daily.html', tasks=tasks)

# Logout route
@app.route('/logout')
def logout():
    session.pop('email', None)
    flash("You have been logged out.")
    return redirect(url_for('home'))

# Initialize database tables before running the app
create_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)