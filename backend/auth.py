import sqlite3
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "smartcrop.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_users_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def create_default_users():
    conn = get_db_connection()

    # Default Admin
    admin = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        conn.execute("""
            INSERT INTO users (username, password, name, role)
            VALUES (?, ?, ?, ?)
        """, (
            "admin",
            hash_password("admin123"),
            "Administrator",
            "admin"
        ))

    # Default Farmer/User
    farmer = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("farmer",)
    ).fetchone()

    if not farmer:
        conn.execute("""
            INSERT INTO users (username, password, name, role)
            VALUES (?, ?, ?, ?)
        """, (
            "farmer",
            hash_password("farmer123"),
            "Farmer",
            "user"
        ))

    conn.commit()
    conn.close()


def login_user(username, password):
    conn = get_db_connection()

    user = conn.execute("""
        SELECT id, username, password, name, role
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    conn.close()

    if not user:
        return {
            "success": False,
            "message": "Invalid username or password."
        }

    if user["password"] != hash_password(password):
        return {
            "success": False,
            "message": "Invalid username or password."
        }

    return {
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"]
        }
    }


def create_user(username, password, name, role="user"):
    username = username.strip()
    password = password.strip()
    name = name.strip()
    role = role.strip().lower()

    if not username or not password or not name:
        return {
            "success": False,
            "message": "All fields are required."
        }

    if role not in ["user", "admin"]:
        return {
            "success": False,
            "message": "Invalid role."
        }

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if existing:
        conn.close()
        return {
            "success": False,
            "message": "Username already exists."
        }

    cursor = conn.execute("""
        INSERT INTO users (username, password, name, role)
        VALUES (?, ?, ?, ?)
    """, (
        username,
        hash_password(password),
        name,
        role
    ))

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "User created successfully.",
        "user": {
            "id": user_id,
            "username": username,
            "name": name,
            "role": role
        }
    }


def get_all_users():
    conn = get_db_connection()

    users = conn.execute("""
        SELECT id, username, name, role, created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [
        {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "created_at": user["created_at"]
        }
        for user in users
    ]


if __name__ == "__main__":
    create_users_table()
    create_default_users()
    print("Users database setup completed.")
