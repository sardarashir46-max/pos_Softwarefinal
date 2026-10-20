
# ============================================================
# MyPOS - Database Layer
# File: database.py
# Purpose: Database connection, products and sales
# ============================================================

import sqlite3
import math
from pathlib import Path
from contextlib import contextmanager


# Keep pos.db beside this Python file.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pos.db"


@contextmanager
def get_connection():
    """Open a connection and safely commit, rollback and close."""

    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    """Create required tables without deleting existing data."""

    with get_connection() as connection:

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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total REAL NOT NULL CHECK(total >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

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


def get_all_products():
    """Return all products for the interface."""

    with get_connection() as connection:
        return connection.execute("""
            SELECT id, name, barcode, price, stock
            FROM products
            ORDER BY id DESC
        """).fetchall()


def add_product(name, barcode, price, stock):
    """Insert a product."""

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO products (name, barcode, price, stock)
            VALUES (?, ?, ?, ?)
        """, (name, barcode or None, price, stock))


def update_product(product_id, name, barcode, price, stock):
    """Update a product."""

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE products
            SET name = ?, barcode = ?, price = ?, stock = ?
            WHERE id = ?
        """, (name, barcode or None, price, stock, product_id))

        if cursor.rowcount == 0:
            raise ValueError("Product was not found.")


def delete_product(product_id):
    """Delete a product if no saved sale references it."""

    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM products WHERE id = ?
        """, (product_id,))

        if cursor.rowcount == 0:
            raise ValueError("Product was not found.")


def complete_sale(cart_items):
    """
    Save one sale, save its line items and deduct stock atomically.

    cart_items format:
    [
        {"product_id": 1, "quantity": 2},
        {"product_id": 3, "quantity": 1}
    ]

    Prices are always read again from the database.
    """

    if not cart_items:
        raise ValueError("The cart is empty.")

    # Combine duplicate product IDs and validate quantities.
    quantities = {}

    for item in cart_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity")

        if (
            isinstance(product_id, bool)
            or not isinstance(product_id, int)
            or product_id <= 0
        ):
            raise ValueError("Invalid product ID.")

        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity <= 0
        ):
            raise ValueError("Quantity must be a positive whole number.")

        quantities[product_id] = (
            quantities.get(product_id, 0) + quantity
        )

    # BEGIN IMMEDIATE obtains the write reservation before we
    # check stock, preventing another writer from selling the
    # same available stock during this transaction.
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        prepared_items = []
        total = 0.0

        # Step 1: Recheck each product and its current stock.
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
                raise ValueError(
                    f"Invalid price for {product['name']}."
                )

            if stock < quantity:
                raise ValueError(
                    f"Insufficient stock for {product['name']}. "
                    f"Available: {stock}, requested: {quantity}."
                )

            subtotal = round(price * quantity, 2)
            total = round(total + subtotal, 2)

            prepared_items.append({
                "product_id": product_id,
                "name": product["name"],
                "quantity": quantity,
                "price": price,
                "subtotal": subtotal
            })

        # Step 2: Create the main sale record.
        cursor = connection.execute("""
            INSERT INTO sales (total)
            VALUES (?)
        """, (total,))

        sale_id = cursor.lastrowid

        # Step 3: Save each item and deduct its stock.
        for item in prepared_items:

            connection.execute("""
                INSERT INTO sale_items (
                    sale_id, product_id, product_name,
                    quantity, unit_price, subtotal
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

            cursor = connection.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ? AND stock >= ?
            """, (
                item["quantity"],
                item["product_id"],
                item["quantity"]
            ))

            if cursor.rowcount != 1:
                raise ValueError(
                    f"Stock update failed for {item['name']}."
                )

        # The context manager commits only if all steps succeed.
        # Any exception rolls back the complete transaction.
        return {
            "sale_id": sale_id,
            "total": total,
            "items": prepared_items
        }


def get_sales_history():
    """Return saved sales, newest first."""

    with get_connection() as connection:
        return connection.execute("""
            SELECT id, total, created_at
            FROM sales
            ORDER BY id DESC
        """).fetchall()


def get_sale_items(sale_id):
    """Return the items belonging to one sale."""

    with get_connection() as connection:
        return connection.execute("""
            SELECT product_name, quantity, unit_price, subtotal
            FROM sale_items
            WHERE sale_id = ?
            ORDER BY id
        """, (sale_id,)).fetchall()
