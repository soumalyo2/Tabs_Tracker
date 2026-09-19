import sqlite3
import os
from config import DATABASE_PATH, BASE_DIR

def db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    # with db_connection() as conn:
    #     with open("backend/schema.sql") as f:
    #         conn.executescript(f.read())

                                                                    # Build an absolute path to the schema file to prevent path reference drift
    schema_path = os.path.join(BASE_DIR, "schema.sql")
    
    with db_connection() as conn:                                   # Open and read the raw text contents of your external SQL file
        with open(schema_path, "r", encoding="utf-8") as f:         # Run all tables, constraints, and indices in one atomic batch execution
            conn.executescript(f.read())                            # The safety Context Manager automatically commits changes and locks down resource handles


