# ============================================================
# MyPOS - Categories Management
# File: categories.py
# Purpose: Add, view, update and delete product categories
#          (category name + status True/False)
# ============================================================

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

import database


# ------------------------------------------------------------
# THEME (same colors as the Products page)
# ------------------------------------------------------------

BG = "#10131C"
CARD = "#191E2B"
INPUT_BG = "#22293A"
TEXT = "#F2F4F8"
MUTED = "#A6B0C3"
ACCENT = "#7857FF"
ACCENT_HOVER = "#6242E8"
DANGER = "#E04F5F"
SUCCESS = "#16A34A"
BORDER = "#30384B"
HEADER_BG = "#293147"
ROW_ALT = "#1D2433"

STATUS_ACTIVE = "Active (True)"
STATUS_INACTIVE = "Inactive (False)"
MAX_CATEGORY_LENGTH = 60


# ============================================================
# PART 1 - DATABASE FUNCTIONS
# Uses the same pos.db connection as the rest of MyPOS.
# The categories table is created only if it does not exist,
# so existing products and sales are never touched.
# ============================================================

def initialize_categories_table():
    """Create the categories table if it is missing (safe to repeat)."""

    with database.get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _clean_name(name):
    """Trim spaces and validate the category name."""

    name = " ".join(str(name or "").split())

    if not name:
        raise ValueError("Category name is required.")

    if len(name) > MAX_CATEGORY_LENGTH:
        raise ValueError(
            f"Category name must be {MAX_CATEGORY_LENGTH} "
            "characters or fewer."
        )

    return name


def get_all_categories():
    """Return all categories, oldest first."""

    with database.get_connection() as connection:
        return connection.execute("""
            SELECT id, name, is_active, created_at
            FROM categories
            ORDER BY id ASC
        """).fetchall()


def get_category(category_id):
    """Return one category, or None."""

    with database.get_connection() as connection:
        return connection.execute("""
            SELECT id, name, is_active, created_at
            FROM categories
            WHERE id = ?
        """, (category_id,)).fetchone()


def add_category(name, is_active=True):
    """Add a category. Raises IntegrityError if the name exists."""

    name = _clean_name(name)

    with database.get_connection() as connection:
        connection.execute("""
            INSERT INTO categories (name, is_active)
            VALUES (?, ?)
        """, (name, 1 if is_active else 0))


def update_category(category_id, name, is_active):
    """Update name and status of a category."""

    name = _clean_name(name)

    with database.get_connection() as connection:
        cursor = connection.execute("""
            UPDATE categories
            SET name = ?, is_active = ?
            WHERE id = ?
        """, (name, 1 if is_active else 0, category_id))

        if cursor.rowcount == 0:
            raise ValueError("Category was not found.")


def delete_category(category_id):
    """Delete a category."""

    with database.get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM categories
            WHERE id = ?
        """, (category_id,))

        if cursor.rowcount == 0:
            raise ValueError("Category was not found.")


# ============================================================
# PART 2 - CATEGORIES PAGE (called by main.py)
# ============================================================

def create_categories_page(parent):
    """Create the complete categories screen."""

    # Make sure the table exists even if main.py was not updated.
    initialize_categories_table()

    page = tk.Frame(parent, bg=BG)
    page.pack(fill="both", expand=True)

    # Form = natural height, table = all remaining space.
    page.grid_columnconfigure(0, weight=1)
    page.grid_rowconfigure(0, weight=0)
    page.grid_rowconfigure(1, weight=1, minsize=170)

    selected_category_id = {"value": None}

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    style = ttk.Style()

    try:
        style.configure(
            "MyPOSCategories.Treeview",
            background=INPUT_BG,
            foreground=TEXT,
            fieldbackground=INPUT_BG,
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        style.configure(
            "MyPOSCategories.Treeview.Heading",
            background=HEADER_BG,
            foreground=TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
            padding=(8, 7)
        )
        style.map(
            "MyPOSCategories.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")]
        )
        style.map(
            "MyPOSCategories.Treeview.Heading",
            background=[("active", "#35405A")]
        )

        for orient in ("Vertical", "Horizontal"):
            style.configure(
                f"MyPOSCat.{orient}.TScrollbar",
                background="#2C3550",
                troughcolor=BG,
                bordercolor=BG,
                darkcolor="#2C3550",
                lightcolor="#2C3550",
                arrowcolor=TEXT,
                relief="flat"
            )
            style.map(
                f"MyPOSCat.{orient}.TScrollbar",
                background=[("active", "#3A4666")]
            )

        style.configure(
            "MyPOSCat.TCombobox",
            fieldbackground=INPUT_BG,
            background=INPUT_BG,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=INPUT_BG,
            darkcolor=INPUT_BG,
            selectbackground=INPUT_BG,
            selectforeground=TEXT,
            padding=4
        )
        style.map(
            "MyPOSCat.TCombobox",
            fieldbackground=[
                ("readonly", INPUT_BG), ("disabled", INPUT_BG)
            ],
            foreground=[("readonly", TEXT), ("disabled", MUTED)],
            background=[("active", INPUT_BG)]
        )
    except tk.TclError:
        pass

    page.option_add("*TCombobox*Listbox.background", INPUT_BG)
    page.option_add("*TCombobox*Listbox.foreground", TEXT)
    page.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    page.option_add("*TCombobox*Listbox.selectForeground", "white")

    # --------------------------------------------------------
    # WIDGET HELPERS
    # --------------------------------------------------------

    def make_button(container, text, command, bg=ACCENT, pady=8):
        return tk.Button(
            container,
            text=text,
            command=command,
            bg=bg,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=pady,
            font=("Segoe UI", 9, "bold")
        )

    # --------------------------------------------------------
    # FORM CARD (row 0)
    # --------------------------------------------------------

    form_card = tk.Frame(
        page,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    form_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

    for column_index in range(4):
        form_card.grid_columnconfigure(
            column_index, weight=1, uniform="cat_cols"
        )

    name_var = tk.StringVar()
    status_var = tk.StringVar(value=STATUS_ACTIVE)

    tk.Label(
        form_card,
        text="Category Details",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 13, "bold")
    ).grid(
        row=0, column=0, columnspan=4,
        sticky="w", padx=16, pady=(12, 6)
    )

    # Category name (wide)
    tk.Label(
        form_card, text="Category Name *",
        bg=CARD, fg=MUTED, font=("Segoe UI", 9)
    ).grid(
        row=1, column=0, columnspan=3,
        sticky="w", padx=(16, 8), pady=(4, 2)
    )

    name_entry = tk.Entry(
        form_card,
        textvariable=name_var,
        bg=INPUT_BG,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        font=("Segoe UI", 10),
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT
    )
    name_entry.grid(
        row=2, column=0, columnspan=3,
        sticky="ew", padx=(16, 8), pady=(0, 10), ipady=5
    )

    # Status (True / False)
    tk.Label(
        form_card, text="Status",
        bg=CARD, fg=MUTED, font=("Segoe UI", 9)
    ).grid(
        row=1, column=3, sticky="w", padx=(8, 16), pady=(4, 2)
    )

    status_box = ttk.Combobox(
        form_card,
        textvariable=status_var,
        values=[STATUS_ACTIVE, STATUS_INACTIVE],
        state="readonly",
        style="MyPOSCat.TCombobox",
        font=("Segoe UI", 10)
    )
    status_box.grid(
        row=2, column=3,
        sticky="ew", padx=(8, 16), pady=(0, 10), ipady=3
    )

    # Buttons row (centered)
    bottom_buttons = tk.Frame(form_card, bg=CARD)
    bottom_buttons.grid(
        row=3, column=0, columnspan=4,
        padx=16, pady=(2, 14)
    )

    # --------------------------------------------------------
    # TABLE CARD (row 1)
    # --------------------------------------------------------

    table_card = tk.Frame(
        page,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    table_card.grid(row=1, column=0, sticky="nsew")

    table_card.grid_columnconfigure(0, weight=1)
    table_card.grid_rowconfigure(0, weight=0)
    table_card.grid_rowconfigure(1, weight=1)

    table_header = tk.Frame(table_card, bg=CARD)
    table_header.grid(
        row=0, column=0, sticky="ew", padx=14, pady=(10, 6)
    )

    tk.Label(
        table_header,
        text="Saved Categories",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 13, "bold")
    ).pack(side="left")

    count_label = tk.Label(
        table_header,
        text="0 categories",
        bg=CARD,
        fg=MUTED,
        font=("Segoe UI", 9)
    )
    count_label.pack(side="right", padx=(12, 0))

    table_actions = tk.Frame(table_header, bg=CARD)
    table_actions.pack(side="right")

    table_frame = tk.Frame(table_card, bg=CARD)
    table_frame.grid(
        row=1, column=0, sticky="nsew", padx=12, pady=(0, 12)
    )
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    columns = ("sr", "name", "status", "created")

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="MyPOSCategories.Treeview",
        selectmode="browse",
        height=6
    )

    # (heading, width, minimum, alignment, may stretch?)
    column_settings = {
        "sr":      ("Sr",            50,  40, "center", False),
        "name":    ("Category Name", 320, 140, "w",     True),
        "status":  ("Status",        130,  90, "w",     False),
        "created": ("Created",       150, 110, "w",     False),
    }

    for column in columns:
        heading, width, minimum, anchor, stretch = (
            column_settings[column]
        )
        tree.heading(column, text=heading, anchor=anchor)
        tree.column(
            column,
            width=width,
            minwidth=minimum,
            anchor=anchor,
            stretch=stretch
        )

    tree.tag_configure("even", background=INPUT_BG)
    tree.tag_configure("odd", background=ROW_ALT)

    vertical_scroll = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview,
        style="MyPOSCat.Vertical.TScrollbar"
    )
    horizontal_scroll = ttk.Scrollbar(
        table_frame,
        orient="horizontal",
        command=tree.xview,
        style="MyPOSCat.Horizontal.TScrollbar"
    )

    tree.configure(
        yscrollcommand=vertical_scroll.set,
        xscrollcommand=horizontal_scroll.set
    )

    tree.grid(row=0, column=0, sticky="nsew")
    vertical_scroll.grid(row=0, column=1, sticky="ns")
    horizontal_scroll.grid(row=1, column=0, sticky="ew")

    # --------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------

    def clear_form():
        selected_category_id["value"] = None
        name_var.set("")
        status_var.set(STATUS_ACTIVE)
        tree.selection_set(())
        save_button.config(text="Save Category")
        name_entry.focus_set()

    def refresh_categories():
        try:
            categories = get_all_categories()

            for item in tree.get_children():
                tree.delete(item)

            for index, category in enumerate(categories):
                is_active = bool(category["is_active"])

                tree.insert(
                    "",
                    "end",
                    iid=str(category["id"]),   # real ID stays here
                    tags=("even" if index % 2 == 0 else "odd",),
                    values=(
                        index + 1,
                        category["name"],
                        "Active" if is_active else "Inactive",
                        str(category["created_at"] or "")[:16]
                    )
                )

            count = len(categories)
            count_label.config(
                text=f"{count} categor{'y' if count == 1 else 'ies'}"
            )

        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load categories:\n{error}",
                parent=page
            )

    def save_category():
        is_active = status_var.get() == STATUS_ACTIVE

        try:
            if selected_category_id["value"] is None:
                add_category(name_var.get(), is_active)
                success_message = "Category added successfully."
            else:
                update_category(
                    selected_category_id["value"],
                    name_var.get(),
                    is_active
                )
                success_message = "Category updated successfully."

        except ValueError as error:
            messagebox.showwarning(
                "Check Category Details",
                str(error),
                parent=page
            )
            return

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Category",
                "A category with this name already exists.",
                parent=page
            )
            return

        except sqlite3.Error as error:
            messagebox.showerror(
                "Could Not Save Category",
                str(error),
                parent=page
            )
            return

        refresh_categories()
        clear_form()

        messagebox.showinfo(
            "Success", success_message, parent=page
        )

    def select_category(_event=None):
        selection = tree.selection()

        if not selection:
            return

        try:
            category = get_category(int(selection[0]))

            if category is None:
                messagebox.showwarning(
                    "Category Not Found",
                    "This category no longer exists.",
                    parent=page
                )
                refresh_categories()
                return

            selected_category_id["value"] = category["id"]
            name_var.set(category["name"])
            status_var.set(
                STATUS_ACTIVE if category["is_active"]
                else STATUS_INACTIVE
            )
            save_button.config(text="Update Category")

        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            messagebox.showerror(
                "Could Not Open Category",
                str(error),
                parent=page
            )

    def remove_category():
        category_id = selected_category_id["value"]

        if category_id is None:
            selection = tree.selection()

            if not selection:
                messagebox.showwarning(
                    "Select Category",
                    "Select a category to delete.",
                    parent=page
                )
                return

            category_id = int(selection[0])

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            "Delete this category?",
            parent=page
        )

        if not confirmed:
            return

        try:
            delete_category(category_id)
            clear_form()
            refresh_categories()

            messagebox.showinfo(
                "Success",
                "Category deleted successfully.",
                parent=page
            )

        except (sqlite3.Error, ValueError) as error:
            messagebox.showerror(
                "Delete Failed",
                str(error),
                parent=page
            )

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    save_button = make_button(
        bottom_buttons, "Save Category", save_category
    )
    save_button.pack(side="left", padx=(0, 8))

    make_button(
        bottom_buttons, "New / Clear", clear_form, bg=SUCCESS
    ).pack(side="left")

    make_button(
        table_actions, "Delete Selected", remove_category,
        bg=DANGER, pady=5
    ).pack(side="left", padx=(0, 6))

    make_button(
        table_actions, "Refresh", refresh_categories,
        bg=SUCCESS, pady=5
    ).pack(side="left")

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    tree.bind("<<TreeviewSelect>>", select_category)
    name_entry.bind("<Return>", lambda _event: save_category())

    refresh_categories()

    return page