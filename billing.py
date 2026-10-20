
# ============================================================
# MyPOS - Billing and Checkout
# File: billing.py
# Purpose: Product selection, temporary cart and checkout
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

import database


def create_billing_page(parent, cart):
    """
    Build the billing screen.

    cart is a Python dictionary owned by main.py.
    It survives navigation between screens but not app restarts.
    """

    page = ttk.Frame(parent, padding=16)
    page.pack(fill="both", expand=True)

    # -------------------- Page Heading --------------------
    ttk.Label(
        page,
        text="Billing / Checkout",
        font=("Segoe UI", 20, "bold")
    ).pack(anchor="w")

    ttk.Label(
        page,
        text="Select a product, choose quantity and add it to the cart."
    ).pack(anchor="w", pady=(4, 12))

    # -------------------- Product List --------------------
    product_frame = ttk.LabelFrame(
        page, text="Available Products", padding=8
    )
    product_frame.pack(fill="both", expand=True, pady=(0, 10))

    product_columns = ("id", "name", "price", "stock")
    product_table = ttk.Treeview(
        product_frame,
        columns=product_columns,
        show="headings",
        height=7,
        selectmode="browse"
    )

    product_table.heading("id", text="ID")
    product_table.heading("name", text="Product")
    product_table.heading("price", text="Price (PKR)")
    product_table.heading("stock", text="Available Stock")

    product_table.column("id", width=50, anchor="center")
    product_table.column("name", width=250)
    product_table.column("price", width=130, anchor="e")
    product_table.column("stock", width=120, anchor="center")

    product_scrollbar = ttk.Scrollbar(
        product_frame,
        orient="vertical",
        command=product_table.yview
    )
    product_table.configure(yscrollcommand=product_scrollbar.set)

    product_table.pack(side="left", fill="both", expand=True)
    product_scrollbar.pack(side="right", fill="y")

    # -------------------- Add to Cart Controls --------------------
    controls = ttk.Frame(page)
    controls.pack(fill="x", pady=(0, 12))

    ttk.Label(controls, text="Quantity:").pack(side="left")

    quantity_var = tk.StringVar(value="1")
    quantity_entry = ttk.Entry(
        controls, textvariable=quantity_var, width=8
    )
    quantity_entry.pack(side="left", padx=8)

    # -------------------- Cart Table --------------------
    cart_frame = ttk.LabelFrame(page, text="Current Cart", padding=8)
    cart_frame.pack(fill="both", expand=True)

    cart_columns = (
        "id", "name", "price", "quantity", "subtotal"
    )

    cart_table = ttk.Treeview(
        cart_frame,
        columns=cart_columns,
        show="headings",
        height=6,
        selectmode="browse"
    )

    cart_headings = {
        "id": "Product ID",
        "name": "Product",
        "price": "Unit Price",
        "quantity": "Quantity",
        "subtotal": "Subtotal"
    }

    for column, heading in cart_headings.items():
        cart_table.heading(column, text=heading)

    cart_table.column("id", width=70, anchor="center")
    cart_table.column("name", width=220)
    cart_table.column("price", width=110, anchor="e")
    cart_table.column("quantity", width=90, anchor="center")
    cart_table.column("subtotal", width=120, anchor="e")

    cart_scrollbar = ttk.Scrollbar(
        cart_frame,
        orient="vertical",
        command=cart_table.yview
    )
    cart_table.configure(yscrollcommand=cart_scrollbar.set)

    cart_table.pack(side="left", fill="both", expand=True)
    cart_scrollbar.pack(side="right", fill="y")

    # -------------------- Total and Actions --------------------
    footer = ttk.Frame(page)
    footer.pack(fill="x", pady=(12, 0))

    total_var = tk.StringVar(value="Total: PKR 0.00")

    ttk.Label(
        footer,
        textvariable=total_var,
        font=("Segoe UI", 16, "bold")
    ).pack(side="left")

    # -------------------- Refresh Products --------------------
    def refresh_products():
        """Reload current products and their stock."""

        rows = database.get_all_products()
        current_products = {row["id"]: row for row in rows}

        for row in product_table.get_children():
            product_table.delete(row)

        for product in rows:
            product_table.insert("", "end", values=(
                product["id"],
                product["name"],
                f'{product["price"]:.2f}',
                product["stock"]
            ))

        # Refresh cart details if a product's price/name changed.
        for product_id, item in list(cart.items()):
            current = current_products.get(product_id)

            if current is not None:
                item["name"] = current["name"]
                item["price"] = float(current["price"])

        refresh_cart()

    # -------------------- Refresh Cart --------------------
    def refresh_cart():
        """Redraw cart rows and calculate the displayed total."""

        for row in cart_table.get_children():
            cart_table.delete(row)

        total = 0.0

        for product_id, item in cart.items():
            subtotal = round(item["price"] * item["quantity"], 2)
            total = round(total + subtotal, 2)

            cart_table.insert("", "end", values=(
                product_id,
                item["name"],
                f'{item["price"]:.2f}',
                item["quantity"],
                f"{subtotal:.2f}"
            ))

        total_var.set(f"Total: PKR {total:,.2f}")

    # -------------------- Add Product to Cart --------------------
    def add_to_cart():
        """Add the selected product to the temporary cart."""

        selection = product_table.selection()

        if not selection:
            messagebox.showwarning(
                "Select Product",
                "Select a product from the product list first."
            )
            return

        try:
            quantity = int(quantity_var.get().strip())

            if quantity <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid Quantity",
                "Enter a positive whole number for quantity."
            )
            return

        values = product_table.item(selection[0], "values")

        product_id = int(values[0])
        name = values[1]
        price = float(values[2])
        available_stock = int(values[3])

        if available_stock < 1:
            messagebox.showwarning(
                "Out of Stock",
                f"{name} is currently out of stock."
            )
            return

        existing_quantity = cart.get(
            product_id, {}
        ).get("quantity", 0)

        if existing_quantity + quantity > available_stock:
            messagebox.showwarning(
                "Insufficient Stock",
                f"Available stock for {name}: {available_stock}.\n"
                f"Already in cart: {existing_quantity}."
            )
            return

        if product_id in cart:
            cart[product_id]["quantity"] += quantity
        else:
            cart[product_id] = {
                "product_id": product_id,
                "name": name,
                "price": price,
                "quantity": quantity
            }

        quantity_var.set("1")
        refresh_cart()

    # -------------------- Remove Cart Item --------------------
    def remove_from_cart():
        """Remove the selected product from the cart."""

        selection = cart_table.selection()

        if not selection:
            messagebox.showwarning(
                "Select Item",
                "Select an item from the cart first."
            )
            return

        values = cart_table.item(selection[0], "values")
        product_id = int(values[0])

        cart.pop(product_id, None)
        refresh_cart()

    # -------------------- Clear Cart --------------------
    def clear_cart():
        """Empty the temporary cart."""

        if not cart:
            return

        if messagebox.askyesno(
            "Clear Cart",
            "Remove all items from the current cart?"
        ):
            cart.clear()
            refresh_cart()

    # -------------------- Complete Sale --------------------
    def checkout():
        """Send cart quantities to the database transaction."""

        if not cart:
            messagebox.showwarning(
                "Empty Cart",
                "Add at least one product before checkout."
            )
            return

        displayed_total = round(
            sum(
                item["price"] * item["quantity"]
                for item in cart.values()
            ),
            2
        )

        confirmed = messagebox.askyesno(
            "Confirm Sale",
            f"Complete this sale?\n\n"
            f"Total: PKR {displayed_total:,.2f}"
        )

        if not confirmed:
            return

        # Send only IDs and quantities.
        # The database reads authoritative prices and stock.
        sale_request = [
            {
                "product_id": product_id,
                "quantity": item["quantity"]
            }
            for product_id, item in cart.items()
        ]

        try:
            result = database.complete_sale(sale_request)

            # Clear cart only after the sale has committed.
            cart.clear()
            refresh_products()

            messagebox.showinfo(
                "Sale Completed",
                f"Sale ID: {result['sale_id']}\n"
                f"Total: PKR {result['total']:,.2f}\n\n"
                "Sale saved and stock updated successfully."
            )

        except Exception as error:
            # Keep the cart so the user can correct the issue.
            refresh_products()

            messagebox.showerror(
                "Checkout Failed",
                f"The sale could not be completed.\n\n{error}\n\n"
                "The database transaction was rolled back."
            )

    # -------------------- Buttons --------------------
    ttk.Button(
        controls,
        text="Add to Cart",
        command=add_to_cart
    ).pack(side="left", padx=(4, 8))

    ttk.Button(
        controls,
        text="Remove Item",
        command=remove_from_cart
    ).pack(side="left", padx=4)

    ttk.Button(
        controls,
        text="Clear Cart",
        command=clear_cart
    ).pack(side="left", padx=4)

    ttk.Button(
        footer,
        text="Complete Sale",
        command=checkout
    ).pack(side="right")

    # Load products and any cart items retained from navigation.
    refresh_products()

    return page
