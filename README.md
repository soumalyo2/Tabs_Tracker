# Tab Tracker

Tab Tracker is a local browser session management and history tracking system. It consists of a Google Chrome Extension (Manifest V3) that captures tab navigation events and a local Python Flask backend that persists browsing sessions and tab visit metrics in an embedded SQLite database.

---

## Architecture Overview

1. **Frontend (Browser Extension)**:
   - **Service Worker (`background.js`)**: Asynchronously monitors browser tab navigation events (`chrome.tabs.onUpdated`), filters out non-HTTP/HTTPS and internal browser URLs, and dispatches telemetry payloads to the local backend.
   - **Popup Interface (`popup.html`, `popup.js`)**: Displays tracked browsing sessions grouped by creation time, tracks tab visit frequencies, supports batch tab restoration into active browser windows, provides manual session lifecycle controls, and supports custom interface color themes.

2. **Backend (REST API)**:
   - **Flask API (`app.py`, `routes.py`)**: Handles incoming HTTP requests from the extension, validates payloads, manages CORS, and routes operations to model abstractions.
   - **Session Engine & Models (`models.py`)**: Enforces a 30-minute idle-timeout session rolling rule, automatically manages active session states, and executes database queries.

3. **Storage (SQLite Database)**:
   - Relational schema with foreign key constraints, cascading deletes, and unique composite indexes to support upsert operations on tab revisit.

---

## File Structure

```
project-tab-tracker/
├── backend/
│   ├── app.py              # Application entry point and server initialization
│   ├── config.py           # Configuration variables and file paths
│   ├── database.py         # SQLite connection factory and schema migration runner
│   ├── models.py           # SessionModel and TabModel database interaction logic
│   ├── requirements.txt    # Python package dependencies
│   ├── routes.py           # Flask Blueprint API route definitions
│   └── schema.sql          # DDL definitions for sessions and tabs tables
└── extensions/
    ├── background.js       # Extension service worker listening to tab events
    ├── manifest.json       # Manifest V3 extension configuration and permissions
    ├── popup.html          # Extension popup markup and theme styling
    └── popup.js            # Popup DOM manipulation, API client, and event handling
```

---

## Prerequisites

- **Python**: Version 3.8 or higher
- **Browser**: Google Chrome, Brave, Microsoft Edge, or any Chromium-based browser supporting Manifest V3
- **Git** (optional, for cloning)

---

## Installation and Setup

### 1. Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. (Recommended) Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   python app.py
   ```
   The server will start on `http://127.0.0.1:5000`. The SQLite database (`database.db`) will be automatically created and initialized on the first launch.

---

### 2. Chrome Extension Installation

1. Open Google Chrome and enter `chrome://extensions` in the address bar.
2. Enable **Developer mode** using the toggle switch located in the upper-right corner.
3. Click the **Load unpacked** button located in the upper-left corner.
4. Select the `extensions/` directory inside this repository.
5. The **Tab Tracker** extension icon will now appear in your browser's toolbar/extensions menu.

---

## API Reference

All backend API routes are prefixed under `/api`.

| Method | Endpoint | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Backend diagnostic check and active session query | None | `{"status": "healthy", "active_session": "<uuid>"}` |
| `POST` | `/api/track` | Logs or updates a tab visit | `{"url": "string", "title": "string", "fav_icon_url": "string"}` | `{"status": "success", "session_id": "<uuid>"}` |
| `POST` | `/api/new_session` | Deactivates current session and allocates a new session | None | `{"status": "success", "session_id": "<uuid>"}` |
| `GET` | `/api/get_sessions` | Retrieves all sessions and their associated tabs | None | `{"status": "success", "sessions": {...}}` |
| `DELETE` | `/api/delete_session/<id>` | Deletes a session and cascades deletion to its tabs | None | `{"status": "success", "message": "..."}` |
| `DELETE` | `/api/clear_all_sessions` | Deletes all session and tab records | None | `{"status": "success", "session_id": "<new_uuid>"}` |
| `GET` | `/api/get_session/<id>` | Fetches metadata for an individual session | None | `{"status": "success", "session": {...}}` |

---

## Database Schema

The database utilizes SQLite with foreign key enforcement enabled (`PRAGMA foreign_keys = ON`).

### `sessions` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `session_id` | `TEXT` | `PRIMARY KEY` | RFC 4122 UUID representing the session |
| `created_at` | `TEXT` | `NOT NULL` | ISO 8601 UTC timestamp of creation |
| `last_active` | `TEXT` | `NOT NULL` | ISO 8601 UTC timestamp of the most recent tab activity |
| `is_active` | `INTEGER` | `NOT NULL DEFAULT 1` | `1` indicates currently active session, `0` indicates closed |

### `tabs` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Internal row identifier |
| `session_id` | `TEXT` | `NOT NULL`, `FOREIGN KEY ... ON DELETE CASCADE` | Associated parent session ID |
| `url` | `TEXT` | `NOT NULL` | Tracked webpage URL |
| `title` | `TEXT` | | Webpage title |
| `fav_icon_url` | `TEXT` | | URL to page favicon |
| `visit_count` | `INTEGER` | `NOT NULL DEFAULT 1` | Number of times page was visited in this session |
| `first_visited`| `TEXT` | `NOT NULL` | ISO 8601 UTC timestamp of initial visit |
| `last_visited` | `TEXT` | `NOT NULL` | ISO 8601 UTC timestamp of latest visit |

- **Composite Constraint**: `UNIQUE (session_id, url)` prevents duplicate records and drives SQL `ON CONFLICT` upsert operations.
- **Indexes**: `idx_tabs_session` on `tabs(session_id)` and `idx_tabs_last_visited` on `tabs(last_visited)`.

---

## Extension Controls and Features

- **Automatic Session Rolling**: If the browser receives no navigation events for longer than 30 minutes (`IDLE_TIMEOUT_SECONDS = 1800`), the current session closes automatically, and the next page load initializes a new session.
- **Batch Tab Restoration**: Check individual tabs or use the master "Select All" checkbox, then click **Restore Selected** to open all checked URLs in background browser tabs.
- **New Session**: Click **New Session** in the toolbar to manually split your browsing timeline and start a fresh session immediately.
- **Palette Selector**: The popup header includes a theme dropdown (`Archive`, `Ash`, `Crimson`, `Heather`, `Sienna`, `Spruce`). Selected themes are saved in `localStorage` and persist across browser restarts.
- **Anti-Gravity Privacy Mode**: Pressing `Escape` or clicking the **Panic** button hides all tracking views from DOM memory and opens a decoy page (`https://xkcd.com/353/`).
