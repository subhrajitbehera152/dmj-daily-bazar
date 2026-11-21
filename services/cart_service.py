from database import get_db_connection
from config import FREE_DELIVERY_THRESHOLD, DELIVERY_FEE


def calculate_delivery_fee(subtotal: float) -> float:
    """Customer delivery fee rule: ₹30 if 0 < subtotal < 199, else ₹0."""
    return DELIVERY_FEE if 0 < subtotal < FREE_DELIVERY_THRESHOLD else 0.0


def update_cart_item(cart: dict, item_id: int, action: str, db_path: str | None = None) -> dict:
    """
    Mirrors original /update_cart/<item_id>/<action>.
    Supports 'add', 'remove' (decrement by 1), and 'delete' (remove item completely).
    """
    if cart is None or not isinstance(cart, dict):
        cart = {}

    key = str(item_id)
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name, price, is_out_of_stock FROM items WHERE id = ?", (item_id,))
    item = c.fetchone()
    conn.close()

    if not item:
        return {"ok": False, "status_code": 404, "error": "Item not found", "item_id": item_id, "cart": cart}

    if action == "add":
        if item[3]:
            qty = int(cart.get(key, 0))
            return {
                "ok": False,
                "status_code": 409,
                "error": "Out of Stock",
                "item_id": item_id,
                "qty": qty,
                "subtotal": round(qty * item[2], 2),
                "out_of_stock": True,
                "cart": cart,
            }
        cart[key] = int(cart.get(key, 0)) + 1
    elif action == "remove":
        if key in cart:
            cart[key] = int(cart[key]) - 1
            if cart[key] <= 0:
                del cart[key]
    elif action == "delete":
        cart.pop(key, None)
    else:
        return {"ok": False, "status_code": 400, "error": "Invalid cart action", "cart": cart}

    qty = int(cart.get(key, 0))
    return {
        "ok": True,
        "status_code": 200,
        "item_id": item_id,
        "qty": qty,
        "subtotal": round(qty * item[2], 2),
        "out_of_stock": bool(item[3]),
        "cart": cart,
    }


def get_cart_details(cart: dict, db_path: str | None = None) -> dict:
    """
    Resolves cart dictionary {item_id_str: qty} against the database.
    Returns items list (including photo URL), total_qty, subtotal, delivery_fee, payable_total.
    """
    if not isinstance(cart, dict):
        cart = {}

    conn = get_db_connection(db_path)
    c = conn.cursor()

    items = []
    subtotal = 0.0
    total_qty = 0

    for item_id_str, qty in list(cart.items()):
        try:
            item_id = int(item_id_str)
            qty_int = int(qty)
        except (TypeError, ValueError):
            continue

        if qty_int <= 0:
            continue

        c.execute(
            "SELECT id, name, price, is_out_of_stock, photo, category FROM items WHERE id = ?",
            (item_id,),
        )
        row = c.fetchone()
        if row:
            line_total = round(float(row[2]) * qty_int, 2)
            items.append({
                "id": row[0],
                "name": row[1],
                "price": float(row[2]),
                "qty": qty_int,
                "subtotal": line_total,
                "is_out_of_stock": bool(row[3]),
                "photo": row[4] or "",
                "category": row[5] or "",
            })
            subtotal += line_total
            total_qty += qty_int

    conn.close()

    subtotal = round(subtotal, 2)
    delivery_fee = calculate_delivery_fee(subtotal)
    payable_total = round(subtotal + delivery_fee, 2)

    return {
        "items": items,
        "total_qty": total_qty,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "payable_total": payable_total,
    }
