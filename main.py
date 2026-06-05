"""
Zero-Knowledge MCP Server
=========================
DB path is read from environment variable DB_PATH.
Set it in claude_desktop_config.json under "env".

What this file does, in order:
    1. Read DB_PATH from environment variable
    2. Scan the DB — discover all tables, columns, foreign keys
    3. Build a context prompt from the schema (for Claude's brain)
    4. Generate CRUD tools in memory for every table found
    5. Start MCP server — Claude Desktop connects and uses the tools

Zero-Knowledge means: Claude only calls tool names + passes parameters.
Claude never writes or sees any SQL. All SQL lives here, parameterized.
"""

import os
import json
import sqlite3
from mcp.server.fastmcp import FastMCP


# ──────────────────────────────────────────────
# STEP 1: Read DB path from environment variable
#
# Set in claude_desktop_config.json like:
#   "env": { "DB_PATH": "C:\\path\\to\\legacy.db" }
#
# Falls back to legacy.db in same folder if env not set
# (useful for running locally during development)
# ──────────────────────────────────────────────

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "legacy.db")  # fallback
)



if not os.path.exists(DB_PATH):

    raise SystemExit(1)


# ──────────────────────────────────────────────
# STEP 2: Scan the DB
#
# Uses sqlite3 PRAGMA commands to discover:
#   - All table names
#   - All columns per table
#   - All foreign key relationships
#
# Returns a dict like:
# {
#   "users":  { "columns": ["id","name","email"], "foreign_keys": [] },
#   "orders": { "columns": ["id","user_id",...],
#               "foreign_keys": [{"from_col":"user_id","to_table":"users","to_col":"id"}] }
# }
# ──────────────────────────────────────────────

def scan_db(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]

    schema = {}
    for table in tables:
        cur.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in cur.fetchall()]

        cur.execute(f"PRAGMA foreign_key_list({table});")
        fks = []
        for fk in cur.fetchall():
            fks.append({
                "from_col": fk[3],
                "to_table": fk[2],
                "to_col":   fk[4],
            })

        schema[table] = {"columns": columns, "foreign_keys": fks}

    conn.close()
    return schema


# ──────────────────────────────────────────────
# STEP 3: Build context prompt from schema
#
# This string is passed to Claude as system instructions.
# It tells Claude what tables exist, what columns they have,
# and how tables relate via foreign keys.
#
# WITHOUT this, Claude would see tool names like get_orders
# but have no idea that orders.user_id connects to users.id
# ──────────────────────────────────────────────

def build_prompt(schema: dict) -> str:
    lines = ["You have access to a database with these tables:\n"]

    for table, info in schema.items():
        cols = ", ".join(info["columns"])
        lines.append(f"  - {table} (columns: {cols})")

    lines.append("\nTable relationships (foreign keys):")
    found = False
    for table, info in schema.items():
        for fk in info["foreign_keys"]:
            lines.append(f"  - {table}.{fk['from_col']} → {fk['to_table']}.{fk['to_col']}")
            found = True
    if not found:
        lines.append("  - None found.")

    lines.append("\nRULE: You cannot write SQL. Use only the tools provided.")
    lines.append("For multi-table questions, call tools in sequence using the foreign key relationships above.")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# ZERO-KNOWLEDGE SQL TEMPLATES
#
# All SQL lives here. Claude never sees these.
# Every query is parameterized — no SQL injection possible.
# These 4 functions work for ANY table name passed in.
# ──────────────────────────────────────────────

def sql_get(table: str, filters: dict) -> list:
    """SELECT with optional WHERE filters."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if filters:
        where = " AND ".join([f"{col} = ?" for col in filters.keys()])
        cur.execute(f"SELECT * FROM {table} WHERE {where}", list(filters.values()))
    else:
        cur.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows

def sql_create(table: str, data: dict) -> str:
    """INSERT a new row."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()
    return f"Row inserted into {table}."

def sql_update(table: str, row_id: int, data: dict) -> str:
    """UPDATE a row by id."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
    cur.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", list(data.values()) + [row_id])
    conn.commit()
    conn.close()
    return f"Row {row_id} updated in {table}."

def sql_delete(table: str, row_id: int) -> str:
    """DELETE a row by id."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ?", [row_id])
    conn.commit()
    conn.close()
    return f"Row {row_id} deleted from {table}."


# ──────────────────────────────────────────────
# STEP 4: Scan + build prompt + start MCP server
# ──────────────────────────────────────────────

schema = scan_db(DB_PATH)


prompt = build_prompt(schema)


mcp = FastMCP("zero-knowledge-db", instructions=prompt)


# ──────────────────────────────────────────────
# STEP 5: Generate CRUD tools in memory for every table
#
# For each table, 4 functions are created and registered
# into mcp.tools dict via @mcp.tool() decorator.
#
# make_X(t) pattern freezes the table name inside each
# function via closure. Without this all functions would
# use the last value of `table` from the loop.
#
# After this loop, mcp.tools has 4 * len(schema) entries.
# When Claude Desktop asks "what tools exist?", the SDK
# replies with this full list automatically.
# ──────────────────────────────────────────────

for table in schema.keys():

    def make_get(t):
        @mcp.tool(
            name=f"get_{t}",
            description=f"Get rows from {t}. filters = JSON string like '{{\"col\":\"val\"}}' or empty string for all rows."
        )
        def get_tool(filters: str = "") -> str:
            parsed = json.loads(filters) if filters.strip() else {}
            rows = sql_get(t, parsed)
            return json.dumps(rows, indent=2)
        return get_tool
    make_get(table)

    def make_create(t):
        @mcp.tool(
            name=f"create_{t}",
            description=f"Insert a new row into {t}. data = JSON string like '{{\"col\":\"val\"}}'."
        )
        def create_tool(data: str) -> str:
            return sql_create(t, json.loads(data))
        return create_tool
    make_create(table)

    def make_update(t):
        @mcp.tool(
            name=f"update_{t}",
            description=f"Update a row in {t} by id. data = JSON string of fields to update."
        )
        def update_tool(row_id: int, data: str) -> str:
            return sql_update(t, row_id, json.loads(data))
        return update_tool
    make_update(table)

    def make_delete(t):
        @mcp.tool(
            name=f"delete_{t}",
            description=f"Delete a row from {t} by id."
        )
        def delete_tool(row_id: int) -> str:
            return sql_delete(t, row_id)
        return delete_tool
    make_delete(table)




if __name__ == "__main__":
    mcp.run()