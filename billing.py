
import tkinter as tk
from tkinter import ttk, messagebox

import database
from receipt import generate_receipt


def create_billing_page(parent, cart):
    """
    Create the Billing / Checkout screen.

    parent: Frame in which the billing screen will appear.
    cart: Shared cart dictionary maintained by main.py.
    """

    # ---------------------------------------------------------
    # MAIN SCREEN
    # ---------------------------------------------------------

    container = ttk.Frame(parent, padding=15)
    container.pack(fill="both", expand=True)

    title = ttk.Label(
        container,
        text="Billing / Checkout",
        font=("Arial", 20, "bold")
    )
    title.pack(anchor="w", pady=(0, 5))

    subtitle = ttk.Label(
        container,
        text="Select products, manage the cart, and complete a sale."
    )
    subtitle.pack(anchor="w", pady=(0, 15))

    # ---------------------------------------------------------
    # MAIN CONTENT: PRODUCTS AND CART
    # ---------------------------------------------------------

    content = ttk.Frame(container)
    content.pack(fill="both", expand=True)

    content.columnconfigure(0, weight=3)
    content.columnconfigure(1, weight=2)
    content.rowconfigure(0, weight=1)

    # =========================================================
    # LEFT SIDE: AVAILABLE PRODUCTS
    # =========================================================

    products_frame = ttk.LabelFrame(
        content,
        text="Available Products",
        padding=10
    )
    products_frame.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=(0, 8)
    )

    products_frame.columnconfigure(0, weight=1)
    products_frame.rowconfigure(0, weight=1)

    product_columns = (
        "id",
        "name",
        "price",
        "stock"
    )

    products_tree = ttk.Treeview(
        products_frame,
        columns=product_columns,
        show="headings",
        selectmode="browse",
        height=15
    )

    products_tree.heading("id", text="ID")
    products_tree.heading("name", text="Product")
    products_tree.heading("price", text="Price (Rs.)")
    products_tree.heading("stock", text="Stock")

    products_tree.column("id", width=45, anchor="center")
    products_tree.column("name", width=180)
    products_tree.column("price", width=100, anchor="e")
    products_tree.column("stock", width=65, anchor="center")

    products_scrollbar = ttk.Scrollbar(
        products_frame,
        orient="vertical",
        command=products_tree.yview
    )

    products_tree.configure(
        yscrollcommand=products_scrollbar.set
    )

    products_tree.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    products_scrollbar.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    # Quantity controls
    quantity_frame = ttk.Frame(products_frame)
    quantity_frame.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(12, 0)
    )

    ttk.Label(
        quantity_frame,
        text="Quantity:"
    ).pack(side="left", padx=(0, 8))

    quantity_var = tk.StringVar(value="1")

    quantity_entry = ttk.Entry(
        quantity_frame,
        textvariable=quantity_var,
        width=10
    )
    quantity_entry.pack(side="left")

    add_button = ttk.Button(
        quantity_frame,
        text="Add to Cart"
    )
    add_button.pack(side="left", padx=10)

    refresh_products_button = ttk.Button(
        quantity_frame,
        text="Refresh Products"
    )
    refresh_products_button.pack(side="left")

    # =========================================================
    # RIGHT SIDE: SHOPPING CART
    # =========================================================

    cart_frame = ttk.LabelFrame(
        content,
        text="Shopping Cart",
        padding=10
    )
    cart_frame.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=(8, 0)
    )

    cart_frame.columnconfigure(0, weight=1)
    cart_frame.rowconfigure(0, weight=1)

    cart_columns = (
        "name",
        "quantity",
        "price",
        "subtotal"
    )

    cart_tree = ttk.Treeview(
        cart_frame,
        columns=cart_columns,
        show="headings",
        selectmode="browse",
        height=15
    )

    cart_tree.heading("name", text="Product")
    cart_tree.heading("quantity", text="Qty")
    cart_tree.heading("price", text="Price")
    cart_tree.heading("subtotal", text="Subtotal")

    cart_tree.column("name", width=135)
    cart_tree.column("quantity", width=45, anchor="center")
    cart_tree.column("price", width=75, anchor="e")
    cart_tree.column("subtotal", width=90, anchor="e")

    cart_scrollbar = ttk.Scrollbar(
        cart_frame,
        orient="vertical",
        command=cart_tree.yview
    )

    cart_tree.configure(
        yscrollcommand=cart_scrollbar.set
    )

    cart_tree.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    cart_scrollbar.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    # ---------------------------------------------------------
    # CART BUTTONS
    # ---------------------------------------------------------

    cart_buttons = ttk.Frame(cart_frame)
    cart_buttons.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(12, 5)
    )

    remove_button = ttk.Button(
        cart_buttons,
        text="Remove Item"
    )
    remove_button.pack(side="left", padx=(0, 5))

    clear_button = ttk.Button(
        cart_buttons,
        text="Clear Cart"
    )
    clear_button.pack(side="left")

    # ---------------------------------------------------------
    # TOTAL AMOUNT
    # ---------------------------------------------------------

    total_frame = ttk.Frame(cart_frame)
    total_frame.grid(
        row=2,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(12, 5)
    )

    ttk.Label(
        total_frame,
        text="Grand Total:",
        font=("Arial", 13, "bold")
    ).pack(side="left")

    total_var = tk.StringVar(value="Rs. 0.00")

    ttk.Label(
        total_frame,
        textvariable=total_var,
        font=("Arial", 13, "bold")
    ).pack(side="right")

    checkout_button = ttk.Button(
        cart_frame,
        text="Complete Sale"
    )
    checkout_button.grid(
        row=3,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(12, 0),
        ipady=5
    )

    # =========================================================
    # FUNCTIONS
    # =========================================================

    def refresh_products():
        """Load the latest products and stock from the database."""

        products_tree.delete(*products_tree.get_children())

        try:
            products = database.get_all_products()

            for product in products:
                products_tree.insert(
                    "",
                    "end",
                    iid=str(product["id"]),
                    values=(
                        product["id"],
                        product["name"],
                        f'{float(product["price"]):,.2f}',
                        product["stock"]
                    )
                )

        except Exception as error:
            messagebox.showerror(
                "Products Error",
                f"Could not load products.\n\n{error}",
                parent=container
            )

    def refresh_cart():
        """Refresh the cart table and calculate its displayed total."""

        cart_tree.delete(*cart_tree.get_children())

        grand_total = 0.0

        for product_id, item in cart.items():
            quantity = int(item["quantity"])
            price = float(item["price"])
            subtotal = quantity * price

            grand_total += subtotal

            cart_tree.insert(
                "",
                "end",
                iid=str(product_id),
                values=(
                    item["name"],
                    quantity,
                    f"{price:,.2f}",
                    f"{subtotal:,.2f}"
                )
            )

        total_var.set(f"Rs. {grand_total:,.2f}")

    def add_to_cart():
        """Add the selected product and quantity to the cart."""

        selected = products_tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Product",
                "Please select a product first.",
                parent=container
            )
            return

        try:
            quantity = int(quantity_var.get().strip())

            if quantity <= 0:
                raise ValueError

        except ValueError:
            messagebox.showwarning(
                "Invalid Quantity",
                "Enter a whole number greater than zero.",
                parent=container
            )
            return

        product_id = int(selected[0])

        try:
            # Read current data rather than relying only on
            # the values displayed in the products table.
            products = database.get_all_products()

            product = next(
                (
                    item for item in products
                    if int(item["id"]) == product_id
                ),
                None
            )

            if product is None:
                messagebox.showwarning(
                    "Product Not Found",
                    "This product no longer exists. Refresh the list.",
                    parent=container
                )
                refresh_products()
                return

            stock = int(product["stock"])
            current_quantity = int(
                cart.get(product_id, {}).get("quantity", 0)
            )

            if stock <= 0:
                messagebox.showwarning(
                    "Out of Stock",
                    "This product is currently out of stock.",
                    parent=container
                )
                return

            if current_quantity + quantity > stock:
                messagebox.showwarning(
                    "Insufficient Stock",
                    f"Available stock: {stock}\n"
                    f"Already in cart: {current_quantity}\n"
                    f"Requested quantity: {quantity}",
                    parent=container
                )
                return

            # Add to an existing cart item or create a new one.
            if product_id in cart:
                cart[product_id]["quantity"] += quantity
                cart[product_id]["name"] = product["name"]
                cart[product_id]["price"] = float(product["price"])

            else:
                cart[product_id] = {
                    "product_id": product_id,
                    "name": product["name"],
                    "price": float(product["price"]),
                    "quantity": quantity
                }

            refresh_cart()
            quantity_var.set("1")

        except Exception as error:
            messagebox.showerror(
                "Cart Error",
                f"Could not add the product.\n\n{error}",
                parent=container
            )

    def remove_from_cart():
        """Remove the selected item from the cart."""

        selected = cart_tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Item",
                "Please select a cart item to remove.",
                parent=container
            )
            return

        product_id = int(selected[0])

        if product_id in cart:
            del cart[product_id]

        refresh_cart()

    def clear_cart():
        """Remove every item from the current cart."""

        if not cart:
            messagebox.showinfo(
                "Cart Empty",
                "The cart is already empty.",
                parent=container
            )
            return

        confirm = messagebox.askyesno(
            "Clear Cart",
            "Are you sure you want to remove all items?",
            parent=container
        )

        if confirm:
            cart.clear()
            refresh_cart()

    def complete_checkout():
        """
        Save the sale transaction.

        Clear the cart only after the database confirms success.
        Receipt errors must not cause the sale to be repeated.
        """

        if not cart:
            messagebox.showwarning(
                "Empty Cart",
                "Add at least one product before checkout.",
                parent=container
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Sale",
            f"Complete this sale?\n\n{total_var.get()}",
            parent=container
        )

        if not confirm:
            return

        # The database checks the real stock and prices again.
        cart_items = [
            {
                "product_id": int(item["product_id"]),
                "quantity": int(item["quantity"])
            }
            for item in cart.values()
        ]

        try:
            sale = database.complete_sale(cart_items)

        except Exception as error:
            messagebox.showerror(
                "Checkout Failed",
                "The sale could not be completed.\n\n"
                f"Reason: {error}\n\n"
                "Your cart has been kept so you can review it.",
                parent=container
            )

            refresh_products()
            return

        # The database transaction succeeded. Do not retry this
        # sale just because receipt generation might fail.
        cart.clear()
        refresh_cart()
        refresh_products()

        # Receipt creation is separate from the saved transaction.
        try:
            receipt_path = generate_receipt(sale)

            messagebox.showinfo(
                "Sale Completed",
                f"Sale ID: {sale['sale_id']}\n"
                f"Total: Rs. {float(sale['total']):,.2f}\n\n"
                "The sale was saved successfully.\n"
                "Receipt saved to:\n"
                f"{receipt_path}",
                parent=container
            )

        except Exception as error:
            messagebox.showwarning(
                "Sale Completed - Receipt Error",
                f"Sale ID: {sale['sale_id']}\n"
                f"Total: Rs. {float(sale['total']):,.2f}\n\n"
                "The sale was saved successfully, but the receipt "
                "could not be generated or opened.\n\n"
                f"Reason: {error}\n\n"
                "Do not complete the same sale again.",
                parent=container
            )

    # ---------------------------------------------------------
    # CONNECT BUTTONS TO FUNCTIONS
    # ---------------------------------------------------------

    add_button.configure(command=add_to_cart)

    remove_button.configure(command=remove_from_cart)

    clear_button.configure(command=clear_cart)

    checkout_button.configure(command=complete_checkout)

    refresh_products_button.configure(command=refresh_products)

    # ---------------------------------------------------------
    # INITIAL SCREEN DATA
    # ---------------------------------------------------------

    refresh_products()
    refresh_cart()
