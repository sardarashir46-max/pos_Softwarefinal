
# ============================================================
# MyPOS - Main Application
# File: main.py
# Purpose: Start the app and navigate between screens
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

import database
from products import create_products_page
from billing import create_billing_page


def main():
    # Ensure tables exist before showing any screen.
    database.initialize_database()

    root = tk.Tk()
    root.title("MyPOS - Desktop Point of Sale")
    root.geometry("1150x780")
    root.minsize(900, 620)

    # Temporary cart shared between screens.
    # It disappears when the application closes.
    cart = {}

    # -------------------- Header --------------------
    header = ttk.Frame(root, padding=(20, 15))
    header.pack(fill="x")

    ttk.Label(
        header,
        text="MyPOS",
        font=("Segoe UI", 22, "bold")
    ).pack(side="left")

    ttk.Label(
        header,
        text="Desktop Point of Sale",
        font=("Segoe UI", 10)
    ).pack(side="left", padx=15, pady=(8, 0))

    # -------------------- Navigation --------------------
    navigation = ttk.Frame(root, padding=(20, 0, 20, 10))
    navigation.pack(fill="x")

    content = ttk.Frame(root)
    content.pack(fill="both", expand=True)

    def clear_screen():
        """Remove the previous screen from the content area."""

        for widget in content.winfo_children():
            widget.destroy()

    def show_dashboard():
        """Display the home screen."""

        clear_screen()

        dashboard = ttk.Frame(content, padding=25)
        dashboard.pack(fill="both", expand=True)

        ttk.Label(
            dashboard,
            text="Welcome to MyPOS",
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w")

        ttk.Label(
            dashboard,
            text=(
                "Manage products, create customer bills, "
                "and keep your stock updated."
            ),
            wraplength=650
        ).pack(anchor="w", pady=12)

        ttk.Button(
            dashboard,
            text="Open Billing / Checkout",
            command=open_billing
        ).pack(anchor="w", pady=8)

        ttk.Button(
            dashboard,
            text="Manage Products",
            command=open_products
        ).pack(anchor="w", pady=4)

    def open_products():
        """Open the existing product management screen."""

        clear_screen()
        create_products_page(content)

    def open_billing():
        """Open billing while retaining the in-memory cart."""

        clear_screen()
        create_billing_page(content, cart)

    # -------------------- Navigation Buttons --------------------
    ttk.Button(
        navigation,
        text="Dashboard",
        command=show_dashboard
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        navigation,
        text="Products",
        command=open_products
    ).pack(side="left", padx=8)

    ttk.Button(
        navigation,
        text="Billing / Checkout",
        command=open_billing
    ).pack(side="left", padx=8)

    # -------------------- Start Application --------------------
    show_dashboard()
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        messagebox.showerror(
            "MyPOS Startup Error",
            f"Application could not start:\n{error}"
        )
 