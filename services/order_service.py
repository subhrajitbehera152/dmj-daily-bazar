from datetime import datetime
from database import get_db_connection, generate_order_number, get_internal_order_id
from config import VALID_ORDER_STATUSES, FREE_DELIVERY_THRESHOLD, DELIVERY_FEE


def place_order(
    cart: dict,
    customer_name: str,
    house_landmark: str,
    customer_address: str,
    mobile: str,
    db_path: str | None = None,
) -> tuple[bool, str]:
    """
    Validates cart and stock, creates order + order_items in a transaction.
    Returns (True, order_number) on success or (False, error_message) on failure.
    """
    customer_name = (customer_name or "").strip()
    customer_address = (customer_address or "").strip()
    house_landmark = (house_landmark or "").strip()
    mobile = (mobile or "").strip()

    full_address = ", ".join(part for part in (house_landmark, customer_address) if part)

    if not isinstance(cart, dict) or not cart:
        return False, "Your cart is empty."
    if not customer_name or not customer_address or not house_landmark:
        return False, "Name, Flat/House/Landmark, and Street Address are required."

    conn = get_db_connection(db_path)
    c = conn.cursor()

    try:
        validated_items = []
        for item_id_str, qty in cart.items():
            try:
                item_id = int(item_id_str)
                quantity = int(qty)
            except (TypeError, ValueError):
                return False, "Invalid item or quantity in cart."

            if quantity <= 0:
                return False, "Item quantity must be greater than zero."

            c.execute("SELECT id, name, is_out_of_stock FROM items WHERE id = ?", (item_id,))
            stock_row = c.fetchone()
            if not stock_row:
                return False, f"Item #{item_id} is no longer available."
            if stock_row[2]:
                return False, f"'{stock_row[1]}' is currently out of stock."

            validated_items.append((item_id, quantity))

        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_number = generate_order_number(c)

        c.execute("""
            INSERT INTO orders (customer_name, customer_address, mobile, date, status, order_number)
            VALUES (?, ?, ?, ?, 'Pending', ?)
        """, (customer_name, full_address, mobile, order_date, order_number))

        internal_order_id = c.lastrowid
        for item_id, quantity in validated_items:
            c.execute(
                "INSERT INTO order_items (order_id, item_id, quantity) VALUES (?, ?, ?)",
                (internal_order_id, item_id, quantity),
            )

        conn.commit()
        return True, order_number
    except Exception as exc:
        conn.rollback()
        return False, f"Order failed: {exc}"
    finally:
        conn.close()


def get_tracking_order(order_ref: str, db_path: str | None = None) -> tuple[dict | None, list[dict]]:
    """Mirrors original /track/<order_id>."""
    conn = get_db_connection(db_path)
    c = conn.cursor()
    internal_order_id = get_internal_order_id(c, order_ref)
    if internal_order_id is None:
        conn.close()
        return None, []

    c.execute("""
        SELECT id, customer_name, customer_address, mobile, date,
               COALESCE(status, 'Pending'), order_number
        FROM orders WHERE id = ?
    """, (internal_order_id,))
    order_row = c.fetchone()
    if not order_row:
        conn.close()
        return None, []

    formatted_order_number = order_row[6] or str(order_row[0])

    c.execute("""
        SELECT
            COALESCE(items.name, 'Deleted item'),
            order_items.quantity,
            COALESCE(items.price, 0),
            COALESCE(order_items.quantity * items.price, 0)
        FROM order_items
        LEFT JOIN items ON order_items.item_id = items.id
        WHERE order_items.order_id = ?
        ORDER BY order_items.id
    """, (internal_order_id,))
    item_rows = c.fetchall()
    conn.close()

    items = [
        {"name": r[0], "quantity": r[1], "price": float(r[2]), "subtotal": float(r[3])}
        for r in item_rows
    ]
    subtotal = sum(i["subtotal"] or 0.0 for i in items)
    delivery_fee = DELIVERY_FEE if 0 < subtotal < FREE_DELIVERY_THRESHOLD else 0.0
    total = subtotal + delivery_fee

    status = order_row[5]
    status_map = {
        "Pending": "Order Placed",
        "In Progress": "Preparing",
        "On the way": "On the way",
        "Completed": "Delivered",
    }
    display_status = status_map.get(status, status)

    order = {
        "id": formatted_order_number,
        "order_number": formatted_order_number,
        "name": order_row[1],
        "house_landmark": "",
        "address": order_row[2],
        "mobile": order_row[3],
        "date": order_row[4],
        "status": display_status,
        "raw_status": status,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "payment_method": "Not specified",
    }
    return order, items


def get_all_admin_orders(db_path: str | None = None) -> list[tuple]:
    """Mirrors original /admin/orders."""
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT
            COALESCE(orders.order_number, CAST(orders.id AS TEXT)),
            orders.date,
            orders.customer_name,
            orders.customer_address,
            orders.mobile,
            COALESCE(orders.status, 'Pending'),
            COUNT(order_items.id) AS item_count,
            COALESCE(SUM(order_items.quantity * items.price), 0) AS total
        FROM orders
        LEFT JOIN order_items ON orders.id = order_items.order_id
        LEFT JOIN items ON order_items.item_id = items.id
        GROUP BY orders.id
        ORDER BY orders.date DESC, orders.id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_admin_order_details(order_ref: str, db_path: str | None = None) -> tuple[tuple | None, list[tuple]]:
    """Mirrors original /admin/order/<order_id>."""
    conn = get_db_connection(db_path)
    c = conn.cursor()
    internal_order_id = get_internal_order_id(c, order_ref)
    if internal_order_id is None:
        conn.close()
        return None, []

    c.execute("""
        SELECT
            COALESCE(order_number, CAST(id AS TEXT)),
            customer_name,
            customer_address,
            mobile,
            date,
            COALESCE(status, 'Pending')
        FROM orders WHERE id = ?
    """, (internal_order_id,))
    order = c.fetchone()
    if not order:
        conn.close()
        return None, []

    c.execute("""
        SELECT
            COALESCE(items.name, 'Deleted item'),
            order_items.quantity,
            COALESCE(items.price, 0),
            COALESCE(order_items.quantity * items.price, 0) AS subtotal
        FROM order_items
        LEFT JOIN items ON order_items.item_id = items.id
        WHERE order_items.order_id = ?
        ORDER BY order_items.id
    """, (internal_order_id,))
    items = c.fetchall()
    conn.close()
    return order, items


def update_order_status(order_ref: str, status: str, db_path: str | None = None) -> tuple[bool, str]:
    status = (status or "").strip()
    if status not in VALID_ORDER_STATUSES:
        return False, "Invalid order status"

    conn = get_db_connection(db_path)
    c = conn.cursor()
    internal_order_id = get_internal_order_id(c, order_ref)
    if internal_order_id is None:
        conn.close()
        return False, "Order not found"

    c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, internal_order_id))
    updated = c.rowcount
    conn.commit()
    conn.close()
    if not updated:
        return False, "Order not found"
    return True, "Status updated"


def delete_order(order_ref: str, db_path: str | None = None) -> tuple[bool, str]:
    conn = get_db_connection(db_path)
    try:
        conn.execute("BEGIN")
        c = conn.cursor()
        internal_order_id = get_internal_order_id(c, order_ref)
        if internal_order_id is None:
            conn.rollback()
            return False, "Order not found"

        c.execute("DELETE FROM order_items WHERE order_id = ?", (internal_order_id,))
        c.execute("DELETE FROM orders WHERE id = ?", (internal_order_id,))
        conn.commit()
        return True, "Order deleted"
    except Exception as exc:
        conn.rollback()
        return False, f"Delete failed: {exc}"
    finally:
        conn.close()


def generate_order_pdf_bytes(
    order: tuple,
    items: list[tuple],
    oos_indices: set[int],
    summary: dict,
) -> bytes:
    """Generate a clean downloadable PDF invoice compatible with both fpdf2 and fpdf."""
    from fpdf import FPDF

    def _safe(text) -> str:
        return str(text or "").encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, _safe(f"DMJ Daily Bazar - Order #{order[0]}"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe(f"Status: {order[5]}   |   Date: {order[4]}"), ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Customer Information", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _safe(f"Name: {order[1]}"), ln=True)
    pdf.cell(0, 6, _safe(f"Mobile: {order[3] or 'Not provided'}"), ln=True)
    pdf.multi_cell(0, 6, _safe(f"Address: {order[2]}"))
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(85, 8, "Product", border=1)
    pdf.cell(20, 8, "Qty", border=1, align="C")
    pdf.cell(35, 8, "Unit Price", border=1, align="R")
    pdf.cell(45, 8, "Subtotal", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    for idx, item in enumerate(items):
        is_oos = idx in oos_indices
        name = f"{item[0]} [OUT OF STOCK]" if is_oos else str(item[0])
        pdf.cell(85, 8, _safe(name[:42]), border=1)
        pdf.cell(20, 8, str(item[1]), border=1, align="C")
        pdf.cell(35, 8, f"Rs.{float(item[2] or 0):.2f}", border=1, align="R")
        pdf.cell(45, 8, f"Rs.{float(item[3] or 0):.2f}", border=1, align="R", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Original Items Subtotal: Rs.{summary['original_subtotal']:.2f}", ln=True, align="R")
    pdf.cell(0, 6, f"Out-of-Stock Deduction: Rs.{summary['deduction']:.2f}", ln=True, align="R")
    pdf.cell(0, 6, f"Adjusted Items Subtotal: Rs.{summary['adjusted_subtotal']:.2f}", ln=True, align="R")
    fee_str = "Free" if summary["delivery_fee"] == 0 else f"Rs.{summary['delivery_fee']:.2f}"
    pdf.cell(0, 6, f"Delivery Fee: {fee_str}", ln=True, align="R")
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, f"Adjusted Grand Total: Rs.{summary['grand_total']:.2f}", ln=True, align="R")

    out = pdf.output(dest="S")
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("latin-1")
