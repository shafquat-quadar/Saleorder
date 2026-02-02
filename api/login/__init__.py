"""
Login Function - Validates SAP credentials and creates session

Accepts system selection (DEV, QAS, PRD) along with user credentials.
Tests connection to the selected SAP system before creating session.
"""
import azure.functions as func
import json
import os
import sys

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.sap_connection import SAPConnectionManager
from shared.session_store import SessionStore
from cryptography.fernet import Fernet


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle login request.

    Expected JSON body:
    {
        "system": "DEV|QAS|PRD",
        "user": "SAP_USER",
        "password": "password",
        "client": "100"
    }

    Returns:
    {
        "success": true,
        "sessionId": "uuid",
        "user": "SAP_USER"
    }
    """
    try:
        body = req.get_json()
        system = body.get('system', '').strip().upper()
        user = body.get('user', '').strip().upper()
        password = body.get('password', '')
        client = body.get('client', '100').strip()

        # Validate required fields
        if not system:
            return func.HttpResponse(
                json.dumps({'success': False, 'error': 'System selection required'}),
                status_code=400,
                mimetype='application/json'
            )

        if not user or not password:
            return func.HttpResponse(
                json.dumps({'success': False, 'error': 'User and password required'}),
                status_code=400,
                mimetype='application/json'
            )

        # Create SAP connection manager for selected system
        try:
            sap = SAPConnectionManager(system)
        except ValueError as e:
            return func.HttpResponse(
                json.dumps({'success': False, 'error': str(e)}),
                status_code=400,
                mimetype='application/json'
            )

        # Test SAP connection
        if not sap.test_connection(user, password, client):
            return func.HttpResponse(
                json.dumps({'success': False, 'error': 'Invalid SAP credentials'}),
                status_code=401,
                mimetype='application/json'
            )

        # Encrypt password for session storage
        key = os.environ.get('ENCRYPTION_KEY').encode()
        fernet = Fernet(key)
        encrypted_password = fernet.encrypt(password.encode()).decode()

        # Create session
        session_store = SessionStore()
        session_id = session_store.create_session(
            user=user,
            client=client,
            system=system,
            password_encrypted=encrypted_password
        )

        return func.HttpResponse(
            json.dumps({
                'success': True,
                'sessionId': session_id,
                'user': user,
                'system': system
            }),
            mimetype='application/json'
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'success': False, 'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )
