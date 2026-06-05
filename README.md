# AutoMCP-SQL — Zero-Knowledge MCP Server

An MCP server that **autonomously scans any SQLite database**, generates typed CRUD tools for every table it discovers, builds a schema-aware prompt explaining joins/relationships, and enforces **Zero-Knowledge security** — the LLM never writes raw SQL, only calls pre-validated parameterized templates.

---

## What It Does

| Feature | Detail |
|---|---|
| **Auto-Discovery** | Scans `sqlite_master` at startup; no manual table registration |
| **CRUD Generation** | Creates `get_`, `create_`, `update_`, `delete_` tools per table in memory |
| **Schema Prompt** | Injects table columns + foreign-key relationships as MCP instructions |
| **Zero-Knowledge SQL** | Instead of allowing the LLM to write arbitrary SQL (which risks SQL injection and destructive operations), the server generates isolated CRUD tools (Create, Read, Update, Delete) in memory for *each* table. The LLM interacts with these safe, pre-validated python templates |
| **Configurable DB** | Point at any SQLite file via `DB_PATH` env var |

---

## Project Structure

```
AutoMCP-SQL/
├── server.py        # MCP server — scans DB, generates tools, starts server
├── setupdb.py       # One-time script to create and seed legacy.db for testing
├── legacy.db        # SQLite database (auto-created by setupdb.py)
├── pyproject.toml   # Dependencies managed by uv
├── uv.lock          # Lockfile — guarantees reproducible installs
└── README.md
```

---

## Tech Stack

| Tool | Why |
|---|---|
| **[FastMCP](https://github.com/jlowin/fastmcp)** | Minimal decorator-based MCP server; zero boilerplate for tool registration |
| **sqlite3** (stdlib) | No extra dependency; sufficient for parameterized CRUD on any SQLite file |
| **uv** | 10-100× faster than pip; lockfile guarantees reproducible installs across machines |
| **MCP (Model Context Protocol)** | Standard protocol for giving LLMs structured, auditable tool access |

---

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — fast Python package/project manager
- **[Claude Desktop](https://claude.ai/download)** — to connect the MCP server

Install `uv` if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Mav977/AutoMCP-SQL.git
cd AutoMCP-SQL
```

### 2. Install dependencies

```bash
uv sync
```

This reads `uv.lock` and recreates the exact virtual environment.

### 3. Seed the demo database

```bash
uv run setupdb.py
```

This creates `legacy.db` in the project root with sample tables (`users`, `orders`, `products`, etc.) so you can test immediately.

> **Using your own database?** Skip this step and point `DB_PATH` at your existing `.db` file (see Configuration below).

---

### 1. Open your Claude Desktop config file

You can access the configuration file directly from within the app:
1. Open **Claude Desktop**.
2. Navigate to **Settings**.
3. Select the **Developer** tab.
4. Click **Edit Config** to open the `claude_desktop_config.json` file in your default text editor.

### 2. Add the MCP server entry

Replace the path below with the **absolute path** to your cloned `server.py`:

**Windows:**
```json
{
  "mcpServers": {
    "AutoMCP-SQL": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "C:\\Users\\YourName\\Desktop\\Projects\\AutoMCP-SQL\\server.py"
      ],
      "env": {
        "DB_PATH": "C:\\Users\\YourName\\Desktop\\Projects\\AutoMCP-SQL\\legacy.db"
      }
    }
  }
}
```

**macOS / Linux:**
```json
{
  "mcpServers": {
    "AutoMCP-SQL": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "/home/yourname/projects/AutoMCP-SQL/server.py"
      ],
      "env": {
        "DB_PATH": "/home/yourname/projects/AutoMCP-SQL/legacy.db"
      }
    }
  }
}
```

> **Important:** Use double backslashes (`\\`) in Windows paths inside JSON.

### 3. Restart Claude Desktop

Fully quit and reopen Claude Desktop. The MCP server starts automatically when Claude launches.

### 4. Verify the connection

Open a new conversation in Claude Desktop. Click the **plus icon (+)** in the chat input area, select **Connectors**, and then click **Manage connectors**. Here, you will see `AutoMCP-SQL` listed along with all the tools the MCP has access to (like `get_users`, `create_orders`, etc.).

You can also just ask Claude:
> *"What tables do you have access to?"*

Claude will use the injected schema prompt to describe the database structure without querying it.

---

## Using Your Own Database

Set `DB_PATH` in the config to point at any existing SQLite file:

```json
"env": {
  "DB_PATH": "C:\\path\\to\\your\\database.db"
}
```

The server will scan it on startup and auto-generate tools for every table it finds — no code changes needed.

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `DB_PATH` | `./legacy.db` (next to `server.py`) | Path to the SQLite database file |

---

## How Zero-Knowledge Security Works

The server never exposes raw SQL execution to the LLM. Instead:

1. On startup, `scan_db()` reads the schema and builds a natural-language prompt describing tables and relationships.
2. For each table, four tool functions are registered with hard-coded SQL templates:
   - `get_<table>` → `SELECT * FROM <table> WHERE col = ?`
   - `create_<table>` → `INSERT INTO <table> (cols) VALUES (?)`
   - `update_<table>` → `UPDATE <table> SET col = ? WHERE id = ?`
   - `delete_<table>` → `DELETE FROM <table> WHERE id = ?`
3. All values are passed as parameterized arguments — never string-interpolated into queries.
4. Claude can only call these named tools; it has no mechanism to execute arbitrary SQL.

This means even a prompt-injected or jailbroken model cannot run `DROP TABLE` or exfiltrate data via `UNION` — the attack surface is limited to the four CRUD templates.



## Troubleshooting

**Server doesn't appear in Claude Desktop**
- Wait a few seconds; it may take some time to load.
- Double-check the path in `claude_desktop_config.json` — it must be the absolute path to `server.py`, not a folder.
- Make sure `uv` is on your system PATH (open a new terminal and run `uv --version` to verify).
- Fully quit Claude Desktop (system tray on Windows, Cmd+Q on Mac) and reopen it.

**`DB_PATH does not exist` error**
Run `uv run setupdb.py` first to create `legacy.db`, or update `DB_PATH` in the config to point at an existing database.

**Tools not showing up after config change**
Claude Desktop only reads the config on launch. Fully restart it after any config edits.