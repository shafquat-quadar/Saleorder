"""
SAP Equipment Enrichment - BAPI calls

Provides functions to enrich equipment data with SAP master data:
- BAPI_EQUI_DETAILS: Get equipment master data (plant, cost center, company code)
- Z_MATREQ_COST_CENTER: Get cost center details (AUGRU/order reason)
"""
from typing import List, Dict
from .config import (
    PLANT_CONFIG,
    FIXED_DIST_CHANNEL,
    FIXED_DIVISION,
    CONTROLLING_AREA,
    get_plant_config
)


def enrich_equipment_data(conn, rows: List[Dict]) -> List[Dict]:
    """
    Enrich rows with SAP data.

    For each row:
    1. Call BAPI_EQUI_DETAILS to get plant, cost center, company code
    2. Derive sales org, sold to, ship to from plant configuration
    3. Call Z_MATREQ_COST_CENTER to get AUGRU (order reason)

    Args:
        conn: PyRFC Connection object
        rows: List of row dictionaries with equipment_id, material, material_qty

    Returns:
        List of enriched row dictionaries
    """
    enriched = []

    for row in rows:
        equipment_id = str(row.get('equipment_id', '')).strip()

        if not equipment_id:
            row['status'] = 'Error: No Equipment ID'
            enriched.append(row)
            continue

        try:
            # Call BAPI_EQUI_DETAILS
            equip_data = call_bapi_equi_details(conn, equipment_id)

            if equip_data.get('error'):
                row['status'] = f"Error: {equip_data['error']}"
                enriched.append(row)
                continue

            # Populate from BAPI response
            plant = equip_data.get('plant', '')
            cost_center = equip_data.get('cost_center', '')
            company_code = equip_data.get('company_code', '')

            row['plant'] = plant
            row['cost_center'] = cost_center
            row['company_code'] = company_code

            # Derive values from plant configuration
            plant_upper = plant.upper() if plant else ''
            config = get_plant_config(plant_upper)

            row['sales_org'] = config.get('sales_org', plant_upper)
            row['dist_channel'] = FIXED_DIST_CHANNEL
            row['division'] = FIXED_DIVISION
            row['sold_to'] = config.get('sold_to', '')
            row['ship_to'] = config.get('ship_to', '')

            # Call Z_MATREQ_COST_CENTER for AUGRU
            if cost_center and row['sales_org']:
                cc_data = call_z_matreq_cost_center(
                    conn, cost_center, row['sales_org']
                )
                row['augru'] = cc_data.get('augru', '')
                row['cost_center_text'] = cc_data.get('ltext', '')
            else:
                row['augru'] = ''
                row['cost_center_text'] = ''

            row['status'] = 'Ready'

        except Exception as e:
            row['status'] = f'Error: {str(e)}'

        enriched.append(row)

    return enriched


def call_bapi_equi_details(conn, equipment_id: str) -> Dict:
    """
    Call BAPI_EQUI_DETAILS to get equipment master data.

    Args:
        conn: PyRFC Connection object
        equipment_id: Equipment ID (will be padded to 18 chars)

    Returns:
        Dictionary with plant, cost_center, company_code or error
    """
    # Pad equipment ID to 18 characters (SAP requirement)
    equip_padded = equipment_id.zfill(18)

    result = conn.call('BAPI_EQUI_DETAILS', EQUIPMENT=equip_padded)

    # Check for errors in RETURN structure
    ret = result.get('RETURN', {})
    if ret.get('TYPE') in ('E', 'A'):
        return {'error': ret.get('MESSAGE', 'Unknown error')}

    # Extract data from DATA_GENERAL_EXP structure
    data_general = result.get('DATA_GENERAL_EXP', {})

    # Plant can be in PLANPLANT or MAINTPLANT
    plant = data_general.get('PLANPLANT', '') or data_general.get('MAINTPLANT', '')
    cost_center = data_general.get('COSTCENTER', '')
    company_code = data_general.get('COMPANYCODE', '') or data_general.get('BUKRS', '')

    return {
        'plant': plant.strip(),
        'cost_center': cost_center.strip(),
        'company_code': company_code.strip()
    }


def call_z_matreq_cost_center(conn, cost_center: str, sales_org: str) -> Dict:
    """
    Call Z_MATREQ_COST_CENTER to get cost center details and AUGRU.

    Args:
        conn: PyRFC Connection object
        cost_center: Cost center (will be padded to 10 chars)
        sales_org: Sales organization

    Returns:
        Dictionary with augru, ltext (description)
    """
    # Pad cost center to 10 characters
    cc_padded = cost_center.zfill(10)

    try:
        result = conn.call(
            'Z_MATREQ_COST_CENTER',
            P_COSTCENTER=cc_padded,
            P_SALESORG=sales_org,
            P_DIST_CHANNEL=FIXED_DIST_CHANNEL,
            P_DIVISION=FIXED_DIVISION,
            P_CONTROLLING_AREA=CONTROLLING_AREA,
            P_LANGUAGE='E'
        )

        table = result.get('T_COST_CENTER', [])
        if table:
            first_row = table[0]
            return {
                'augru': first_row.get('AUG', '').strip(),
                'ltext': first_row.get('LTEXT', '').strip()
            }
    except Exception:
        pass

    return {'augru': '', 'ltext': ''}
