# ============================================================
# MyPOS - Products Management
# File: products.py
# Purpose: Add, view, update and delete products
# ============================================================

import math
import shutil
import uuid
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import database


# ------------------------------------------------------------
# THEME
# ------------------------------------------------------------

BG = "#10131C"
CARD = "#191E2B"
INPUT_BG = "#22293A"
TEXT = "#F2F4F8"
MUTED = "#A6B0C3"
ACCENT = "#7857FF"
ACCENT_HOVER = "#6242E8"
DANGER = "#E04F5F"
BORDER = "#30384B"
HEADER_BG = "#293147"
ROW_ALT = "#1D2433"

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "product_images"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

UNITS = [
    "Piece", "Kg", "Gram", "Litre",
    "Millilitre", "Bottle", "Box", "Pack", "Dozen"
]

MAX_NAME_LENGTH = 100
MAX_BARCODE_LENGTH = 50


# ------------------------------------------------------------
# SMALL HELPER FUNCTIONS (no widgets inside these)
# ------------------------------------------------------------

def shorten(text, limit):
    """Cut long text and add '...' so it cannot break the layout."""
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def single_line(text):
    """Turn multi-line text into one line for the table."""
    return " ".join(str(text or "").split())


def parse_number(text, field_name, required=True):
    """Read a non-negative number from an entry box."""
    cleaned = str(text).strip().replace(",", "")

    if not cleaned:
        if required:
            raise ValueError(f"{field_name} is required.")
        return 0.0

    try:
        value = float(cleaned)
    except ValueError:
        raise ValueError(f"{field_name} must be a valid number.")

    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{field_name} must be zero or greater.")

    return value


def copy_image_to_project(source):
    """Copy a chosen image into product_images/ with a unique name."""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    destination = IMAGE_DIR / (
        f"{uuid.uuid4().hex}{source.suffix.lower()}"
    )
    shutil.copy2(source, destination)
    return destination


def remove_file_quietly(path):
    """Delete a file we just copied if saving the product failed."""
    if path is None:
        return
    try:
        Path(path).unlink()
    except OSError:
        pass


# ------------------------------------------------------------
# MAIN PAGE BUILDER (called by main.py)
# ------------------------------------------------------------

def create_products_page(parent):
    """Create the complete product management screen."""

    # The page uses GRID so the table row can take all leftover space.
    page = tk.Frame(parent, bg=BG)
    page.pack(fill="both", expand=True)

    page.grid_columnconfigure(0, weight=1)
    page.grid_rowconfigure(0, weight=0)               # form: natural height
    page.grid_rowconfigure(1, weight=1, minsize=170)  # table: ALL the rest

    selected_product_id = {"value": None}
    selected_image_path = {"value": ""}   # path already saved in database
    pending_image = {"source": None}      # new image, copied on Save

    # --------------------------------------------------------
    # STYLES (dark Treeview, scrollbars and combobox)
    # --------------------------------------------------------

    style = ttk.Style()

    try:
        style.configure(
            "MyPOSProducts.Treeview",
            background=INPUT_BG,
            foreground=TEXT,
            fieldbackground=INPUT_BG,
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        style.configure(
            "MyPOSProducts.Treeview.Heading",
            background=HEADER_BG,
            foreground=TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
            padding=(8, 7)
        )
        style.map(
            "MyPOSProducts.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")]
        )
        style.map(
            "MyPOSProducts.Treeview.Heading",
            background=[("active", "#35405A")]
        )

        for orient in ("Vertical", "Horizontal"):
            style.configure(
                f"MyPOS.{orient}.TScrollbar",
                background="#2C3550",
                troughcolor=BG,
                bordercolor=BG,
                darkcolor="#2C3550",
                lightcolor="#2C3550",
                arrowcolor=TEXT,
                relief="flat"
            )
            style.map(
                f"MyPOS.{orient}.TScrollbar",
                background=[("active", "#3A4666")]
            )

        style.configure(
            "MyPOS.TCombobox",
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
            "MyPOS.TCombobox",
            fieldbackground=[
                ("readonly", INPUT_BG), ("disabled", INPUT_BG)
            ],
            foreground=[("readonly", TEXT), ("disabled", MUTED)],
            background=[("active", INPUT_BG)]
        )
    except tk.TclError:
        pass

    # Dark dropdown list for the Unit combobox.
    page.option_add("*TCombobox*Listbox.background", INPUT_BG)
    page.option_add("*TCombobox*Listbox.foreground", TEXT)
    page.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    page.option_add("*TCombobox*Listbox.selectForeground", "white")

    # --------------------------------------------------------
    # WIDGET HELPERS
    # --------------------------------------------------------

    def make_label(container, text):
        return tk.Label(
            container,
            text=text,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9)
        )

    def make_entry(container, variable):
        return tk.Entry(
            container,
            textvariable=variable,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT
        )

    def make_button(container, text, command,
                    bg=ACCENT, fg="white", pady=7):
        return tk.Button(
            container,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=pady,
            font=("Segoe UI", 9, "bold")
        )

    def cell_padding(column, span=1):
        """Left/right padding so the form edges line up nicely."""
        left = 16 if column == 0 else 8
        right = 16 if column + span >= 4 else 8
        return left, right

    # --------------------------------------------------------
    # PRODUCT FORM CARD  (row 0 of the page)
    # Four equal columns, three short rows of fields.
    # --------------------------------------------------------

    form_card = tk.Frame(
        page,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    form_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

    # Weight is on the columns that REALLY hold widgets (0 to 3).
    for column_index in range(4):
        form_card.grid_columnconfigure(
            column_index, weight=1, uniform="form_cols"
        )

    name_var = tk.StringVar()
    barcode_var = tk.StringVar()
    sale_price_var = tk.StringVar()
    purchase_price_var = tk.StringVar()
    stock_var = tk.StringVar(value="0")
    unit_var = tk.StringVar(value="Piece")

    # Row 0: form title.
    tk.Label(
        form_card,
        text="Product Details",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 13, "bold")
    ).grid(
        row=0, column=0, columnspan=2,
        sticky="w", padx=16, pady=(12, 6)
    )

    def add_field(label_text, widget, row, column, span=1,
                  ipady=0, bottom=8):
        """Place a label (row) and its widget (row + 1)."""
        left, right = cell_padding(column, span)

        make_label(form_card, label_text).grid(
            row=row, column=column, columnspan=span,
            sticky="w", padx=(left, right), pady=(4, 2)
        )
        widget.grid(
            row=row + 1, column=column, columnspan=span,
            sticky="ew", padx=(left, right), pady=(0, bottom),
            ipady=ipady
        )

    # Row 1-2: Name (wide) | Barcode | Unit
    add_field(
        "Product Name *", make_entry(form_card, name_var),
        1, 0, span=2, ipady=5
    )
    add_field(
        "Barcode", make_entry(form_card, barcode_var),
        1, 2, ipady=5
    )

    unit_box = ttk.Combobox(
        form_card,
        textvariable=unit_var,
        values=UNITS,
        style="MyPOS.TCombobox",
        font=("Segoe UI", 10)
    )
    add_field("Unit", unit_box, 1, 3, ipady=3)

    # Row 3-4: Sale | Purchase | Stock | Image
    add_field(
        "Sale Price (PKR) *", make_entry(form_card, sale_price_var),
        3, 0, ipady=5
    )
    add_field(
        "Purchase Price (PKR)",
        make_entry(form_card, purchase_price_var),
        3, 1, ipady=5
    )
    add_field(
        "Current Stock *", make_entry(form_card, stock_var),
        3, 2, ipady=5
    )

    image_row = tk.Frame(form_card, bg=CARD)
    add_field("Product Image", image_row, 3, 3)

    image_name_label = tk.Label(
        image_row,
        text="No image selected",
        bg=CARD,
        fg=MUTED,
        font=("Segoe UI", 9),
        anchor="w"
    )

    # Row 5-6: Note (full width, only two lines high)
    note_text = tk.Text(
        form_card,
        height=2,
        wrap="word",
        bg=INPUT_BG,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        font=("Segoe UI", 10),
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT
    )
    add_field("Product Note", note_text, 5, 0, span=4, bottom=10)

    # Row 7: Save and New / Clear buttons, centered under the form.
    # (No "sticky" option: the frame stays in the middle of the row.)
    bottom_buttons = tk.Frame(form_card, bg=CARD)
    bottom_buttons.grid(
        row=7, column=0, columnspan=4,
        padx=16, pady=(0, 14)
    )

    # --------------------------------------------------------
    # SAVED PRODUCTS CARD  (row 1 of the page - takes the rest)
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
        text="Saved Products",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 13, "bold")
    ).pack(side="left")

    product_count_label = tk.Label(
        table_header,
        text="0 products",
        bg=CARD,
        fg=MUTED,
        font=("Segoe UI", 9)
    )
    product_count_label.pack(side="right", padx=(10, 0))

    table_actions = tk.Frame(table_header, bg=CARD)
    table_actions.pack(side="right")

    def add_tooltip(widget, message):
        """Show a small tooltip when the mouse hovers over an icon."""
        tip = {"window": None}

        def show_tip(_event=None):
            if tip["window"] is not None:
                return
            popup = tk.Toplevel(widget)
            tip["window"] = popup
            popup.wm_overrideredirect(True)
            popup.configure(bg="#080B12")
            label = tk.Label(
                popup, text=message,
                bg="#080B12", fg="white",
                font=("Segoe UI", 9),
                padx=8, pady=4
            )
            label.pack()
            popup.update_idletasks()
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() - popup.winfo_reqheight() - 6
            popup.geometry(f"+{x}+{max(0, y)}")

        def hide_tip(_event=None):
            popup = tip["window"]
            if popup is not None:
                popup.destroy()
                tip["window"] = None

        widget.bind("<Enter>", show_tip)
        widget.bind("<Leave>", hide_tip)

    table_frame = tk.Frame(table_card, bg=CARD)
    table_frame.grid(
        row=1, column=0, sticky="nsew", padx=12, pady=(0, 12)
    )
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    columns = (
        "id", "name", "barcode", "sale_price",
        "purchase_price", "stock", "unit", "image", "note"
    )

    # height=6 is only a small request; the grid weight decides
    # the real height, so the table can never push the form away.
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="MyPOSProducts.Treeview",
        selectmode="browse",
        height=6
    )

    # (heading, width, minimum, alignment, may stretch?)
    column_settings = {
        "id":             ("Sr.",             45,  40, "center", False),
        "name":           ("Product Name",  180, 100, "w",      True),
        "barcode":        ("Barcode",       110,  80, "w",      False),
        "sale_price":     ("Sale Price",     90,  70, "e",      False),
        "purchase_price": ("Purchase Price", 105, 80, "e",      False),
        "stock":          ("Stock",          60,  50, "e",      False),
        "unit":           ("Unit",           75,  55, "w",      False),
        "image":          ("Image",          60,  50, "center", False),
        "note":           ("Note",          180, 100, "w",      True),
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
        style="MyPOS.Vertical.TScrollbar"
    )
    horizontal_scroll = ttk.Scrollbar(
        table_frame,
        orient="horizontal",
        command=tree.xview,
        style="MyPOS.Horizontal.TScrollbar"
    )

    tree.configure(
        yscrollcommand=vertical_scroll.set,
        xscrollcommand=horizontal_scroll.set
    )

    tree.grid(row=0, column=0, sticky="nsew")
    vertical_scroll.grid(row=0, column=1, sticky="ns")
    horizontal_scroll.grid(row=1, column=0, sticky="ew")

    # --------------------------------------------------------
    # IMAGE SELECTION
    # The image is copied into product_images/ when you press
    # Save, so cancelled forms never leave unused files behind.
    # --------------------------------------------------------

    def show_image_name(file_name):
        if file_name:
            image_name_label.config(
                text=shorten(file_name, 16), fg=TEXT
            )
        else:
            image_name_label.config(
                text="No image selected", fg=MUTED
            )

    def choose_image():
        file_path = filedialog.askopenfilename(
            title="Choose Product Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        source = Path(file_path)

        if source.suffix.lower() not in IMAGE_EXTENSIONS:
            messagebox.showerror(
                "Invalid Image",
                "Please select a PNG, JPG, JPEG, WEBP or BMP image.",
                parent=page
            )
            return

        if not source.is_file():
            messagebox.showerror(
                "Image Error",
                "The selected file could not be found.",
                parent=page
            )
            return

        pending_image["source"] = source
        show_image_name(source.name)

    make_button(
        image_row, "Choose Image", choose_image,
        bg=INPUT_BG, pady=4
    ).pack(side="left")

    image_name_label.pack(
        side="left", fill="x", expand=True, padx=(8, 0)
    )

    # --------------------------------------------------------
    # FORM ACTIONS
    # --------------------------------------------------------

    def clear_form():
        selected_product_id["value"] = None
        selected_image_path["value"] = ""
        pending_image["source"] = None

        name_var.set("")
        barcode_var.set("")
        sale_price_var.set("")
        purchase_price_var.set("")
        stock_var.set("0")
        unit_var.set("Piece")
        note_text.delete("1.0", "end")
        show_image_name("")

        tree.selection_set(())
        save_button.config(text="Save Product")

    def refresh_products():
        try:
            products = database.get_all_products()
            products = list(reversed(products))

            for item in tree.get_children():
                tree.delete(item)

            for index, product in enumerate(products):
                has_image = bool(product["image_path"])

                tree.insert(
                    "",
                    "end",
                    iid=str(product["id"]),
                    tags=("even" if index % 2 == 0 else "odd",),
                    values=(
                        product["id"],
                        product["name"],
                        product["barcode"] or "",
                        f'{float(product["price"]):,.2f}',
                        f'{float(product["purchase_price"] or 0):,.2f}',
                        product["stock"],
                        product["unit"] or "Piece",
                        "Yes" if has_image else "No",
                        shorten(single_line(product["note"]), 80)
                    )
                )

            count = len(products)
            product_count_label.config(
                text=f"{count} product{'s' if count != 1 else ''}"
            )

        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load products:\n{error}",
                parent=page
            )

    def save_product():
        name = name_var.get().strip()
        barcode = barcode_var.get().strip()
        unit = unit_var.get().strip() or "Piece"
        note = note_text.get("1.0", "end").strip()

        # ---- Validation ----
        try:
            if not name:
                raise ValueError("Please enter a product name.")

            if len(name) > MAX_NAME_LENGTH:
                raise ValueError(
                    f"Product name must be {MAX_NAME_LENGTH} "
                    "characters or fewer."
                )

            if barcode:
                if len(barcode) > MAX_BARCODE_LENGTH:
                    raise ValueError(
                        f"Barcode must be {MAX_BARCODE_LENGTH} "
                        "characters or fewer."
                    )
                if any(ch.isspace() for ch in barcode):
                    raise ValueError(
                        "Barcode cannot contain spaces."
                    )

            sale_price = parse_number(
                sale_price_var.get(), "Sale price"
            )
            purchase_price = parse_number(
                purchase_price_var.get(), "Purchase price",
                required=False
            )
            stock_value = parse_number(stock_var.get(), "Stock")

            if not stock_value.is_integer():
                raise ValueError(
                    "Stock must be a whole number, for example 10."
                )

            stock = int(stock_value)

        except ValueError as error:
            messagebox.showwarning(
                "Check Product Details",
                str(error),
                parent=page
            )
            return

        # ---- Copy a newly chosen image ----
        image_path = selected_image_path["value"]
        new_image_file = None

        if pending_image["source"] is not None:
            try:
                new_image_file = copy_image_to_project(
                    pending_image["source"]
                )
                image_path = str(new_image_file.relative_to(BASE_DIR))
            except OSError as error:
                messagebox.showerror(
                    "Image Error",
                    f"Could not save the image:\n{error}",
                    parent=page
                )
                return

        # ---- Save to the database ----
        try:
            if selected_product_id["value"] is None:
                database.add_product(
                    name, barcode, sale_price, stock,
                    purchase_price, image_path, unit, note
                )
                success_message = "Product added successfully."
            else:
                database.update_product(
                    selected_product_id["value"],
                    name, barcode, sale_price, stock,
                    purchase_price, image_path, unit, note
                )
                success_message = "Product updated successfully."

        except sqlite3.IntegrityError as error:
            remove_file_quietly(new_image_file)

            if "barcode" in str(error).lower():
                messagebox.showerror(
                    "Duplicate Barcode",
                    "This barcode is already assigned to "
                    "another product.",
                    parent=page
                )
            else:
                messagebox.showerror(
                    "Could Not Save Product",
                    str(error),
                    parent=page
                )
            return

        except (sqlite3.Error, ValueError) as error:
            remove_file_quietly(new_image_file)
            messagebox.showerror(
                "Could Not Save Product",
                str(error),
                parent=page
            )
            return

        refresh_products()
        clear_form()

        messagebox.showinfo(
            "Success", success_message, parent=page
        )

    def select_product(_event=None):
        selection = tree.selection()

        if not selection:
            return

        try:
            product_id = int(selection[0])
            product = database.get_product(product_id)

            if product is None:
                messagebox.showwarning(
                    "Product Not Found",
                    "This product no longer exists.",
                    parent=page
                )
                refresh_products()
                return

            selected_product_id["value"] = product_id
            pending_image["source"] = None

            name_var.set(product["name"] or "")
            barcode_var.set(product["barcode"] or "")
            sale_price_var.set(str(product["price"]))
            purchase_price_var.set(
                str(product["purchase_price"] or 0)
            )
            stock_var.set(str(product["stock"]))
            unit_var.set(product["unit"] or "Piece")

            note_text.delete("1.0", "end")
            note_text.insert("1.0", product["note"] or "")

            selected_image_path["value"] = (
                product["image_path"] or ""
            )
            if selected_image_path["value"]:
                show_image_name(
                    Path(selected_image_path["value"]).name
                )
            else:
                show_image_name("")

            save_button.config(text="Update Product")

        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            messagebox.showerror(
                "Could Not Open Product",
                str(error),
                parent=page
            )

    def remove_product():
        product_id = selected_product_id["value"]

        if product_id is None:
            selection = tree.selection()

            if not selection:
                messagebox.showwarning(
                    "Select Product",
                    "Select a product to delete.",
                    parent=page
                )
                return

            product_id = int(selection[0])

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            "Delete this product?\n\n"
            "Old sales will keep its name and price, "
            "but the product cannot be restored.",
            parent=page
        )
        

        if not confirmed:
            return

        try:
            database.delete_product(product_id)
            clear_form()
            refresh_products()

            messagebox.showinfo(
                "Success",
                "Product deleted successfully.",
                parent=page
            )

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Cannot Delete",
                "This product is linked to saved sales. "
                "Keep it in the database instead.",
                parent=page
            )

        except (sqlite3.Error, ValueError) as error:
            messagebox.showerror(
                "Delete Failed",
                str(error),
                parent=page
            )

    # --------------------------------------------------------
    # ACTION BUTTONSf
    # Save Product and New / Clear: centered under the form.
    # Edit / Delete / Refresh icons: beside Saved Products.
    # --------------------------------------------------------

    save_button = make_button(
        bottom_buttons, "Save Product", save_product, pady=8
    )
    save_button.pack(side="left", padx=(0, 8))

    clear_button = make_button(
        bottom_buttons, "Cancel", clear_form,
        bg="#A31616", pady=8
    )
    clear_button.pack(side="left")

    def update_selected_product():
        if selected_product_id["value"] is None:
            selection = tree.selection()
            if not selection:
                messagebox.showinfo(
                    "Select Product",
                    "Select a product row first, then click the edit icon.",
                    parent=page
                )
                return
            select_product()
        if selected_product_id["value"] is not None:
            save_product()

    # Icon buttons are compact; tooltips explain their actions.
    edit_icon_button = make_button(
        table_actions, "\u270e", update_selected_product,
        bg=ACCENT, pady=4
    )
    edit_icon_button.config(
        font=("Segoe UI Symbol", 13, "bold"),
        padx=11, width=2
    )
    edit_icon_button.pack(side="left", padx=(0, 6))
    add_tooltip(edit_icon_button, "Update selected product")

    delete_icon_button = make_button(
        table_actions, "\U0001F5D1", remove_product,
        bg=DANGER, pady=4
    )
    delete_icon_button.config(
        text="\U0001F5D1", font=("Segoe UI Emoji", 11),
        padx=11, width=2
    )
    delete_icon_button.pack(side="left", padx=(0, 6))
    add_tooltip(delete_icon_button, "Delete selected product")

    refresh_icon_button = make_button(
        table_actions, "\u21bb", refresh_products,
        bg="#16A34A", pady=4
    )
    refresh_icon_button.config(
        font=("Segoe UI Symbol", 13, "bold"),
        padx=11, width=2
    )
    refresh_icon_button.pack(side="left", padx=(0, 8))
    add_tooltip(refresh_icon_button, "Refresh products list")

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    tree.bind("<<TreeviewSelect>>", select_product)

    refresh_products()

    return page