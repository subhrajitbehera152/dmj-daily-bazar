from database import get_db_connection


def get_all_locations(db_path: str | None = None) -> list[tuple]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name FROM locations")
    rows = c.fetchall()
    conn.close()
    return rows


def add_location(name: str, db_path: str | None = None) -> bool:
    name = (name or "").strip()
    if not name:
        return False
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO locations (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return True


def delete_location(location_id: int, db_path: str | None = None) -> None:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute(
        "DELETE FROM items WHERE shop_id IN (SELECT id FROM shops WHERE location_id = ?)",
        (location_id,),
    )
    c.execute("DELETE FROM shops WHERE location_id = ?", (location_id,))
    c.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    conn.commit()
    conn.close()


def get_all_shops(db_path: str | None = None) -> list[tuple]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name, location_id FROM shops")
    rows = c.fetchall()
    conn.close()
    return rows


def add_shop(name: str, location_id: int, db_path: str | None = None) -> bool:
    name = (name or "").strip()
    if not name or location_id is None:
        return False
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO shops (name, location_id) VALUES (?, ?)", (name, int(location_id)))
    conn.commit()
    conn.close()
    return True


def delete_shop(shop_id: int, db_path: str | None = None) -> None:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE shop_id = ?", (shop_id,))
    c.execute("DELETE FROM shops WHERE id = ?", (shop_id,))
    conn.commit()
    conn.close()


def get_items_by_location(loc_id: int, search_query: str = "", db_path: str | None = None) -> dict[str, list[tuple]]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT
            items.id,
            items.name,
            items.category,
            items.price,
            items.photo,
            items.is_out_of_stock
        FROM items
        LEFT JOIN shops ON items.shop_id = shops.id
        WHERE shops.location_id = ?
    """, (loc_id,))
    items = c.fetchall()
    conn.close()

    q = (search_query or "").strip().lower()
    if q:
        items = [
            item for item in items
            if q in (item[1] or "").lower() or q in (item[2] or "").lower()
        ]

    categories: dict[str, list[tuple]] = {}
    for item in items:
        cat = item[2]
        categories.setdefault(cat, []).append(item)
    return categories


def get_all_admin_items(db_path: str | None = None) -> list[tuple]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT
            items.id,
            items.name,
            items.category,
            items.price,
            items.photo,
            shops.name,
            locations.name,
            items.is_out_of_stock
        FROM items
        LEFT JOIN shops ON items.shop_id = shops.id
        LEFT JOIN locations ON shops.location_id = locations.id
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_item_by_id(item_id: int, db_path: str | None = None) -> tuple | None:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT id, name, category, price, photo, shop_id, is_out_of_stock FROM items WHERE id = ?",
        (item_id,),
    )
    row = c.fetchone()
    conn.close()
    return row


def add_item(
    name: str,
    category: str,
    price: float,
    photo: str,
    shop_id: int,
    is_out_of_stock: bool = False,
    db_path: str | None = None,
) -> bool:
    name = (name or "").strip()
    category = (category or "").strip()
    photo = (photo or "").strip()
    if not name or not category or shop_id is None:
        return False
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        INSERT INTO items (name, category, price, photo, shop_id, is_out_of_stock)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, category, float(price), photo, int(shop_id), 1 if is_out_of_stock else 0))
    conn.commit()
    conn.close()
    return True


def update_item(
    item_id: int,
    name: str,
    category: str,
    price: float,
    photo: str,
    shop_id: int,
    is_out_of_stock: bool,
    db_path: str | None = None,
) -> tuple[bool, str | None]:
    name = (name or "").strip()
    category = (category or "").strip()
    photo = (photo or "").strip()

    try:
        price_val = float(price)
        shop_id_val = int(shop_id)
    except (TypeError, ValueError):
        return False, "Enter a valid price and shop."

    if not name or not category or price_val < 0:
        return False, "Name and category are required; price cannot be negative."

    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    if not c.fetchone():
        conn.close()
        return False, "Item not found."

    c.execute("""
        UPDATE items
        SET name = ?, category = ?, price = ?, photo = ?, shop_id = ?, is_out_of_stock = ?
        WHERE id = ?
    """, (name, category, price_val, photo, shop_id_val, 1 if is_out_of_stock else 0, item_id))
    conn.commit()
    conn.close()
    return True, None


def toggle_item_stock(item_id: int, db_path: str | None = None) -> None:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        UPDATE items
        SET is_out_of_stock = CASE WHEN is_out_of_stock = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (item_id,))
    conn.commit()
    conn.close()


def delete_item(item_id: int, db_path: str | None = None) -> None:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
