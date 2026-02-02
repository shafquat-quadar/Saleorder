"""
Upload Function - Parse file and enrich with SAP data
"""
import azure.functions as func
import json
import os
import sys
import pandas as pd
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.session_store import SessionStore
from shared.sap_connection import SAPConnectionManager
from shared.sap_equipment import enrich_equipment_data
from cryptography.fernet import Fernet


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle file upload and SAP data enrichment.

    Expects:
    - X-Session-Id header with valid session ID
    - multipart/form-data with 'file' field

    Returns enriched data with SAP master data fields.
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

        # Get file from request
        file = req.files.get('file')
        if not file:
            return func.HttpResponse(
                json.dumps({'error': 'No file uploaded'}),
                status_code=400,
                mimetype='application/json'
            )

        # Parse file
        filename = file.filename.lower()
        file_content = file.read()

        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(file_content))
        else:
            return func.HttpResponse(
                json.dumps({'error': 'Unsupported file type. Use CSV or Excel.'}),
                status_code=400,
                mimetype='application/json'
            )

        # Normalize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        # Validate required columns
        required_cols = ['equipment_id', 'material', 'material_qty']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return func.HttpResponse(
                json.dumps({'error': f'Missing required columns: {missing}'}),
                status_code=400,
                mimetype='application/json'
            )

        # Convert to list of dicts with row numbers
        rows = df.to_dict('records')
        for i, row in enumerate(rows):
            row['row_number'] = i + 1
            # Convert any NaN values to empty strings
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = ''

        # Decrypt password
        key = os.environ.get('ENCRYPTION_KEY').encode()
        fernet = Fernet(key)
        password = fernet.decrypt(session['password'].encode()).decode()

        # Connect to SAP and enrich data
        system = session.get('system', 'PRD')
        sap = SAPConnectionManager(system)
        conn = sap.connect(session['user'], password, session['client'])

        try:
            enriched_rows = enrich_equipment_data(conn, rows)
        finally:
            conn.close()

        return func.HttpResponse(
            json.dumps({
                'success': True,
                'rows': enriched_rows,
                'total': len(enriched_rows)
            }),
            mimetype='application/json'
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )
