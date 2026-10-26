# ============================================================
# MyPOS - Modern Desktop Point of Sale
# File: main.py
# UI: Tkinter + SQLite
# Theme: Dark Charcoal / Purple / Blue
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import database
from products import create_products_page
from categories import create_categories_page
from login import run_login, initialize_users_table
from billing import create_billing_page
from sales_history import create_sales_history_page


# ============================================================
# 1. APPLICATION COLORS
# ============================================================

BG_COLOR = "#111318"
SIDEBAR_COLOR = "#191B24"
CARD_COLOR = "#1E212B"
CARD_HOVER = "#282C39"

PURPLE = "#7958F5"
PURPLE_HOVER = "#6847E5"
BLUE = "#3987F5"

TEXT_COLOR = "#F4F5FA"
MUTED_COLOR = "#A0A5B5"
BORDER_COLOR = "#303442"

SUCCESS_COLOR = "#35C995"
WARNING_COLOR = "#F5B942"
DANGER_COLOR = "#F16D79"


# ============================================================
# 2. MAIN APPLICATION CLASS
# ============================================================

class MyPOSApp:

    def __init__(self, root, current_user=None):
        self.root = root
        self.root.title("MyPOS | Point of Sale")
        self.root.geometry("1250x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG_COLOR)

        # Shared cart used by the existing billing module.
        self.cart = {}

        # The person who logged in (set by login.py).
        self.current_user = current_user or {
            "username": "User", "role": "admin"
        }

        self.current_page = "Dashboard"
        self.navigation_buttons = {}

        # Keep existing database and records.
        database.initialize_database()
       

        self.configure_styles()
        self.create_layout()
        self.show_dashboard()

    # ========================================================
    # 3. GLOBAL TKINTER STYLES
    # ========================================================

    def configure_styles(self):
        style = ttk.Style()

        # Use a theme that supports custom colors.
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=CARD_COLOR,
            foreground=TEXT_COLOR,
            fieldbackground=CARD_COLOR,
            borderwidth=0,
            rowheight=36,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Treeview.Heading",
            background=SIDEBAR_COLOR,
            foreground=TEXT_COLOR,
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 12)
        )

        style.map(
            "Treeview",
            background=[("selected", PURPLE)],
            foreground=[("selected", "#FFFFFF")]
        )

        style.map(
            "Treeview.Heading",
            background=[("active", CARD_HOVER)]
        )

        style.configure(
            "Vertical.TScrollbar",
            background=CARD_HOVER,
            troughcolor=BG_COLOR,
            bordercolor=BG_COLOR,
            arrowcolor=TEXT_COLOR
        )

    # ========================================================
    # 4. MAIN LAYOUT
    # ========================================================

    def create_layout(self):

        # Fixed-width left sidebar.
        self.sidebar = tk.Frame(
            self.root,
            bg=SIDEBAR_COLOR,
            width=245
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Main page area.
        self.main_area = tk.Frame(
            self.root,
            bg=BG_COLOR
        )
        self.main_area.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.create_sidebar()
        self.create_topbar()

        # All page content is rendered inside this frame.
        self.content_frame = tk.Frame(
            self.main_area,
            bg=BG_COLOR
        )
        self.content_frame.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(10, 24)
        )

    # ========================================================
    # 5. SIDEBAR
    # ========================================================

    def create_sidebar(self):

        # Brand section.
        brand_frame = tk.Frame(
            self.sidebar,
            bg=SIDEBAR_COLOR
        )
        brand_frame.pack(fill="x", padx=22, pady=(26, 34))

        logo = tk.Label(
            brand_frame,
            text="M",
            bg=PURPLE,
            fg="white",
            font=("Segoe UI", 19, "bold"),
            width=2,
            height=1
        )
        logo.pack(side="left", padx=(0, 12))

        brand_text = tk.Frame(
            brand_frame,
            bg=SIDEBAR_COLOR
        )
        brand_text.pack(side="left")

        tk.Label(
            brand_text,
            text="MyPOS",
            bg=SIDEBAR_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w")

        tk.Label(
            brand_text,
            text="POINT OF SALE",
            bg=SIDEBAR_COLOR,
            fg=MUTED_COLOR,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(2, 0))

        # Navigation heading.
        tk.Label(
            self.sidebar,
            text="MAIN MENU",
            bg=SIDEBAR_COLOR,
            fg=MUTED_COLOR,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=25, pady=(0, 12))

        # Unicode icons avoid external icon dependencies.
        nav_items = [
            ("Dashboard", "▦", self.show_dashboard),
            ("Products", "▣", self.show_products),
            ("Categories", "▥", self.show_categories),
            ("Billing / Checkout", "🛒", self.show_billing),
            ("Sales History", "▤", self.show_sales_history),
        ]

        for label, icon_text, command in nav_items:
            button = tk.Button(
                self.sidebar,
                text=f"  {icon_text}    {label}",
                command=command,
                anchor="w",
                bg=SIDEBAR_COLOR,
                fg=MUTED_COLOR,
                activebackground=CARD_HOVER,
                activeforeground=TEXT_COLOR,
                font=("Segoe UI", 11),
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=16,
                pady=13,
                highlightthickness=0
            )
            button.pack(fill="x", padx=12, pady=3)

            self.navigation_buttons[label] = button

        # Bottom section.
        bottom_frame = tk.Frame(
            self.sidebar,
            bg=SIDEBAR_COLOR
        )
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=22)

        tk.Frame(
            bottom_frame,
            bg=BORDER_COLOR,
            height=1
        ).pack(fill="x", pady=(0, 12))

        # Logged-in user and Logout button.
        user_row = tk.Frame(bottom_frame, bg=SIDEBAR_COLOR)
        user_row.pack(fill="x", pady=(0, 12))

        tk.Label(
            user_row,
            text=f"\U0001F464  {str(self.current_user['username'])[:12]}",
            bg=SIDEBAR_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        tk.Button(
            user_row,
            text="Logout",
            command=self.logout,
            bg=CARD_HOVER,
            fg=TEXT_COLOR,
            activebackground=DANGER_COLOR,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=4,
            font=("Segoe UI", 9, "bold")
        ).pack(side="right")

        tk.Label(
            bottom_frame,
            text="●  System Ready",
            bg=SIDEBAR_COLOR,
            fg=SUCCESS_COLOR,
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        tk.Label(
            bottom_frame,
            text="MyPOS Desktop Edition",
            bg=SIDEBAR_COLOR,
            fg=MUTED_COLOR,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(8, 0))

    # ========================================================
    # 6. TOP BAR
    # ========================================================

    def create_topbar(self):

        self.topbar = tk.Frame(
            self.main_area,
            bg=BG_COLOR,
            height=85
        )
        self.topbar.pack(fill="x", padx=28, pady=(20, 0))
        self.topbar.pack_propagate(False)

        title_frame = tk.Frame(
            self.topbar,
            bg=BG_COLOR
        )
        title_frame.pack(side="left", fill="y")

        self.page_title = tk.Label(
            title_frame,
            text="Dashboard",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 23, "bold")
        )
        self.page_title.pack(anchor="w")

        self.page_subtitle = tk.Label(
            title_frame,
            text="Overview of your business",
            bg=BG_COLOR,
            fg=MUTED_COLOR,
            font=("Segoe UI", 10)
        )
        self.page_subtitle.pack(anchor="w", pady=(3, 0))

        # Current date.
        date_text = datetime.now().strftime("%d %b %Y")

        tk.Label(
            self.topbar,
            text=f"▦   {date_text}",
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 10),
            padx=15,
            pady=10
        ).pack(side="right", pady=10)

    # ========================================================
    # 7. NAVIGATION HELPERS
    # ========================================================

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def set_active_navigation(self, page_name):

        self.current_page = page_name

        for name, button in self.navigation_buttons.items():

            if name == page_name:
                button.configure(
                    bg="#30264F",
                    fg="#C9BBFF",
                    activebackground="#30264F",
                    activeforeground="#FFFFFF",
                    font=("Segoe UI", 11, "bold")
                )
            else:
                button.configure(
                    bg=SIDEBAR_COLOR,
                    fg=MUTED_COLOR,
                    activebackground=CARD_HOVER,
                    activeforeground=TEXT_COLOR,
                    font=("Segoe UI", 11)
                )

    def prepare_page(self, title, subtitle, navigation_name):

        self.clear_content()
        self.page_title.configure(text=title)
        self.page_subtitle.configure(text=subtitle)
        self.set_active_navigation(navigation_name)

    def logout(self):
        """Close the app screens and show the login window again."""

        if not messagebox.askyesno(
            "Logout",
            "Do you want to log out?",
            parent=self.root
        ):
            return

        root = self.root

        for widget in root.winfo_children():
            widget.destroy()

        root.withdraw()
        user = run_login(root)

        if user is None:
            root.destroy()
            return

        root.deiconify()
        MyPOSApp(root, user)

    # ========================================================
    # 8. DASHBOARD
    # ========================================================

    def show_dashboard(self):

        self.prepare_page(
            "Dashboard",
            "Overview of your business performance",
            "Dashboard"
        )

        # Read existing records without deleting or recreating them.
        try:
            products = [
                dict(row) for row in database.get_all_products()
            ]
            sales = [
                dict(row) for row in database.get_sales_history()
            ]
        except Exception as error:
            messagebox.showerror(
                "Dashboard Error",
                f"Could not load dashboard data.\n\n{error}"
            )
            return

        # Calculate values from the existing database.
        total_products = len(products)

        low_stock_products = [
            product for product in products
            if int(product.get("stock", 0) or 0) <= 5
        ]

        total_sales = sum(
            float(sale.get("total", 0) or 0)
            for sale in sales
        )

        today = datetime.now().date()
        today_sales = 0.0

        for sale in sales:
            created_at = str(sale.get("created_at", ""))

            try:
                sale_date = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).date()

                if sale_date == today:
                    today_sales += float(sale.get("total", 0) or 0)

            except (ValueError, TypeError):
                # Skip dates that cannot be parsed.
                continue

        # ----------------------------------------------------
        # Summary cards
        # ----------------------------------------------------

        cards_frame = tk.Frame(
            self.content_frame,
            bg=BG_COLOR
        )
        cards_frame.pack(fill="x", pady=(5, 22))

        cards_frame.grid_columnconfigure(
            (0, 1, 2, 3),
            weight=1,
            uniform="dashboard_cards"
        )

        self.create_stat_card(
            cards_frame,
            0,
            "TOTAL SALES",
            f"Rs. {total_sales:,.2f}",
            "All recorded sales",
            PURPLE
        )

        self.create_stat_card(
            cards_frame,
            1,
            "TODAY'S SALES",
            f"Rs. {today_sales:,.2f}",
            "Sales recorded today",
            BLUE
        )

        self.create_stat_card(
            cards_frame,
            2,
            "PRODUCTS",
            str(total_products),
            "Products in catalogue",
            SUCCESS_COLOR
        )

        self.create_stat_card(
            cards_frame,
            3,
            "LOW STOCK",
            str(len(low_stock_products)),
            "Stock at 5 or below",
            WARNING_COLOR
        )

        # ----------------------------------------------------
        # Main dashboard panels
        # ----------------------------------------------------

        panels = tk.Frame(
            self.content_frame,
            bg=BG_COLOR
        )
        panels.pack(fill="both", expand=True)

        panels.grid_columnconfigure(0, weight=3)
        panels.grid_columnconfigure(1, weight=2)
        panels.grid_rowconfigure(0, weight=1)

        # Recent sales panel.
        recent_panel = tk.Frame(
            panels,
            bg=CARD_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        recent_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        tk.Label(
            recent_panel,
            text="Recent Sales",
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 12))

        table_frame = tk.Frame(
            recent_panel,
            bg=CARD_COLOR
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 14)
        )

        columns = ("sale_id", "date", "total")

        recent_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10
        )

        recent_table.heading("sale_id", text="Sale ID")
        recent_table.heading("date", text="Date")
        recent_table.heading("total", text="Total (PKR)")

        recent_table.column("sale_id", width=70, anchor="center")
        recent_table.column("date", width=150, anchor="w")
        recent_table.column("total", width=130, anchor="e")

        recent_table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=recent_table.yview
        )
        scrollbar.pack(side="right", fill="y")

        recent_table.configure(
            yscrollcommand=scrollbar.set
        )

        for sale in reversed(sales[-10:]):
            sale_date = str(sale.get("created_at", ""))
            sale_date = sale_date[:16].replace("T", " ")

            recent_table.insert(
                "",
                "end",
                values=(
                    sale.get("id", ""),
                    sale_date,
                    f'{float(sale.get("total", 0) or 0):,.2f}'
                )
            )

        if not sales:
            recent_table.insert(
                "",
                "end",
                values=("-", "No sales yet", "0.00")
            )

        # Low stock panel.
        stock_panel = tk.Frame(
            panels,
            bg=CARD_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        stock_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        tk.Label(
            stock_panel,
            text="Low Stock Alerts",
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 6))

        tk.Label(
            stock_panel,
            text="Products that may need restocking",
            bg=CARD_COLOR,
            fg=MUTED_COLOR,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(0, 12))

        stock_list = tk.Frame(
            stock_panel,
            bg=CARD_COLOR
        )
        stock_list.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        if low_stock_products:
            for product in low_stock_products[:10]:
                item_frame = tk.Frame(
                    stock_list,
                    bg=SIDEBAR_COLOR
                )
                item_frame.pack(fill="x", pady=4)

                tk.Label(
                    item_frame,
                    text=str(product.get("name", "Product")),
                    bg=SIDEBAR_COLOR,
                    fg=TEXT_COLOR,
                    font=("Segoe UI", 10),
                    anchor="w"
                ).pack(
                    side="left",
                    fill="x",
                    expand=True,
                    padx=10,
                    pady=10
                )

                tk.Label(
                    item_frame,
                    text=f'{product.get("stock", 0)} left',
                    bg=SIDEBAR_COLOR,
                    fg=WARNING_COLOR,
                    font=("Segoe UI", 9, "bold")
                ).pack(side="right", padx=10)
        else:
            tk.Label(
                stock_list,
                text="No low-stock products.",
                bg=CARD_COLOR,
                fg=SUCCESS_COLOR,
                font=("Segoe UI", 10)
            ).pack(anchor="w", pady=8)

        # Dashboard refresh button.
        tk.Button(
            self.content_frame,
            text="↻  Refresh Dashboard",
            command=self.show_dashboard,
            bg=PURPLE,
            fg="#FFFFFF",
            activebackground=PURPLE_HOVER,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=16,
            pady=10
        ).pack(anchor="e", pady=(16, 0))

    # ========================================================
    # 9. DASHBOARD SUMMARY CARD
    # ========================================================

    def create_stat_card(
        self,
        parent,
        column,
        title,
        value,
        description,
        accent
    ):

        card = tk.Frame(
            parent,
            bg=CARD_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=5,
            pady=4
        )

        # Small accent bar.
        tk.Frame(
            card,
            bg=accent,
            height=4
        ).pack(fill="x")

        tk.Label(
            card,
            text=title,
            bg=CARD_COLOR,
            fg=MUTED_COLOR,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=14, pady=(15, 8))

        tk.Label(
            card,
            text=value,
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="w", padx=14)

        tk.Label(
            card,
            text=description,
            bg=CARD_COLOR,
            fg=MUTED_COLOR,
            font=("Segoe UI", 9),
            wraplength=180
        ).pack(anchor="w", padx=14, pady=(7, 16))

    # ========================================================
    # 10. EXISTING PRODUCTS PAGE
    # ========================================================

    def show_products(self):

        self.prepare_page(
            "Products",
            "Manage your products, prices and stock",
            "Products"
        )

        create_products_page(self.content_frame)

    # ========================================================
    # 10B. CATEGORIES PAGE (new)
    # ========================================================

    def show_categories(self):

        self.prepare_page(
            "Categories",
            "Manage product categories and their status",
            "Categories"
        )

        create_categories_page(self.content_frame)

    # ========================================================
    # 11. EXISTING BILLING PAGE
    # ========================================================

    def show_billing(self):

        self.prepare_page(
            "Billing / Checkout",
            "Add products to the cart and complete sales",
            "Billing / Checkout"
        )

        create_billing_page(
            self.content_frame,
            self.cart
        )

    # ========================================================
    # 12. EXISTING SALES HISTORY PAGE
    # ========================================================

    def show_sales_history(self):

        self.prepare_page(
            "Sales History",
            "Review previously completed transactions",
            "Sales History"
        )

        create_sales_history_page(self.content_frame)


# ============================================================
# 13. APPLICATION ENTRY POINT
# ============================================================

def main():

    root = tk.Tk()

    # Hide the main window until the login succeeds.
    root.withdraw()

    database.initialize_database()
    initialize_users_table()

    user = run_login(root)

    if user is None:
        # Login window was closed without signing in.
        root.destroy()
        return

    root.deiconify()
    app = MyPOSApp(root, user)

    root.mainloop()


if __name__ == "__main__":
    main()