"""
Zero-Knowledge MCP Server
"""

import os
import json
import sqlite3
from mcp.server.fastmcp import FastMCP


#get db from config or fallback to demo db

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "legacy.db")  # fallback
)


#error handling
if not os.path.exists(DB_PATH):

    raise SystemExit(1)




# Returns a dict like:
# {
#   "users":  { "columns": ["id","name","email"], "foreign_keys": [] },
#   "orders": { "columns": ["id","user_id",...],
#               "foreign_keys": [{"from_col":"user_id","to_table":"users","to_col":"id"}] }
# }


def scan_db(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # cur.fetchall returns: [('users',), ('products',), ('orders',)]
    tables = [row[0] for row in cur.fetchall()]
    # ['users','products','orders']
    schema = {}
    for table in tables:
        cur.execute(f"PRAGMA table_info({table});")
        # [(0, 'id', 'INTEGER', 0, None, 1),
        # (1, 'name', 'TEXT', 0, None, 0),
        # (2, 'email', 'TEXT', 0, None, 0)]
        columns = [row[1] for row in cur.fetchall()]

        cur.execute(f"PRAGMA foreign_key_list({table});")
        # [{'from_col': 'product_id', 'to_table': 'products', 'to_col': 'id'},
        # {'from_col': 'user_id', 'to_table': 'users', 'to_col': 'id'}]
        fks = [{"from_col": fk[3],"to_table": fk[2],"to_col": fk[4]} for fk in cur.fetchall()]
        schema[table] = {"columns": columns, "foreign_keys": fks}

    conn.close()
    return schema



#Build context prompt from schema
# This string is passed to Claude as system instructions.

#INPUT
# {
#   "users":  { "columns": ["id","name","email"], "foreign_keys": [] },
#   "orders": { "columns": ["id","user_id",...],
#               "foreign_keys": [{"from_col":"user_id","to_table":"users","to_col":"id"}] }
# }

#OUTPUT
# You have access to these tables:
# - users (id, name, email)
# - orders (id, user_id, amount, status)
# - products (id, name, price)

# Table relationships (foreign keys)::
# - orders.user_id = users.id
# - orders.product_id = products.id

# RULE: You cannot write SQL. Use only the provided tools.
# For multi-table questions, call tools in sequence using the foreign key relationships above.


def build_prompt(schema: dict) -> str:
    lines = ["You have access to a database with these tables:\n"]

    for table, info in schema.items():
        cols = ", ".join(info["columns"])
        lines.append(f"  - {table} (columns: {cols})")

    lines.append("\nTable relationships (foreign keys):")
    found = False
    for table, info in schema.items():
        for fk in info["foreign_keys"]:
            lines.append(f"  - {table}.{fk['from_col']} = {fk['to_table']}.{fk['to_col']}")
            found = True
    if not found:
        lines.append("  - None found.")

    lines.append("\nRULE: You cannot write SQL. Use only the tools provided.")
    lines.append("For multi-table questions, call tools in sequence using the foreign key relationships above.")

    return "\n".join(lines)




# ZERO-KNOWLEDGE SQL TEMPLATES

# filters={"name": "john"}
def sql_get(table: str, filters: dict) -> list:
    """SELECT with optional WHERE filters."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if filters:
        where = " AND ".join([f"{col} = ?" for col in filters.keys()])
        cur.execute(f"SELECT * FROM {table} WHERE {where}", list(filters.values()))
    else:
        cur.execute(f"SELECT * FROM {table}")
    #gets columns from the current table
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows


#data = {"name": "john", "email": "john@gmail.com"}
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



# Scan + build prompt + start MCP server


schema = scan_db(DB_PATH)


prompt = build_prompt(schema)


mcp = FastMCP("zero-knowledge-db", instructions=prompt)



# Generate CRUD tools in memory for every table

# For each table, 4 functions are created 

# After this loop, mcp.tools has 4 * len(schema) entries.

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
    

    def make_create(t):
        @mcp.tool(
            name=f"create_{t}",
            description=f"Insert a new row into {t}. data = JSON string like '{{\"col\":\"val\"}}'."
        )
        def create_tool(data: str) -> str:
            return sql_create(t, json.loads(data))
        return create_tool
    

    def make_update(t):
        @mcp.tool(
            name=f"update_{t}",
            description=f"Update a row in {t} by id. data = JSON string of fields to update."
        )
        def update_tool(row_id: int, data: str) -> str:
            return sql_update(t, row_id, json.loads(data))
        return update_tool
    

    def make_delete(t):
        @mcp.tool(
            name=f"delete_{t}",
            description=f"Delete a row from {t} by id."
        )
        def delete_tool(row_id: int) -> str:
            return sql_delete(t, row_id)
        return delete_tool
    
    make_get(table)
    make_create(table)
    make_update(table)
    make_delete(table)




if __name__ == "__main__":
    mcp.run()