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

    -- Users
    INSERT OR IGNORE INTO users VALUES (1, 'Arjun Sharma', 'arjun.sharma@gmail.com');
    INSERT OR IGNORE INTO users VALUES (2, 'Priya Patel', 'priya.patel@gmail.com');
    INSERT OR IGNORE INTO users VALUES (3, 'Rahul Verma', 'rahul.verma@gmail.com');
    INSERT OR IGNORE INTO users VALUES (4, 'Sneha Iyer', 'sneha.iyer@gmail.com');
    INSERT OR IGNORE INTO users VALUES (5, 'Vikram Nair', 'vikram.nair@gmail.com');
    INSERT OR IGNORE INTO users VALUES (6, 'Ananya Bose', 'ananya.bose@gmail.com');
    INSERT OR IGNORE INTO users VALUES (7, 'Karan Mehta', 'karan.mehta@gmail.com');
    INSERT OR IGNORE INTO users VALUES (8, 'Divya Reddy', 'divya.reddy@gmail.com');
    INSERT OR IGNORE INTO users VALUES (9, 'Rohan Gupta', 'rohan.gupta@gmail.com');
    INSERT OR IGNORE INTO users VALUES (10, 'Meera Joshi', 'meera.joshi@gmail.com');
    INSERT OR IGNORE INTO users VALUES (11, 'Aditya Singh', 'aditya.singh@gmail.com');
    INSERT OR IGNORE INTO users VALUES (12, 'Kavya Menon', 'kavya.menon@gmail.com');

    -- Products
    INSERT OR IGNORE INTO products VALUES (1,  'Laptop',           55000,  'Electronics');
    INSERT OR IGNORE INTO products VALUES (2,  'Notebook',         120,    'Stationery');
    INSERT OR IGNORE INTO products VALUES (3,  'Wireless Mouse',   850,    'Electronics');
    INSERT OR IGNORE INTO products VALUES (4,  'Mechanical Keyboard', 3200, 'Electronics');
    INSERT OR IGNORE INTO products VALUES (5,  'Desk Lamp',        650,    'Furniture');
    INSERT OR IGNORE INTO products VALUES (6,  'Ballpoint Pens',   80,     'Stationery');
    INSERT OR IGNORE INTO products VALUES (7,  'USB-C Hub',        1200,   'Electronics');
    INSERT OR IGNORE INTO products VALUES (8,  'Office Chair',     12000,  'Furniture');
    INSERT OR IGNORE INTO products VALUES (9,  'Monitor 24"',      18000,  'Electronics');
    INSERT OR IGNORE INTO products VALUES (10, 'Whiteboard',       2500,   'Stationery');
    INSERT OR IGNORE INTO products VALUES (11, 'Webcam HD',        3500,   'Electronics');
    INSERT OR IGNORE INTO products VALUES (12, 'Headphones',       4800,   'Electronics');
    INSERT OR IGNORE INTO products VALUES (13, 'Sticky Notes',     60,     'Stationery');
    INSERT OR IGNORE INTO products VALUES (14, 'Standing Desk',    22000,  'Furniture');
    INSERT OR IGNORE INTO products VALUES (15, 'Laptop Stand',     900,    'Furniture');

    -- Orders
    INSERT OR IGNORE INTO orders VALUES (1,  1,  1,  55000,  'delivered');
    INSERT OR IGNORE INTO orders VALUES (2,  2,  3,  850,    'delivered');
    INSERT OR IGNORE INTO orders VALUES (3,  3,  9,  18000,  'pending');
    INSERT OR IGNORE INTO orders VALUES (4,  4,  2,  120,    'delivered');
    INSERT OR IGNORE INTO orders VALUES (5,  5,  8,  12000,  'shipped');
    INSERT OR IGNORE INTO orders VALUES (6,  6,  4,  3200,   'delivered');
    INSERT OR IGNORE INTO orders VALUES (7,  7,  12, 4800,   'pending');
    INSERT OR IGNORE INTO orders VALUES (8,  8,  7,  1200,   'shipped');
    INSERT OR IGNORE INTO orders VALUES (9,  9,  5,  650,    'delivered');
    INSERT OR IGNORE INTO orders VALUES (10, 10, 11, 3500,   'pending');
    INSERT OR IGNORE INTO orders VALUES (11, 11, 14, 22000,  'shipped');
    INSERT OR IGNORE INTO orders VALUES (12, 12, 15, 900,    'delivered');
    INSERT OR IGNORE INTO orders VALUES (13, 1,  3,  850,    'delivered');
    INSERT OR IGNORE INTO orders VALUES (14, 2,  12, 4800,   'shipped');
    INSERT OR IGNORE INTO orders VALUES (15, 3,  6,  80,     'delivered');
    INSERT OR IGNORE INTO orders VALUES (16, 4,  10, 2500,   'pending');
    INSERT OR IGNORE INTO orders VALUES (17, 5,  4,  3200,   'delivered');
    INSERT OR IGNORE INTO orders VALUES (18, 6,  1,  55000,  'pending');
    INSERT OR IGNORE INTO orders VALUES (19, 7,  9,  18000,  'shipped');
    INSERT OR IGNORE INTO orders VALUES (20, 8,  15, 900,    'delivered');
    INSERT OR IGNORE INTO orders VALUES (21, 9,  13, 60,     'delivered');
    INSERT OR IGNORE INTO orders VALUES (22, 10, 8,  12000,  'shipped');
    INSERT OR IGNORE INTO orders VALUES (23, 11, 7,  1200,   'delivered');
    INSERT OR IGNORE INTO orders VALUES (24, 12, 2,  120,    'pending');
    INSERT OR IGNORE INTO orders VALUES (25, 1,  14, 22000,  'shipped');
    INSERT OR IGNORE INTO orders VALUES (26, 3,  11, 3500,   'delivered');
    INSERT OR IGNORE INTO orders VALUES (27, 5,  13, 60,     'delivered');
    INSERT OR IGNORE INTO orders VALUES (28, 7,  10, 2500,   'shipped');
    INSERT OR IGNORE INTO orders VALUES (29, 9,  4,  3200,   'pending');
    INSERT OR IGNORE INTO orders VALUES (30, 11, 3,  850,    'delivered');
""")

conn.commit()
conn.close()
print(f"legacy.db created at: {DB_PATH}")