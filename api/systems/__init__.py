"""
Systems Function - Returns available SAP systems for dropdown
"""
import azure.functions as func
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.config import get_available_systems


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Return list of available SAP systems.

    Returns:
    {
        "systems": [
            {"id": "DEV", "description": "Development"},
            {"id": "QAS", "description": "Quality"},
            {"id": "PRD", "description": "Production"}
        ]
    }
    """
    try:
        systems = get_available_systems()

        return func.HttpResponse(
            json.dumps({'systems': systems}),
            mimetype='application/json'
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )
