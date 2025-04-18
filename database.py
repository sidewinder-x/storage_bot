
import os
import sqlite3
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        balance INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        quantity INTEGER,
        buy_price INTEGER,
        sell_price INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER,
        date TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        amount INTEGER,
        date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS family_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        status TEXT,
        date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER,
        price INTEGER,
        status TEXT DEFAULT 'waiting',
        assigned_to INTEGER,
        created_at TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(assigned_to) REFERENCES users(id)
    )
    """)
    # Обновление существующей таблицы orders, если колонок ещё нет
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN finished_at TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN payout INTEGER DEFAULT 0")
    except:
        pass
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN paid_to_courier INTEGER DEFAULT 0")
    except:
        pass
    try:
        cur.execute("ALTER TABLE products ADD COLUMN photo TEXT")
    except:
        pass

    conn.commit()
    conn.close()



def get_db():
    db_path = os.path.abspath("bot_data.db")
    print(f"📦 Используется база данных: {db_path}")
    return sqlite3.connect(db_path)