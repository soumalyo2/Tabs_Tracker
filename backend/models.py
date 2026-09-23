from datetime import datetime, timezone, timedelta
import sqlite3
from config import DATABASE_PATH, IDLE_TIMEOUT_SECONDS
from database import db_connection
import uuid

class SessionModel:
    def __init__(self, session_id, created_at, last_active, is_active=1):
        self.session_id = session_id
        self.created_at = created_at
        self.last_active = last_active
        self.is_active = is_active

    @staticmethod
    def create_session():
        """Generates a secure UUID string key and logs a new monitoring session folder."""
        new_session_id = str(uuid.uuid4())
        current_time_str = datetime.now(timezone.utc).isoformat()
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (session_id, created_at, last_active, is_active) VALUES (?, ?, ?, 1)", 
                (new_session_id, current_time_str, current_time_str)
            )
            return new_session_id

    @staticmethod
    def get_session(session_id):
        """Fetches operational rows utilizing clear key labels powered by row_factory configuration flags."""
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return SessionModel(
                session_id=row['session_id'],
                created_at=row['created_at'],
                last_active=row['last_active'],
                is_active=row['is_active']
                )
            return None

    @staticmethod
    def update_last_active(session_id):
        """Updates the monitoring heartbeat timestamp to track active presence state bounds."""
        current_time_str = datetime.now(timezone.utc).isoformat()
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET last_active = ? WHERE session_id = ?", (current_time_str, session_id))

    @staticmethod
    def deactivate_expired_sessions():
        """CV Alignment Fix: Flips flags to inactive states without wiping your historical text link logs."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=IDLE_TIMEOUT_SECONDS)
        cutoff_str = cutoff_time.isoformat()
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET is_active = 0 WHERE last_active < ? AND is_active = 1", 
                (cutoff_str,)
            )
    @staticmethod
    def delete_session(session_id):
        """
        Deletes a specific session. 
        Because schema.sql uses ON DELETE CASCADE, all associated tabs 
        in the 'tabs' table will be automatically destroyed by the database.
        """
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

    @staticmethod
    def clear_all_records():
        """
        Wipes all tracking history completely. 
        Deletes all sessions, which cascades down to wipe the tabs table as well.
        """
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions")

class TabModel:
    def __init__(self, id, session_id, url, title, fav_icon_url, visit_count, first_visited, last_visited):
        self.id = id
        self.session_id = session_id
        self.url = url
        self.title = title
        self.fav_icon_url = fav_icon_url
        self.visit_count = visit_count
        self.first_visited = first_visited
        self.last_visited = last_visited

    @staticmethod
    def upsert_tab(session_id, url, title, fav_icon_url=None):
        """
        Executes a smart Upsert strategy. If the URL is new to the session, it inserts it.
        If it already exists, it updates the frequency counter and tracking metrics.
        """
        current_time_str = datetime.now(timezone.utc).isoformat()
        with db_connection() as conn:
            cursor = conn.cursor()
        # Leveraging the UNIQUE(session_id, url) constraint defined in schema.sql
            cursor.execute("""
                INSERT INTO tabs (session_id, url, title, fav_icon_url, first_visited, last_visited)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, url) DO UPDATE SET
                    visit_count = visit_count + 1,
                    title = excluded.title,
                    fav_icon_url = excluded.fav_icon_url,
                    last_visited = excluded.last_visited
            """, (session_id, url, title, fav_icon_url, current_time_str, current_time_str))

    @staticmethod
    def fetch_history_grouped():
        """
        Pulls chronological tab tracking records and groups them into dictionary maps
        separated by their parent Session UUIDs for the frontend UI accordion.
        """
        with db_connection() as conn:
            cursor = conn.cursor()

        ### Relational join ordering data by the absolute latest visits first

            cursor.execute("""
            SELECT t.session_id, t.url, t.title, t.fav_icon_url, t.visit_count, t.last_visited, s.created_at
            FROM tabs t
            JOIN sessions s ON t.session_id = s.session_id
            ORDER BY s.created_at DESC, t.last_visited DESC
            """)
            rows = cursor.fetchall()

            sessions_map = {}
            for row in rows:
                sid = row['session_id']
                if sid not in sessions_map:
                    sessions_map[sid] = []

                    sessions_map[sid].append({
                    "url": row['url'],
                    "title": row['title'],
                    "fav_icon_url": row['fav_icon_url'],
                    "visits": row['visit_count'],
                    "time": row['last_visited']
                    })
            return sessions_map