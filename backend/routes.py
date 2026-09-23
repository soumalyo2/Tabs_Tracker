'''
from flask import Blueprint, request, jsonify
from models import SessionModel, TabModel
from datetime import datetime
import os
from config import DATABASE_PATH 

### Instantiate a modern isolated routing controller component

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route("/health", methods=["GET"])
def health():
    """Healthcheck endpoint returning server engine diagnostics state."""
    try:
    # Check active session status by probing the logic layers dynamically
        active_id = SessionModel.get_active_session_id()
        return jsonify({
        "status": "online",
        "service": "Local Tab Tracker Backend Pro",
        "active_session": active_id,
        "database_exists": os.path.exists(DATABASE_PATH)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route("/track-tab", methods=["POST"])
def track_tab():
    """Receives tab data from Chrome and applies session filters and Upserts."""
    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()
    title = (payload.get("title") or "Untitled").strip()
    fav_icon_url = (payload.get("favIconUrl") or "").strip() 

    ### Browser edge case filtration rule:

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"status": "ignored", "message": "Non-HTTP/HTTPS URLs are filtered out."}), 400

    try:

        ### 1. Heartbeat check: roll idle sessions down if timeout thresholds are passed

        SessionModel.deactivate_expired_sessions()

        ### 2. Get active UUID identifier (automatically spawns one if none exist)

        session_id = SessionModel.get_or_create_active_session()

        # 3. Stream record data downstream to the atomic data engine layer
        TabModel.upsert_tab(session_id, url, title, fav_icon_url)

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "tab": {
                "url": url,
                "title": title,
                "recorded_at": datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route("/new-session", methods=["POST"])
def create_new_session():
"""Forcibly cuts off current timeline paths to roll a fresh session window."""
try:
SessionModel.deactivate_expired_sessions() # Close current tracking states
new_session_id = SessionModel.create_session() # Allocate clean tracking window
return jsonify({
"status": "success",
"message": "Brand-new session initiated successfully.",
"session_id": new_session_id
}), 201
except Exception as e:
return jsonify({"status": "error", "message": str(e)}), 500 

@api_blueprint.route("/get-sessions", methods=["GET"])
def get_sessions():
"""Feeds structured group maps upstream to draw the frontend interface panels."""
try:
current_active_id = SessionModel.get_active_session_id()
history_data = TabModel.fetch_history_grouped(current_active_id) 

return jsonify({
    "status": "success",
    "active_session": current_active_id,
    "sessions": history_data
}), 200

except Exception as e:
return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route("/delete-session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
"""Removes a session node and triggers automated database cascades."""
try:
SessionModel.delete_session(session_id) 

# Self-healing logic check: If we just killed our active thread window, spawn a replacement
active_id = SessionModel.get_active_session_id()
new_active = None
if not active_id:
    new_active = SessionModel.create_session()
    
return jsonify({
    "status": "success",
    "message": f"Session {session_id} deleted successfully.",
    "new_active_session": new_active
}), 200

except Exception as e:
return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route("/clear-all-sessions", methods=["DELETE"])
def clear_all_sessions():
"""Flushes complete storage engine schemas and leaves a clear monitoring slate."""
try:
SessionModel.clear_all_records()
new_session_id = SessionModel.create_session()
return jsonify({
"status": "success",
"message": "All session history cleared.",
"active_session": new_session_id
}), 200
except Exception as e:
return jsonify({"status": "error", "message": str(e)}), 500

'''

from flask import Blueprint, jsonify, request
from models import SessionModel, TabModel

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/health', methods = ['GET'])
def health():
    return jsonify({"status": "healthy","message": "The system is back online and running."}),200

@api_blueprint.route('/track', methods = ['POST'])
def track():
    data = request.json

    if not data or not data.get('url') or not data.get('title'):
        return jsonify({"error": "The url or the title could not be fetcheed from the request."}),400

    session_id = SessionModel.get_or_create_active_session()
    session_id.touch_session()

    TabModel.upsert_tab(session_id = session_id, url = data.get('url'),title = data.get('title'),favicon_url = data.get('favicon_url',''))
    return jsonify({"message":"tab tracked successfully","session_id": session_id}),200 

@api_blueprint.route('/new_session', methods = ['POST'])
def new_session():
    new_session_id = SessionModel.create_session()
    return jsonify({"message":"New session is created successfully","session_id": new_session_id}),201

@api_blueprint.route('/get_active_session', methods = ['GET'])
def get_active_session():
    active_session_id = TabModel.fetch_history_grouped()
    return jsonify({"active_session_id": active_session_id}),200

@api_blueprint.route('/delete_session/<session_id>', methods = ['DELETE'])
def delete_session(session_id):
    SessionModel.delete_session(session_id)
    return jsonify({"message": f"Session {session_id} deleted successfully."}),200

@api_blueprint.route('/clear_all_session/<session_id>', methods = ['DELETE'])
def clear_all_sessions():
    SessionModel.clear_all_records()
    return jsonify({"message": "All session history cleared successfully."}),200


@api_blueprint.route('/get_session/<session_id>', methods=['GET'])
def get_single_session(session_id):
    session = SessionModel.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404 
    return jsonify({"session": {"session_id": session.session_id,"created_at": session.created_at, "last_active": session.last_active,"is_active": session.is_active}}), 200