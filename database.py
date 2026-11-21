import sqlite3
from datetime import datetime, timedelta
from config import DB_NAME


def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def generate_order_number(c: sqlite3.Cursor) -> str:
    """
    Generate a unique formatted order number.
    Format: DMJ + hour + minute + second + year + day + month + sum(HH+MM+SS)
    """
    offset = 0
    while True:
        generated_time = datetime.now() + timedelta(seconds=offset)
        time_sum = generated_time.hour + generated_time.minute + generated_time.second
        order_number = (
            "DMJ"
            + generated_time.strftime("%H%M%S%Y%d%m")
            + str(time_sum)
        )
        c.execute("SELECT 1 FROM orders WHERE order_number = ?", (order_number,))
        if not c.fetchone():
            return order_number
        offset += 1


def get_internal_order_id(c: sqlite3.Cursor, order_ref) -> int | None:
    """Resolve a formatted order number or legacy numeric ID to internal orders.id."""
    c.execute("SELECT id FROM orders WHERE order_number = ?", (str(order_ref),))
    row = c.fetchone()
    if row:
        return row[0]

    if str(order_ref).isdigit():
        c.execute("SELECT id FROM orders WHERE id = ?", (int(order_ref),))
        row = c.fetchone()
        if row:
            return row[0]

    return None


def get_order_number(c: sqlite3.Cursor, internal_order_id: int) -> str:
    """Return the formatted order number for an internal database ID."""
    c.execute("SELECT order_number FROM orders WHERE id = ?", (internal_order_id,))
    row = c.fetchone()
    if row and row[0]:
        return row[0]
    return str(internal_order_id)


def init_db(db_path: str | None = None) -> None:
    """Non-destructive database initialization and legacy schema migration."""
    conn = get_db_connection(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location_id INTEGER,
            FOREIGN KEY(location_id) REFERENCES locations(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            photo TEXT,
            shop_id INTEGER,
            is_out_of_stock INTEGER DEFAULT 0,
            FOREIGN KEY(shop_id) REFERENCES shops(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            mobile TEXT,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            order_number TEXT UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    """)

    # Non-destructive migrations for older databases
    for alter_sql in (
        "ALTER TABLE items ADD COLUMN is_out_of_stock INTEGER DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'Pending'",
        "ALTER TABLE orders ADD COLUMN order_number TEXT",
    ):
        try:
            c.execute(alter_sql)
        except sqlite3.OperationalError:
            pass

    # Backfill formatted order numbers for legacy orders
    c.execute("""
        SELECT id FROM orders
        WHERE order_number IS NULL OR order_number = ''
        ORDER BY id
    """)
    for (internal_order_id,) in c.fetchall():
        order_number = generate_order_number(c)
        c.execute(
            "UPDATE orders SET order_number = ? WHERE id = ?",
            (order_number, internal_order_id),
        )

    conn.commit()
    conn.close()
