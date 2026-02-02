"""
SAP Sales Order Creation

Provides functions to create sales orders via BAPI_SALESORDER_CREATEFROMDAT2.

Grouping Logic:
- Rows are grouped by: AUGRU + Sold To + Ship To
- Each group creates ONE sales order with multiple line items
"""
from typing import List, Dict
from collections import defaultdict
from .config import SALES_DOC_TYPE


def create_sales_orders(conn, rows: List[Dict], user_id: str) -> Dict:
    """
    Group rows and create sales orders.

    Grouping key: AUGRU + Sold To + Ship To
    Each group creates one sales order with multiple items.

    Args:
        conn: PyRFC Connection object
        rows: List of enriched row dictionaries
        user_id: SAP user ID (for purchase order reference)

    Returns:
        Dictionary with success status, counts, and updated rows
    """
    # Group rows by AUGRU + Sold To + Ship To
    groups = defaultdict(list)
    for row in rows:
        key = f"{row.get('augru', '')}|{row.get('sold_to', '')}|{row.get('ship_to', '')}"
        groups[key].append(row)

    orders_created = 0
    orders_failed = 0
    processed_rows = []

    for group_key, group_rows in groups.items():
        try:
            # Create sales order for this group
            so_number = call_bapi_salesorder_create(
                conn,
                group_rows,
                user_id
            )

            if so_number and not so_number.startswith('Error'):
                orders_created += 1
                for row in group_rows:
                    row['sales_order'] = so_number
                    row['status'] = 'Created'
            else:
                orders_failed += 1
                for row in group_rows:
                    row['sales_order'] = ''
                    row['status'] = so_number or 'Error: Unknown'

        except Exception as e:
            orders_failed += 1
            for row in group_rows:
                row['sales_order'] = ''
                row['status'] = f'Error: {str(e)}'

        processed_rows.extend(group_rows)

    return {
        'success': True,
        'orders_created': orders_created,
        'orders_failed': orders_failed,
        'groups_processed': len(groups),
        'rows': processed_rows
    }


def call_bapi_salesorder_create(conn, rows: List[Dict], user_id: str) -> str:
    """
    Call BAPI_SALESORDER_CREATEFROMDAT2 to create a sales order.

    Args:
        conn: PyRFC Connection object
        rows: List of rows for this order (same AUGRU/SoldTo/ShipTo)
        user_id: SAP user ID

    Returns:
        Sales order number on success, or "Error: message" on failure
    """
    first_row = rows[0]

    # Format values with proper padding
    dist_channel = str(first_row.get('dist_channel', '99')).zfill(2)
    division = str(first_row.get('division', '01')).zfill(2)
    sold_to = format_partner_number(first_row.get('sold_to', ''))
    ship_to = format_partner_number(first_row.get('ship_to', ''))

    # Build order header
    header = {
        'DOC_TYPE': SALES_DOC_TYPE,
        'SALES_ORG': first_row.get('sales_org', ''),
        'DISTR_CHAN': dist_channel,
        'DIVISION': division,
        'PURCH_NO_C': user_id[:35]  # Truncate to max length
    }

    if first_row.get('augru'):
        header['ORD_REASON'] = first_row['augru']

    # Build header change indicators
    header_x = {
        'UPDATEFLAG': 'I',
        'DOC_TYPE': 'X',
        'SALES_ORG': 'X',
        'DISTR_CHAN': 'X',
        'DIVISION': 'X',
        'PURCH_NO_C': 'X'
    }

    if first_row.get('augru'):
        header_x['ORD_REASON'] = 'X'

    # Build partners table
    partners = [
        {'PARTN_ROLE': 'AG', 'PARTN_NUMB': sold_to},  # Sold-to party
        {'PARTN_ROLE': 'WE', 'PARTN_NUMB': ship_to}   # Ship-to party
    ]

    # Build items and schedules
    items = []
    items_x = []
    schedules = []
    schedules_x = []

    item_num = 0
    for row in rows:
        material = str(row.get('material', '')).strip()
        qty = float(row.get('material_qty', 0))

        if not material or qty <= 0:
            continue

        item_num += 10  # SAP item number increment
        item_str = str(item_num).zfill(6)

        # Item data
        item = {
            'ITM_NUMBER': item_str,
            'MATERIAL': material,
            'PLANT': row.get('plant', ''),
            'TARGET_QTY': qty,
            'REF_1': str(row.get('equipment_id', ''))[:12]  # Equipment reference
        }

        if row.get('batch'):
            item['BATCH'] = row['batch']

        items.append(item)

        # Item change indicators
        item_x = {
            'ITM_NUMBER': item_str,
            'UPDATEFLAG': 'I',
            'MATERIAL': 'X',
            'PLANT': 'X',
            'TARGET_QTY': 'X',
            'REF_1': 'X'
        }

        if row.get('batch'):
            item_x['BATCH'] = 'X'

        items_x.append(item_x)

        # Schedule line
        schedules.append({
            'ITM_NUMBER': item_str,
            'SCHED_LINE': '0001',
            'REQ_QTY': qty
        })

        # Schedule change indicators
        schedules_x.append({
            'ITM_NUMBER': item_str,
            'SCHED_LINE': '0001',
            'UPDATEFLAG': 'I',
            'REQ_QTY': 'X'
        })

    # Call BAPI
    result = conn.call(
        'BAPI_SALESORDER_CREATEFROMDAT2',
        ORDER_HEADER_IN=header,
        ORDER_HEADER_INX=header_x,
        ORDER_PARTNERS=partners,
        ORDER_ITEMS_IN=items,
        ORDER_ITEMS_INX=items_x,
        ORDER_SCHEDULES_IN=schedules,
        ORDER_SCHEDULES_INX=schedules_x
    )

    # Get sales order number
    so_number = result.get('SALESDOCUMENT', '').strip()

    # Check for errors in RETURN table
    returns = result.get('RETURN', [])
    for ret in returns:
        if ret.get('TYPE') in ('E', 'A'):
            return f"Error: {ret.get('MESSAGE', 'Unknown error')}"

    # Commit transaction if successful
    if so_number:
        conn.call('BAPI_TRANSACTION_COMMIT', WAIT='X')
        return so_number

    return 'Error: No sales order number returned'


def format_partner_number(partner: str) -> str:
    """
    Format partner number for SAP.

    Numeric partners are padded to 10 characters.

    Args:
        partner: Partner number (string)

    Returns:
        Formatted partner number
    """
    partner = str(partner).strip()
    if not partner:
        return ''
    if partner.isdigit():
        return partner.zfill(10)
    return partner
