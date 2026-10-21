# ============================================================
# MyPOS - Login System
# File: login.py
# Purpose: Users table, secure passwords and the login window
# ============================================================
import hashlib
import hmac
import re
import secrets
import sqlite3
import time
import tkinter as tk

import database


# ------------------------------------------------------------
# THEME (same colors as the rest of MyPOS)
# ------------------------------------------------------------

BG = "#111318"
CARD = "#1E212B"
INPUT_BG = "#262B38"
TEXT = "#F4F5FA"
MUTED = "#A0A5B5"
ACCENT = "#7958F5"
ACCENT_HOVER = "#6847E5"
DANGER = "#F16D79"
BORDER = "#303442"

PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_LENGTH = 6
MAX_FAILED_ATTEMPTS = 5
LOCK_SECONDS = 30


# ============================================================
# PART 1 - DATABASE AND PASSWORD FUNCTIONS
# Passwords are NEVER stored as plain text. Each user gets a
# random "salt" and the password is hashed with PBKDF2.
# ============================================================

def initialize_users_table():
    """
    Create the login table if it is missing (safe to repeat).

    The table is called app_users so it can never clash with an
    older table named "users" that may already exist in pos.db.
    """

    with database.get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                iterations INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _hash_password(password, salt_hex, iterations):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        iterations
    ).hex()


def validate_username(username):
    """Return a clean username or raise ValueError."""

    username = str(username or "").strip()

    if not username:
        raise ValueError("Please enter a username.")

    if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", username):
        raise ValueError(
            "Username must be 3 to 30 characters: letters, "
            "numbers, dot, dash or underscore."
        )

    return username


def validate_password(password):
    """Raise ValueError if the password is too weak."""

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} "
            "characters."
        )


def count_users():
    """How many user accounts exist."""

    with database.get_connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM app_users"
        ).fetchone()[0]


def create_user(username, password, role="admin"):
    """Create a user. Raises IntegrityError if the name exists."""

    username = validate_username(username)
    validate_password(password)

    salt_hex = secrets.token_hex(16)
    password_hash = _hash_password(
        password, salt_hex, PBKDF2_ITERATIONS
    )

    with database.get_connection() as connection:
        connection.execute("""
            INSERT INTO app_users (
                username, password_hash, salt, iterations, role
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            username, password_hash, salt_hex,
            PBKDF2_ITERATIONS, role
        ))


def authenticate(username, password):
    """
    Check username and password.

    Returns {"id", "username", "role"} when correct, otherwise None.
    """

    username = str(username or "").strip()

    with database.get_connection() as connection:
        row = connection.execute("""
            SELECT id, username, password_hash, salt,
                iterations, role, is_active
            FROM app_users
            WHERE username = ?
        """, (username,)).fetchone()

    if row is None or not row["is_active"]:
        # Do the same amount of work so timing does not reveal
        # whether the username exists.
        _hash_password(password, "00" * 16, PBKDF2_ITERATIONS)
        return None

    expected = row["password_hash"]
    actual = _hash_password(password, row["salt"], row["iterations"])

    if not hmac.compare_digest(expected, actual):
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"]
    }


# ============================================================
# PART 2 - LOGIN WINDOW
# ============================================================

def run_login(root):
    """
    Show the login window and wait until it closes.

    Returns the user dictionary after a successful login,
    or None if the window was closed.

    If no user exists yet, the window asks you to create the
    first (admin) account instead.
    """

    initialize_users_table()
    setup_mode = count_users() == 0

    result = {"user": None}
    failed = {"count": 0, "locked_until": 0.0}

    win = tk.Toplevel(root)
    win.title("MyPOS | Login")
    win.configure(bg=BG)
    win.resizable(False, False)

    width = 440
    height = 640 if setup_mode else 540
    x = (win.winfo_screenwidth() - width) // 2
    y = (win.winfo_screenheight() - height) // 2
    win.geometry(f"{width}x{height}+{x}+{max(0, y - 20)}")
    win.protocol("WM_DELETE_WINDOW", win.destroy)

    card = tk.Frame(
        win,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    card.pack(fill="both", expand=True, padx=22, pady=22)

    # ---- Brand ----
    brand = tk.Frame(card, bg=CARD)
    brand.pack(pady=(28, 6))

    tk.Label(
        brand, text="M", bg=ACCENT, fg="white",
        font=("Segoe UI", 20, "bold"), width=2
    ).pack(side="left", padx=(0, 12))

    tk.Label(
        brand, text="MyPOS", bg=CARD, fg=TEXT,
        font=("Segoe UI", 22, "bold")
    ).pack(side="left")

    tk.Label(
        card,
        text=(
            "Create your admin account"
            if setup_mode else "Sign in to continue"
        ),
        bg=CARD, fg=TEXT, font=("Segoe UI", 13, "bold")
    ).pack(pady=(14, 2))

    tk.Label(
        card,
        text=(
            "First-time setup. Choose a password you will remember."
            if setup_mode else "Enter your username and password."
        ),
        bg=CARD, fg=MUTED, font=("Segoe UI", 9),
        wraplength=330, justify="center"
    ).pack(pady=(0, 14))

    # ---- Fields ----
    entries = []

    def add_field(label_text, hidden=False):
        tk.Label(
            card, text=label_text, bg=CARD, fg=MUTED,
            font=("Segoe UI", 9), anchor="w"
        ).pack(fill="x", padx=34, pady=(6, 2))

        variable = tk.StringVar()
        entry = tk.Entry(
            card,
            textvariable=variable,
            show="\u25cf" if hidden else "",
            bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 11),
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT
        )
        entry.pack(fill="x", padx=34, ipady=7)

        if hidden:
            entries.append(entry)

        return variable, entry

    username_var, username_entry = add_field("Username")
    password_var, password_entry = add_field("Password", hidden=True)

    confirm_var = tk.StringVar()
    if setup_mode:
        confirm_var, _confirm_entry = add_field(
            "Confirm Password", hidden=True
        )

    show_var = tk.BooleanVar(value=False)

    def toggle_password():
        for entry in entries:
            entry.config(show="" if show_var.get() else "\u25cf")

    tk.Checkbutton(
        card,
        text="Show password",
        variable=show_var,
        command=toggle_password,
        bg=CARD, fg=MUTED,
        activebackground=CARD, activeforeground=TEXT,
        selectcolor=INPUT_BG,
        font=("Segoe UI", 9), bd=0, highlightthickness=0
    ).pack(anchor="w", padx=32, pady=(8, 0))

    error_label = tk.Label(
        card, text="", bg=CARD, fg=DANGER,
        font=("Segoe UI", 9), wraplength=340, justify="left"
    )
    error_label.pack(fill="x", padx=34, pady=(10, 0))

    def show_error(message):
        error_label.config(text=message)

    # ---- Submit ----
    def submit(_event=None):
        now = time.time()

        if now < failed["locked_until"]:
            wait = int(failed["locked_until"] - now) + 1
            show_error(
                f"Too many attempts. Try again in {wait} seconds."
            )
            return

        username = username_var.get().strip()
        password = password_var.get()

        try:
            if setup_mode:
                username = validate_username(username)
                validate_password(password)

                if password != confirm_var.get():
                    raise ValueError("Passwords do not match.")

                create_user(username, password, "admin")

            user = authenticate(username, password)

        except ValueError as error:
            show_error(str(error))
            return

        except sqlite3.IntegrityError:
            show_error("This username already exists.")
            return

        except sqlite3.Error as error:
            show_error(f"Database error: {error}")
            return

        if user is None:
            failed["count"] += 1
            password_var.set("")
            password_entry.focus_set()

            if failed["count"] >= MAX_FAILED_ATTEMPTS:
                failed["count"] = 0
                failed["locked_until"] = time.time() + LOCK_SECONDS
                show_error(
                    "Too many failed attempts. "
                    f"Please wait {LOCK_SECONDS} seconds."
                )
            else:
                show_error("Incorrect username or password.")
            return

        result["user"] = user
        win.destroy()

    login_button = tk.Button(
        card,
        text="Create Account & Sign In" if setup_mode else "Sign In",
        command=submit,
        bg=ACCENT, fg="white",
        activebackground=ACCENT_HOVER, activeforeground="white",
        relief="flat", bd=0, cursor="hand2",
        font=("Segoe UI", 11, "bold"), pady=10
    )
    login_button.pack(fill="x", padx=34, pady=(14, 0))

    win.bind("<Return>", submit)

    # ---- Show, focus and wait ----
    win.lift()
    win.after(150, username_entry.focus_force)

    try:
        win.wait_visibility()
        win.grab_set()
    except tk.TclError:
        pass

    root.wait_window(win)

    return result["user"]