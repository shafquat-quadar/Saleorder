"""
Create Sales Orders Function
"""
import azure.functions as func
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.session_store import SessionStore
from shared.sap_connection import SAPConnectionManager
from shared.sap_sales_order import create_sales_orders
from cryptography.fernet import Fernet


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Create sales orders from selected rows.

    Expects:
    - X-Session-Id header with valid session ID
    - JSON body with 'rows' array of enriched data

    Returns results with sales order numbers.
    """
    try:
        # Validate session
        session_id = req.headers.get('X-Session-Id')
        session_store = SessionStore()
        session = session_store.get_session(session_id)

        if not session:
            return func.HttpResponse(
                json.dumps({'error': 'Invalid or expired session'}),
                status_code=401,
                mimetype='application/json'
            )

        # Get rows from request
        body = req.get_json()
        rows = body.get('rows', [])

        if not rows:
            return func.HttpResponse(
                json.dumps({'error': 'No rows provided'}),
                status_code=400,
                mimetype='application/json'
            )

        # Decrypt password
        key = os.environ.get('ENCRYPTION_KEY').encode()
        fernet = Fernet(key)
        password = fernet.decrypt(session['password'].encode()).decode()

        # Connect to SAP
        system = session.get('system', 'PRD')
        sap = SAPConnectionManager(system)
        conn = sap.connect(session['user'], password, session['client'])

        try:
            result = create_sales_orders(conn, rows, session['user'])
        finally:
            conn.close()

        return func.HttpResponse(
            json.dumps(result),
            mimetype='application/json'
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )
