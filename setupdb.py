"""
Run this ONCE to create the fake legacy database.
    uv run setup_db.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "legacy.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL,
        category TEXT
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        amount REAL,
        status TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    INSERT OR IGNORE INTO users VALUES (1, 'Madhav', 'madhav@gmail.com');
    INSERT OR IGNORE INTO users VALUES (2, 'Ram', 'ram@gmail.com');

    INSERT OR IGNORE INTO products VALUES (1, 'Laptop', 55000, 'Electronics');
    INSERT OR IGNORE INTO products VALUES (2, 'Notebook', 120, 'Stationery');

    INSERT OR IGNORE INTO orders VALUES (1, 1, 1, 55000, 'delivered');
    INSERT OR IGNORE INTO orders VALUES (2, 2, 2, 120, 'pending');
    INSERT OR IGNORE INTO orders VALUES (3, 1, 2, 120, 'pending');
""")

conn.commit()
conn.close()
print(f"legacy.db created at: {DB_PATH}")