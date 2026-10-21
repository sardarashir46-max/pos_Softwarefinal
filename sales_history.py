
# ============================================================
# MyPOS - Sales History
# File: sales_history.py
# Purpose: View completed sales and their individual items
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

import database


def create_sales_history_page(parent):
    """Build the sales history and sale details screen."""

    page = ttk.Frame(parent, padding=16)
    page.pack(fill="both", expand=True)

    # -------------------- Heading --------------------
    ttk.Label(
        page,
        text="Sales History",
        font=("Segoe UI", 20, "bold")
    ).pack(anchor="w")

    ttk.Label(
        page,
        text="Select a completed sale to view its details."
    ).pack(anchor="w", pady=(4, 12))

    # -------------------- Main Layout --------------------
    content = ttk.Panedwindow(page, orient="vertical")
    content.pack(fill="both", expand=True)

    sales_frame = ttk.LabelFrame(
        content, text="Completed Sales", padding=8
    )
    details_frame = ttk.LabelFrame(
        content, text="Selected Sale Details", padding=8
    )

    content.add(sales_frame, weight=3)
    content.add(details_frame, weight=2)

    # -------------------- Sales Table --------------------
    sales_columns = ("id", "date", "total")

    sales_table = ttk.Treeview(
        sales_frame,
        columns=sales_columns,
        show="headings",
        selectmode="browse"
    )

    sales_table.heading("id", text="Sale ID")
    sales_table.heading("date", text="Date / Time")
    sales_table.heading("total", text="Total (PKR)")

    sales_table.column("id", width=80, anchor="center")
    sales_table.column("date", width=220)
    sales_table.column("total", width=150, anchor="e")

    sales_scroll = ttk.Scrollbar(
        sales_frame,
        orient="vertical",
        command=sales_table.yview
    )
    sales_table.configure(yscrollcommand=sales_scroll.set)

    sales_table.pack(side="left", fill="both", expand=True)
    sales_scroll.pack(side="right", fill="y")

    # -------------------- Sale Items Table --------------------
    item_columns = ("name", "quantity", "price", "subtotal")

    items_table = ttk.Treeview(
        details_frame,
        columns=item_columns,
        show="headings",
        selectmode="browse"
    )

    items_table.heading("name", text="Product")
    items_table.heading("quantity", text="Quantity")
    items_table.heading("price", text="Unit Price")
    items_table.heading("subtotal", text="Subtotal")

    items_table.column("name", width=220)
    items_table.column("quantity", width=90, anchor="center")
    items_table.column("price", width=110, anchor="e")
    items_table.column("subtotal", width=120, anchor="e")

    items_scroll = ttk.Scrollbar(
        details_frame,
        orient="vertical",
        command=items_table.yview
    )
    items_table.configure(yscrollcommand=items_scroll.set)

    items_table.pack(side="left", fill="both", expand=True)
    items_scroll.pack(side="right", fill="y")

    selected_total = tk.StringVar(value="Select a sale to view its items.")

    ttk.Label(
        details_frame,
        textvariable=selected_total,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", pady=(8, 0))

    # -------------------- Load Sales --------------------
    def refresh_sales():
        """Reload the list of completed sales."""

        for row in sales_table.get_children():
            sales_table.delete(row)

        for row in items_table.get_children():
            items_table.delete(row)

        selected_total.set("Select a sale to view its items.")

        try:
            sales = database.get_sales_history()

            for sale in sales:
                sales_table.insert("", "end", values=(
                    sale["id"],
                    sale["created_at"],
                    f'{sale["total"]:,.2f}'
                ))

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load sales history:\n{error}"
            )

    # -------------------- Load Sale Details --------------------
    def show_sale_details(event=None):
        """Use the selected sale ID to retrieve its items."""

        selection = sales_table.selection()

        if not selection:
            return

        values = sales_table.item(selection[0], "values")
        sale_id = int(values[0])

        for row in items_table.get_children():
            items_table.delete(row)

        try:
            items = database.get_sale_items(sale_id)

            for item in items:
                items_table.insert("", "end", values=(
                    item["product_name"],
                    item["quantity"],
                    f'{item["unit_price"]:,.2f}',
                    f'{item["subtotal"]:,.2f}'
                ))

            selected_total.set(
                f"Sale #{sale_id} — Total: PKR {float(values[2]):,.2f}"
            )

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load sale details:\n{error}"
            )

    sales_table.bind("<<TreeviewSelect>>", show_sale_details)

    # -------------------- Refresh Button --------------------
    ttk.Button(
        page,
        text="Refresh Sales",
        command=refresh_sales
    ).pack(anchor="e", pady=(10, 0))

    refresh_sales()
    return page
