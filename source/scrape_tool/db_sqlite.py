import logging
import pathlib
import sqlite3

# Track which site DBs we've cleared this run to avoid repeated resets
_db_reset_done = set()

logger = logging.getLogger(__name__)


def connect_db(db_file: pathlib.Path) -> sqlite3.Connection:
    return sqlite3.connect(str(db_file))


def check_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cur.fetchone() is not None


def _init_site_db(path: pathlib.Path, read_only: bool = False) -> sqlite3.Connection:
    db_file = path / 'pages.db'
    conn = connect_db(db_file)
    cur = conn.cursor()
    # Check if the pages table already exists
    table_exists = check_table_exists(conn, 'pages')

    # Ensure table exists
    cur.execute(
        'CREATE TABLE IF NOT EXISTS pages (site TEXT, url TEXT PRIMARY KEY, content TEXT)'
    )
    conn.commit()

    # If the table already existed, remove all existing rows — only once per run
    db_key = str(path.resolve())
    if read_only:
        return conn
    if table_exists and db_key not in _db_reset_done:
        cur.execute('DELETE FROM pages')
        conn.commit()
        _db_reset_done.add(db_key)
        logger.info(f'Cleared existing database at {db_file}.')
    return conn
