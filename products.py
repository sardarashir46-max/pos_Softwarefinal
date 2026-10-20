
# ============================================================
# MyPOS - Product Management Screen
# File: products.py
# Purpose: Add, view, update and delete products
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

import database


def create_products_page(parent):
    """Build the complete product management screen."""

    selected_product_id = {"value": None}

    page = ttk.Frame(parent, padding=20)
    page.pack(fill="both", expand=True)

    # -------------------- Page Heading --------------------
    ttk.Label(
        page,
        text="Product Management",
        font=("Segoe UI", 20, "bold")
    ).pack(anchor="w")

    ttk.Label(
        page,
        text="Add products and manage prices and stock."
    ).pack(anchor="w", pady=(4, 16))

    # -------------------- Product Form --------------------
    form = ttk.LabelFrame(page, text="Product Details", padding=12)
    form.pack(fill="x", pady=(0, 15))

    name_var = tk.StringVar()
    barcode_var = tk.StringVar()
    price_var = tk.StringVar()
    stock_var = tk.StringVar(value="0")

    ttk.Label(form, text="Product Name").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )
    name_entry = ttk.Entry(form, textvariable=name_var, width=28)
    name_entry.grid(row=1, column=0, sticky="ew", padx=5)

    ttk.Label(form, text="Barcode (optional)").grid(
        row=0, column=1, sticky="w", padx=5, pady=5
    )
    ttk.Entry(form, textvariable=barcode_var, width=22).grid(
        row=1, column=1, sticky="ew", padx=5
    )

    ttk.Label(form, text="Selling Price (PKR)").grid(
        row=0, column=2, sticky="w", padx=5, pady=5
    )
    ttk.Entry(form, textvariable=price_var, width=16).grid(
        row=1, column=2, sticky="ew", padx=5
    )

    ttk.Label(form, text="Opening Stock").grid(
        row=0, column=3, sticky="w", padx=5, pady=5
    )
    ttk.Entry(form, textvariable=stock_var, width=12).grid(
        row=1, column=3, sticky="ew", padx=5
    )

    # -------------------- Product Table --------------------
    table_frame = ttk.LabelFrame(page, text="Saved Products", padding=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "name", "barcode", "price", "stock")

    table = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        selectmode="browse"
    )

    headings = {
        "id": "ID",
        "name": "Product Name",
        "barcode": "Barcode",
        "price": "Price (PKR)",
        "stock": "Stock"
    }

    for column, heading in headings.items():
        table.heading(column, text=heading)

    table.column("id", width=55, anchor="center")
    table.column("name", width=230)
    table.column("barcode", width=160)
    table.column("price", width=120, anchor="e")
    table.column("stock", width=90, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame, orient="vertical", command=table.yview
    )
    table.configure(yscrollcommand=scrollbar.set)

    table.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # -------------------- Screen Actions --------------------
    def refresh_products():
        """Reload the table from the database."""

        for item in table.get_children():
            table.delete(item)

        for product in database.get_all_products():
            table.insert("", "end", values=(
                product["id"],
                product["name"],
                product["barcode"] or "",
                f'{product["price"]:.2f}',
                product["stock"]
            ))

    def clear_form():
        """Clear fields and switch back to Add mode."""

        selected_product_id["value"] = None
        name_var.set("")
        barcode_var.set("")
        price_var.set("")
        stock_var.set("0")

        for item in table.selection():
            table.selection_remove(item)

        name_entry.focus_set()

    def save_product():
        """Validate the form, then insert or update."""

        name = name_var.get().strip()
        barcode = barcode_var.get().strip()

        if not name:
            messagebox.showerror(
                "Validation Error", "Enter a product name."
            )
            return

        try:
            price = float(price_var.get())
            stock_text = stock_var.get().strip()
            stock = int(stock_text)

            if price < 0 or stock < 0:
                raise ValueError

            if not price < float("inf"):
                raise ValueError

        except (ValueError, OverflowError):
            messagebox.showerror(
                "Validation Error",
                "Price must be a valid non-negative number "
                "and stock must be a non-negative whole number."
            )
            return

        try:
            product_id = selected_product_id["value"]

            if product_id is None:
                database.add_product(name, barcode, price, stock)
                messagebox.showinfo("Success", "Product added.")
            else:
                database.update_product(
                    product_id, name, barcode, price, stock
                )
                messagebox.showinfo("Success", "Product updated.")

            refresh_products()
            clear_form()

        except Exception as error:
            messagebox.showerror("Database Error", str(error))

    def select_product(event=None):
        """Load a selected table row into the form."""

        selection = table.selection()

        if not selection:
            return

        values = table.item(selection[0], "values")

        selected_product_id["value"] = int(values[0])
        name_var.set(values[1])
        barcode_var.set(values[2])
        price_var.set(values[3])
        stock_var.set(values[4])

    def remove_product():
        """Delete the selected product after confirmation."""

        product_id = selected_product_id["value"]

        if product_id is None:
            messagebox.showwarning(
                "Select Product", "Select a product from the table first."
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this product?"
        )

        if not confirmed:
            return

        try:
            database.delete_product(product_id)
            refresh_products()
            clear_form()
            messagebox.showinfo("Success", "Product deleted.")

        except Exception as error:
            messagebox.showerror("Database Error", str(error))

    table.bind("<<TreeviewSelect>>", select_product)

    # -------------------- Buttons --------------------
    buttons = ttk.Frame(page)
    buttons.pack(fill="x", pady=(12, 0))

    ttk.Button(
        buttons, text="Save Product", command=save_product
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        buttons, text="New / Clear", command=clear_form
    ).pack(side="left", padx=8)

    ttk.Button(
        buttons, text="Delete Selected", command=remove_product
    ).pack(side="left", padx=8)

    ttk.Button(
        buttons, text="Refresh", command=refresh_products
    ).pack(side="right")

    refresh_products()
    return page
