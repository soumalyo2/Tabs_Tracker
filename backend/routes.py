from flask import Blueprint, jsonify, request
from models import SessionModel, TabModel

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/health', methods=['GET'])
def health():
    """Health check endpoint to test backend connectivity."""
    active_id = SessionModel.get_active_session_id()
    return jsonify({
        "status": "healthy",
        "message": "The system is online and running.",
        "active_session": active_id
    }), 200

@api_blueprint.route('/track', methods=['POST'])
@api_blueprint.route('/track-tab', methods=['POST'])
def track():
    """Receives tab navigation telemetry from Chrome extension."""
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    title = (data.get('title') or url or 'Untitled').strip()
    fav_icon_url = (data.get('fav_icon_url') or data.get('favicon_url') or '').strip()

    if not url or not (url.startswith('http://') or url.startswith('https://')):
        return jsonify({"status": "ignored", "message": "Non-HTTP/HTTPS URLs are ignored."}), 400

    try:
        session_id = SessionModel.get_or_create_active_session()
        TabModel.upsert_tab(
            session_id=session_id,
            url=url,
            title=title,
            fav_icon_url=fav_icon_url
        )
        return jsonify({
            "status": "success",
            "message": "Tab tracked successfully",
            "session_id": session_id
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route('/new_session', methods=['POST'])
@api_blueprint.route('/new-session', methods=['POST'])
def new_session():
    """Explicitly rolls over to a fresh active session."""
    try:
        new_session_id = SessionModel.create_session()
        return jsonify({
            "status": "success",
            "message": "New session created successfully.",
            "session_id": new_session_id
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route('/get_sessions', methods=['GET'])
@api_blueprint.route('/get_active_session', methods=['GET'])
@api_blueprint.route('/get-sessions', methods=['GET'])
def get_sessions():
    """Returns all session groups with their associated tabs for the extension popup."""
    try:
        sessions_map = TabModel.fetch_history_grouped()
        active_id = SessionModel.get_active_session_id()
        return jsonify({
            "status": "success",
            "active_session": active_id,
            "sessions": sessions_map,
            "active_session_id": sessions_map
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route('/delete_session/<session_id>', methods=['DELETE'])
@api_blueprint.route('/delete-session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Deletes a session and cascades deletion to all its tabs."""
    try:
        SessionModel.delete_session(session_id)
        # If deleted active session, spawn a replacement if none is active
        active_id = SessionModel.get_active_session_id()
        if not active_id:
            SessionModel.create_session()
        return jsonify({
            "status": "success",
            "message": f"Session {session_id} deleted successfully."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route('/clear_all_sessions', methods=['DELETE'])
@api_blueprint.route('/clear_all_session', methods=['DELETE'])
@api_blueprint.route('/clear-all-sessions', methods=['DELETE'])
def clear_all_sessions():
    """Wipes all sessions and tabs, and spawns a fresh active session."""
    try:
        SessionModel.clear_all_records()
        new_session_id = SessionModel.create_session()
        return jsonify({
            "status": "success",
            "message": "All session history cleared successfully.",
            "session_id": new_session_id
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route('/get_session/<session_id>', methods=['GET'])
def get_single_session(session_id):
    """Fetches metadata for a single session."""
    try:
        session = SessionModel.get_session(session_id)
        if not session:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        return jsonify({
            "status": "success",
            "session": {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "last_active": session.last_active,
                "is_active": session.is_active
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500