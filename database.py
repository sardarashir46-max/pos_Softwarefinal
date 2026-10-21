# ============================================================
# MyPOS - Database Layer (beginner-friendly version)
# File: database.py
#
# This file is the ONLY place that talks to the database (pos.db).
# Other files (products.py, billing.py, ...) call the functions
# written here.
#
# The file has 7 parts:
#   1. Settings
#   2. Opening the database (get_connection)
#   3. Creating tables (initialize_database)
#   4. Checking values (validation helpers)
#   5. Products (add, edit, delete, read)
#   6. Sales (checkout, history)
#   7. Users and passwords (create_user, authenticate_user)
# ============================================================

import hashlib
import math
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path


# ============================================================
# PART 1 - SETTINGS
# ============================================================

# The folder where this file lives.
BASE_DIR = Path(__file__).resolve().parent

# The database file. It sits beside this Python file.
# If it already exists, it is reused (your data is kept).
DB_PATH = BASE_DIR / "pos.db"


# ============================================================
# PART 2 - OPENING THE DATABASE
# ============================================================

@contextmanager
def get_connection():
    """
    Open the database, do your work, then close it safely.

    Use it like this:
        with get_connection() as connection:
            connection.execute("SELECT ...")

    - If everything works  -> changes are SAVED (commit).
    - If an error happens  -> changes are CANCELLED (rollback).
    - At the end           -> the connection is always closed.
    """

    # Open (or create) the database file.
    connection = sqlite3.connect(DB_PATH, timeout=10)

    # Let us read columns by name, like row["name"].
    connection.row_factory = sqlite3.Row

    # Turn ON the rule that links tables together
    # (for example sale_items must point to a real sale).
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection        # your code runs here
        connection.commit()     # no error: save the changes
    except Exception:
        connection.rollback()   # error: undo the changes
        raise                   # pass the error on to the caller
    finally:
        connection.close()      # always close the database


# ============================================================
# PART 3 - CREATING TABLES
# Called once when the app starts. It is safe to run many times:
# "IF NOT EXISTS" means "create only if it is missing", so your
# old products and sales are never deleted.
# ============================================================

def _create_tables(connection):
    """Create every table the app needs (only if missing)."""

    # Table 1: products - one row for each product you sell.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT UNIQUE,
            price REAL NOT NULL CHECK(price >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: sales - one row for each completed sale (the bill).
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total REAL NOT NULL CHECK(total >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 3: users - people who can log in.
    # The password is never saved; only a hash and a salt are.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            role TEXT NOT NULL
                CHECK(role IN ('admin', 'cashier')),
            is_active INTEGER NOT NULL DEFAULT 1
                CHECK(is_active IN (0, 1)),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 4: sale_items - the products inside each sale.
    # It keeps its own copy of the product name and price, so old
    # sales stay correct even if the product is edited or deleted.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            subtotal REAL NOT NULL CHECK(subtotal >= 0),

            FOREIGN KEY (sale_id)
                REFERENCES sales(id) ON DELETE RESTRICT,

            FOREIGN KEY (product_id)
                REFERENCES products(id) ON DELETE RESTRICT
        )
    """)


def _add_missing_product_columns(connection):
    """
    Older databases have a products table without the newer columns.
    Add the missing ones. Existing rows are kept and get defaults.
    """

    # Ask the database which columns the products table has now.
    existing_columns = set()
    for row in connection.execute("PRAGMA table_info(products)"):
        existing_columns.add(row["name"])

    # Each new column and the command that adds it.
    new_columns = {
        "purchase_price": (
            "ALTER TABLE products ADD COLUMN "
            "purchase_price REAL NOT NULL DEFAULT 0"
        ),
        "image_path": (
            "ALTER TABLE products ADD COLUMN "
            "image_path TEXT NOT NULL DEFAULT ''"
        ),
        "unit": (
            "ALTER TABLE products ADD COLUMN "
            "unit TEXT NOT NULL DEFAULT 'Piece'"
        ),
        "note": (
            "ALTER TABLE products ADD COLUMN "
            "note TEXT NOT NULL DEFAULT ''"
        ),
    }

    # Add only the columns that are not there yet.
    for column_name, add_command in new_columns.items():
        if column_name not in existing_columns:
            connection.execute(add_command)


def initialize_database():
    """
    Prepare the database. main.py calls this when the app starts.

    Step 1: create any missing tables.
    Step 2: add any missing product columns.
    Your existing products and sales are preserved.
    """

    with get_connection() as connection:
        _create_tables(connection)
        _add_missing_product_columns(connection)


# ============================================================
# PART 4 - CHECKING VALUES
# These small helpers make sure a price or stock value is valid
# BEFORE it goes into the database. They raise ValueError with a
# clear message if something is wrong.
# ============================================================

def _validate_price(value, field_name):
    """Make sure a price is a real number that is not negative."""

    # Try to turn the value into a number.
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")

    # Reject negative numbers and things like "inf" or "nan".
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{field_name} must be zero or greater.")

    # Keep 2 decimal places (for example 10.5 -> 10.5, 3.456 -> 3.46).
    return round(value, 2)


def _validate_stock(stock):
    """Make sure stock is a whole number that is not negative."""

    # True/False are technically numbers in Python; reject them.
    if isinstance(stock, bool):
        raise ValueError("Stock must be a whole number.")

    # Try to turn the value into a number.
    try:
        number = float(stock)
    except (TypeError, ValueError):
        raise ValueError("Stock must be a whole number.")

    # Reject negatives, decimals (like 2.5), "inf" and "nan".
    if (
        not math.isfinite(number)
        or number < 0
        or not number.is_integer()
    ):
        raise ValueError("Stock must be a non-negative whole number.")

    return int(number)


# ============================================================
# PART 5 - PRODUCTS
# ============================================================

def get_all_products():
    """Return every product (newest first) for the products table."""

    with get_connection() as connection:
        return connection.execute("""
            SELECT
                id,
                name,
                barcode,
                price,
                purchase_price,
                image_path,
                unit,
                note,
                stock,
                created_at
            FROM products
            ORDER BY id DESC
        """).fetchall()


def get_product(product_id):
    """Return one product by its id, or None if it does not exist."""

    with get_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()


def add_product(
    name,
    barcode,
    price,
    stock,
    purchase_price=0,
    image_path="",
    unit="Piece",
    note=""
):
    """
    Save a NEW product.

    The first four arguments are required. The rest are optional
    and have default values, so older code still works.
    """

    # Clean the text values (remove extra spaces, set defaults).
    name = str(name).strip()
    barcode = str(barcode or "").strip() or None   # empty -> no barcode
    unit = str(unit or "Piece").strip() or "Piece"
    note = str(note or "").strip()
    image_path = str(image_path or "").strip()

    # A product must have a name.
    if not name:
        raise ValueError("Product name is required.")

    # Check the numbers.
    price = _validate_price(price, "Sale price")
    purchase_price = _validate_price(purchase_price, "Purchase price")
    stock = _validate_stock(stock)

    # Insert the new row into the products table.
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO products (
                name,
                barcode,
                price,
                stock,
                purchase_price,
                image_path,
                unit,
                note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            barcode,
            price,
            stock,
            purchase_price,
            image_path,
            unit,
            note
        ))


def update_product(
    product_id,
    name,
    barcode,
    price,
    stock,
    purchase_price=None,
    image_path=None,
    unit=None,
    note=None
):
    """
    Change an EXISTING product.

    The optional values default to None. None means "keep what is
    already saved", so older code can never erase new information.
    """

    # Clean the values that are always required.
    name = str(name).strip()
    barcode = str(barcode or "").strip() or None

    if not name:
        raise ValueError("Product name is required.")

    price = _validate_price(price, "Sale price")
    stock = _validate_stock(stock)

    with get_connection() as connection:

        # Read the saved product so we can keep its old values.
        existing = connection.execute("""
            SELECT purchase_price, image_path, unit, note
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()

        if existing is None:
            raise ValueError("Product was not found.")

        # For each optional value: None = keep old, else use the new.
        if purchase_price is None:
            purchase_price = existing["purchase_price"]
        else:
            purchase_price = _validate_price(
                purchase_price, "Purchase price"
            )

        if image_path is None:
            image_path = existing["image_path"]

        if unit is None:
            unit = existing["unit"]

        if note is None:
            note = existing["note"]

        # Clean the optional text values.
        image_path = str(image_path or "").strip()
        unit = str(unit or "Piece").strip() or "Piece"
        note = str(note or "").strip()

        # Save all the values into the existing row.
        connection.execute("""
            UPDATE products
            SET
                name = ?,
                barcode = ?,
                price = ?,
                stock = ?,
                purchase_price = ?,
                image_path = ?,
                unit = ?,
                note = ?
            WHERE id = ?
        """, (
            name,
            barcode,
            price,
            stock,
            purchase_price,
            image_path,
            unit,
            note,
            product_id
        ))


def delete_product(product_id):
    """
    Delete a product, even if it was sold before.

    Old sales are not damaged: sale_items keeps its own copy of the
    product name, price and subtotal.
    """

    with get_connection() as connection:

        # Switch OFF the table-link check for this one delete.
        # This line must come BEFORE the DELETE command.
        connection.execute("PRAGMA foreign_keys = OFF")

        cursor = connection.execute("""
            DELETE FROM products
            WHERE id = ?
        """, (product_id,))

        # rowcount = how many rows were deleted. 0 means no such id.
        if cursor.rowcount == 0:
            raise ValueError("Product was not found.")


# ============================================================
# PART 6 - SALES
# ============================================================

def _merge_cart_items(cart_items):
    """
    Check the cart and combine repeated products.

    Input:  [{"product_id": 1, "quantity": 2}, ...]
    Output: {1: 2, ...}   (product id -> total quantity)
    """

    if not cart_items:
        raise ValueError("The cart is empty.")

    quantities = {}

    for item in cart_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity")

        # The product id must be a positive whole number.
        if (
            isinstance(product_id, bool)
            or not isinstance(product_id, int)
            or product_id <= 0
        ):
            raise ValueError("Invalid product ID.")

        # The quantity must be a positive whole number.
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity <= 0
        ):
            raise ValueError("Quantity must be a positive whole number.")

        # If the same product appears twice, add the quantities.
        quantities[product_id] = quantities.get(product_id, 0) + quantity

    return quantities


def complete_sale(cart_items):
    """
    Finish a sale: save the bill and reduce the stock.

    Everything happens as ONE unit. If any step fails, nothing is
    saved (no half-finished sales, no wrong stock).

    Expected input:
        [{"product_id": 1, "quantity": 2},
         {"product_id": 3, "quantity": 1}]

    Prices are read from the database, never from the cart, so the
    cart cannot change a price.
    """

    # Check the cart and combine repeated products.
    quantities = _merge_cart_items(cart_items)

    with get_connection() as connection:

        # Lock the database so nobody else changes stock meanwhile.
        connection.execute("BEGIN IMMEDIATE")

        prepared_items = []   # the lines of the bill
        total = 0.0           # the bill total

        # ---- Step 1: check every product, price and stock ----
        for product_id, quantity in quantities.items():

            product = connection.execute("""
                SELECT id, name, price, stock
                FROM products
                WHERE id = ?
            """, (product_id,)).fetchone()

            if product is None:
                raise ValueError(
                    f"Product ID {product_id} no longer exists."
                )

            price = float(product["price"])
            stock = int(product["stock"])

            if not math.isfinite(price) or price < 0:
                raise ValueError(f"Invalid price for {product['name']}.")

            # Not enough items on the shelf.
            if stock < quantity:
                raise ValueError(
                    f"Insufficient stock for {product['name']}. "
                    f"Available: {stock}, requested: {quantity}."
                )

            # Line total, and add it to the bill total.
            subtotal = round(price * quantity, 2)
            total = round(total + subtotal, 2)

            # Both "name"/"price" and "product_name"/"unit_price" are
            # kept because billing.py and receipt.py use these keys.
            prepared_items.append({
                "product_id": product_id,
                "name": product["name"],
                "product_name": product["name"],
                "quantity": quantity,
                "price": price,
                "unit_price": price,
                "subtotal": subtotal
            })

        # ---- Step 2: create the sale (the bill) ----
        cursor = connection.execute("""
            INSERT INTO sales (total)
            VALUES (?)
        """, (total,))

        sale_id = cursor.lastrowid   # id of the sale just created

        # ---- Step 3: save each line and reduce the stock ----
        for item in prepared_items:

            # Save the line in sale_items.
            connection.execute("""
                INSERT INTO sale_items (
                    sale_id,
                    product_id,
                    product_name,
                    quantity,
                    unit_price,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sale_id,
                item["product_id"],
                item["name"],
                item["quantity"],
                item["price"],
                item["subtotal"]
            ))

            # Reduce the product stock. "stock >= ?" makes sure the
            # stock can never go below zero.
            cursor = connection.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ? AND stock >= ?
            """, (
                item["quantity"],
                item["product_id"],
                item["quantity"]
            ))

            # Exactly one row must change, otherwise cancel the sale.
            if cursor.rowcount != 1:
                raise ValueError(
                    f"Stock update failed for {item['name']}."
                )

        # Give the result back (used for the receipt).
        return {
            "sale_id": sale_id,
            "total": total,
            "items": prepared_items
        }


def get_sales_history():
    """Return all saved sales, newest first."""

    with get_connection() as connection:
        return connection.execute("""
            SELECT id, total, created_at
            FROM sales
            ORDER BY id DESC
        """).fetchall()


def get_sale_items(sale_id):
    """Return the product lines that belong to one sale."""

    with get_connection() as connection:
        return connection.execute("""
            SELECT
                product_name,
                quantity,
                unit_price,
                subtotal
            FROM sale_items
            WHERE sale_id = ?
            ORDER BY id
        """, (sale_id,)).fetchall()


# ============================================================
# PART 7 - USERS AND PASSWORDS
# A password is never saved as plain text. We save:
#   - salt: a random value, different for every user
#   - hash: a scrambled version of (password + salt)
# A hash cannot be turned back into the password.
# ============================================================

def _hash_password(password, salt):
    """Scramble a password with its salt (PBKDF2, 600,000 rounds)."""

    return hashlib.pbkdf2_hmac(
        "sha256",                  # scrambling method
        password.encode("utf-8"),  # password as bytes
        salt,                      # random salt (bytes)
        600_000                    # rounds: makes guessing very slow
    )


def create_user(username, password, role="cashier"):
    """Create a user. The password is saved only as a hash."""

    username = str(username).strip()

    # Basic checks.
    if not username:
        raise ValueError("Username is required.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    if role not in ("admin", "cashier"):
        raise ValueError("Invalid user role.")

    # Make a new random salt and scramble the password with it.
    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt)

    # Save the user. .hex() turns bytes into text for the database.
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO users (
                username,
                password_hash,
                password_salt,
                role
            )
            VALUES (?, ?, ?, ?)
        """, (
            username,
            password_hash.hex(),
            salt.hex(),
            role
        ))


def authenticate_user(username, password):
    """
    Check a username and password.

    Returns {"id", "username", "role"} if they are correct,
    otherwise None.
    """

    username = str(username).strip()

    # Find the user in the database.
    with get_connection() as connection:
        user = connection.execute("""
            SELECT id, username, password_hash,
                   password_salt, role, is_active
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

    # No such user, or the account is switched off.
    if user is None or user["is_active"] != 1:
        return None

    # Scramble the typed password with the SAVED salt.
    try:
        salt = bytes.fromhex(user["password_salt"])
        saved_hash = bytes.fromhex(user["password_hash"])
        typed_hash = _hash_password(password, salt)
    except (ValueError, TypeError):
        return None

    # If both scrambled values match, the password is correct.
    if not secrets.compare_digest(saved_hash, typed_hash):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }