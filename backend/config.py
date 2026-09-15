import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
CACHE_FILE_PATH = os.path.join(BASE_DIR, "cache_session.txt")
IDLE_TIMEOUT_SECONDS = 30 * 60 #30 minutes of max idle time before the session is closed
