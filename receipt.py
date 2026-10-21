
import html
import webbrowser

from pathlib import Path
from datetime import datetime


# Receipt files will be saved inside the receipts folder.
BASE_DIR = Path(__file__).resolve().parent
RECEIPTS_DIR = BASE_DIR / "receipts"


def generate_receipt(sale):
    """
    Generate a printable HTML receipt after a successful sale.

    Expected sale data:
    {
        "sale_id": 1,
        "total": 700.0,
        "items": [
            {
                "product_name": "Burger",
                "quantity": 2,
                "unit_price": 350.0,
                "subtotal": 700.0
            }
        ]
    }
    """

    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

    sale_id = sale["sale_id"]
    total = float(sale["total"])
    items = sale["items"]

    receipt_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

    # Build one HTML table row for every purchased product.
    rows = []

    for item in items:
        print("RECEIPT ITEM DATA:", dict(item))
        product_name = html.escape(
            str(item.get("product_name", item.get("name", "Product")))
        )

        quantity = int(item["quantity"])
        unit_price = float(
    item.get("unit_price", item.get("price", 0))
)
        subtotal = float(item["subtotal"])

        rows.append(
            f"""
            <tr>
                <td>{product_name}</td>
                <td>{quantity}</td>
                <td>Rs. {unit_price:,.2f}</td>
                <td>Rs. {subtotal:,.2f}</td>
            </tr>
            """
        )

    items_html = "\n".join(rows)

    receipt_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>MyPOS Receipt #{sale_id}</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                padding: 25px;
                color: #1e293b;
            }}

            .receipt {{
                max-width: 650px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 18px #00000012;
            }}

            h1 {{
                text-align: center;
                margin-bottom: 5px;
            }}

            .subtitle {{
                text-align: center;
                color: #64748b;
            }}

            .details {{
                margin: 25px 0;
                line-height: 1.8;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}

            th, td {{
                padding: 12px 6px;
                text-align: left;
                border-bottom: 1px solid #e2e8f0;
            }}

            th {{
                background: #f8fafc;
            }}

            .total {{
                text-align: right;
                font-size: 22px;
                font-weight: bold;
                margin-top: 25px;
            }}

            .thank-you {{
                text-align: center;
                margin-top: 35px;
                color: #64748b;
            }}

            .print-button {{
                display: block;
                margin: 25px auto 0;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                background: #2563eb;
                color: white;
                cursor: pointer;
                font-size: 16px;
            }}

            @media print {{
                body {{
                    background: white;
                    padding: 0;
                }}

                .receipt {{
                    box-shadow: none;
                    max-width: 100%;
                    padding: 10px;
                }}

                .print-button {{
                    display: none;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="receipt">
            <h1>MyPOS</h1>
            <p class="subtitle">Point of Sale Receipt</p>

            <div class="details">
                <strong>Sale ID:</strong> {sale_id}<br>
                <strong>Date & Time:</strong> {receipt_time}<br>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Qty</th>
                        <th>Price</th>
                        <th>Subtotal</th>
                    </tr>
                </thead>

                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div class="total">
                Total: Rs. {total:,.2f}
            </div>

            <p class="thank-you">
                Thank you for shopping with us!
            </p>

            <button class="print-button" onclick="window.print()">
                Print Receipt
            </button>
        </div>
    </body>
    </html>
    """

    receipt_path = RECEIPTS_DIR / f"receipt_{sale_id}.html"

    receipt_path.write_text(receipt_html, encoding="utf-8")

    # Open the saved receipt in the default browser.
    webbrowser.open(receipt_path.resolve().as_uri())

    return receipt_path
