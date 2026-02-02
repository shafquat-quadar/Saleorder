"""
Logout Function - Deletes user session
"""
import azure.functions as func
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.session_store import SessionStore


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle logout request.

    Expects X-Session-Id header with valid session ID.
    """
    try:
        session_id = req.headers.get('X-Session-Id')

        if session_id:
            session_store = SessionStore()
            session_store.delete_session(session_id)

        return func.HttpResponse(
            json.dumps({'success': True}),
            mimetype='application/json'
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'success': False, 'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )
