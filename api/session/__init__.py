"""
Session Validation Function - Validates session and returns user info
"""
import azure.functions as func
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.session_store import SessionStore


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validate session and return user info.

    Expects X-Session-Id header with valid session ID.

    Returns:
    {
        "valid": true,
        "user": "SAP_USER",
        "system": "DEV|QAS|PRD"
    }
    """
    try:
        session_id = req.headers.get('X-Session-Id')

        if not session_id:
            return func.HttpResponse(
                json.dumps({'valid': False, 'error': 'No session ID provided'}),
                status_code=401,
                mimetype='application/json'
            )

        session_store = SessionStore()
        session = session_store.get_session(session_id)

        if not session:
            return func.HttpResponse(
                json.dumps({'valid': False, 'error': 'Invalid or expired session'}),
                status_code=401,
                mimetype='application/json'
            )

        return func.HttpResponse(
            json.dumps({
                'valid': True,
                'user': session['user'],
                'system': session.get('system', 'PRD')
            }),
            mimetype='application/json'
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'valid': False, 'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )
