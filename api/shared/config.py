"""
SAP System Configuration

This file contains the mapping between system identifiers (DEV, QAS, PRD)
and their corresponding SAP application server details.

To add a new system:
1. Add a new entry to the SAP_SYSTEMS dictionary
2. Configure the ashost, sysnr, and description fields

The system dropdown in the frontend will automatically populate with
the systems defined here.
"""

# SAP System Configuration
# Maps system ID to SAP application server details
SAP_SYSTEMS = {
    'DEV': {
        'ashost': 'sap-dev.company.com',      # SAP Development Server hostname/IP
        'sysnr': '00',                         # System number
        'description': 'Development'           # Display name in dropdown
    },
    'QAS': {
        'ashost': 'sap-qas.company.com',      # SAP Quality Server hostname/IP
        'sysnr': '00',                         # System number
        'description': 'Quality'               # Display name in dropdown
    },
    'PRD': {
        'ashost': 'sap-prd.company.com',      # SAP Production Server hostname/IP
        'sysnr': '00',                         # System number
        'description': 'Production'            # Display name in dropdown
    }
}

# Plant to Sales Organization Mapping
# Defines derived values based on plant
PLANT_CONFIG = {
    'US01': {
        'sales_org': 'US01',
        'sold_to': '166',
        'ship_to': 'M0001001E'
    },
    'US65': {
        'sales_org': 'US65',
        'sold_to': '1',
        'ship_to': 'M0001001XI'
    }
}

# Fixed business rule values
FIXED_DIST_CHANNEL = '99'
FIXED_DIVISION = '01'
CONTROLLING_AREA = '1000'
SALES_DOC_TYPE = 'ZMTQ'

# Session configuration
SESSION_EXPIRY_HOURS = 8


def get_sap_system(system_id: str) -> dict:
    """
    Get SAP system configuration by system ID.

    Args:
        system_id: System identifier (DEV, QAS, PRD)

    Returns:
        Dictionary with ashost, sysnr, description or None if not found
    """
    return SAP_SYSTEMS.get(system_id.upper()) if system_id else None


def get_available_systems() -> list:
    """
    Get list of available SAP systems for dropdown.

    Returns:
        List of dicts with id and description
    """
    return [
        {'id': sys_id, 'description': sys_config['description']}
        for sys_id, sys_config in SAP_SYSTEMS.items()
    ]


def get_plant_config(plant: str) -> dict:
    """
    Get plant configuration for derived values.

    Args:
        plant: Plant code

    Returns:
        Dictionary with sales_org, sold_to, ship_to or empty dict if not found
    """
    return PLANT_CONFIG.get(plant.upper(), {}) if plant else {}
