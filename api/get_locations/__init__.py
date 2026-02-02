"""
Get Delivery Locations Function - Lookup ship-to locations
"""
import azure.functions as func
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.session_store import SessionStore
from shared.sap_connection import SAPConnectionManager
from cryptography.fernet import Fernet


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get delivery locations for a sold-to partner.

    Expects:
    - X-Session-Id header with valid session ID
    - Query parameter: sold_to

    Returns list of ship-to locations.
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

        # Get sold-to from query params
        sold_to = req.params.get('sold_to', '').strip()

        if not sold_to:
            return func.HttpResponse(
                json.dumps({'error': 'sold_to parameter required'}),
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
            # Pad partner number
            if sold_to.isdigit():
                sold_to_padded = sold_to.zfill(10)
            else:
                sold_to_padded = sold_to

            # Call BAPI to get partner locations
            # This is a placeholder - implement actual BAPI call as needed
            result = conn.call(
                'BAPI_CUSTOMER_GETLIST',
                IDRANGE=[{'SIGN': 'I', 'OPTION': 'EQ', 'LOW': sold_to_padded}]
            )

            locations = []
            for addr in result.get('ADDRESSDATA', []):
                locations.append({
                    'partner': addr.get('CUSTOMER', ''),
                    'name': addr.get('NAME', ''),
                    'city': addr.get('CITY', '')
                })

        finally:
            conn.close()

        return func.HttpResponse(
            json.dumps({
                'success': True,
                'locations': locations
            }),
            mimetype='application/json'
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )
