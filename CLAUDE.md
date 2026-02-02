# CLAUDE.md - AI Assistant Guide for SAP Sales Order Agent

This document provides comprehensive guidance for AI assistants working with the SAP Sales Order Agent codebase.

## Project Overview

The **SAP Sales Order Agent** is a web application that enables users to upload equipment data (CSV/Excel), enrich it with SAP master data, and create sales orders in SAP ECC via RFC calls.

### Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Static Web     │────▶│  Azure Functions │────▶│    SAP ECC       │
│   (HTML/JS/CSS)  │     │  (Python)        │     │    (RFC)         │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                         │
        │                         ▼
        │                 ┌──────────────────┐
        └────────────────▶│  Azure Storage   │
                          │  (Table + Blob)  │
                          └──────────────────┘
```

### Technology Stack

| Component         | Technology               | Purpose                    |
|-------------------|--------------------------|----------------------------|
| **Frontend**      | HTML + Vanilla JS + CSS  | Single page application    |
| **Backend**       | Azure Functions (Python) | Serverless API             |
| **SAP Connector** | PyRFC                    | RFC calls to SAP           |
| **Session Store** | Azure Table Storage      | Session management         |
| **File Storage**  | Azure Blob Storage       | Uploaded files             |
| **Hosting**       | Azure Static Web Apps    | Frontend hosting           |

## Project Structure

```
sap-sales-order-agent/
│
├── CLAUDE.md                   # This file - AI assistant guide
├── README.md                   # Project documentation & deployment
│
├── frontend/
│   ├── index.html              # Main single-page application
│   ├── css/
│   │   └── styles.css          # Styling (BEM-like conventions)
│   └── js/
│       └── app.js              # Main application logic
│
├── api/                        # Azure Functions (Python)
│   ├── login/
│   │   ├── __init__.py         # SAP login validation
│   │   └── function.json       # Function configuration
│   │
│   ├── logout/
│   │   ├── __init__.py         # Session cleanup
│   │   └── function.json
│   │
│   ├── session/
│   │   ├── __init__.py         # Session validation endpoint
│   │   └── function.json
│   │
│   ├── upload/
│   │   ├── __init__.py         # File upload + SAP enrichment
│   │   └── function.json
│   │
│   ├── create_orders/
│   │   ├── __init__.py         # Sales order creation
│   │   └── function.json
│   │
│   ├── get_locations/
│   │   ├── __init__.py         # Delivery locations lookup
│   │   └── function.json
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── config.py           # SAP system configuration
│   │   ├── sap_connection.py   # PyRFC connection manager
│   │   ├── sap_equipment.py    # Equipment BAPI calls
│   │   ├── sap_sales_order.py  # Sales order BAPI calls
│   │   └── session_store.py    # Azure Table session management
│   │
│   ├── requirements.txt        # Python dependencies
│   ├── host.json               # Azure Functions host config
│   └── local.settings.json     # Local development settings
│
└── .gitignore
```

## Key Files and Their Purposes

### Frontend (`/frontend`)

| File | Purpose |
|------|---------|
| `index.html` | Single-page app with login, upload, data table, and order creation UI |
| `css/styles.css` | All styling - uses utility classes and component-based organization |
| `js/app.js` | Main JS - handles auth, file upload, table rendering, API calls |

### Backend (`/api`)

| File | Purpose |
|------|---------|
| `shared/config.py` | **Critical** - SAP system mappings (DEV/QAS/PRD), plant configs, business rules |
| `shared/sap_connection.py` | PyRFC connection factory with multi-system support |
| `shared/sap_equipment.py` | BAPI_EQUI_DETAILS and Z_MATREQ_COST_CENTER calls |
| `shared/sap_sales_order.py` | BAPI_SALESORDER_CREATEFROMDAT2 with grouping logic |
| `shared/session_store.py` | Azure Table Storage session CRUD with encryption |
| `login/__init__.py` | Validates SAP credentials, creates encrypted session |
| `upload/__init__.py` | Parses CSV/Excel, enriches data via SAP BAPIs |
| `create_orders/__init__.py` | Groups rows and creates sales orders |

## Development Workflows

### Local Development Setup

```bash
# 1. Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# 2. Install Python dependencies
cd api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure local settings
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your SAP and Azure credentials

# 4. Start Azure Functions locally
func start

# 5. Serve frontend (separate terminal)
cd frontend
python -m http.server 8080
# Or use VS Code Live Server extension
```

### Running the Application

1. Open `http://localhost:8080` in browser
2. Select SAP system (DEV/QAS/PRD) from dropdown
3. Enter SAP credentials
4. Upload CSV/Excel file with equipment data
5. Review enriched data in table
6. Select rows and create sales orders

### Testing

```bash
# Test SAP connection
cd api
python -c "from shared.sap_connection import SAPConnectionManager; print('OK')"

# Test file parsing
python -c "import pandas as pd; pd.read_csv('test.csv'); print('OK')"

# Run Azure Functions locally with debugging
func start --verbose
```

## Code Conventions

### Python (Backend)

- **Style**: PEP 8 compliant
- **Type hints**: Use for function parameters and return types
- **Docstrings**: Required for all public functions
- **Error handling**: Always return JSON with `error` key on failure
- **SAP calls**: Wrap in try/except, close connections in finally block

```python
# Example pattern
def my_function(param: str) -> Dict:
    """Brief description of function."""
    try:
        # implementation
        return {'success': True, 'data': result}
    except Exception as e:
        return {'error': str(e)}
```

### JavaScript (Frontend)

- **Style**: ES6+ (const/let, arrow functions, template literals)
- **State**: Single global `state` object for app state
- **DOM**: Use `getElementById` / `querySelector`
- **API calls**: Always use `fetch` with proper error handling
- **HTML escaping**: Always use `escapeHtml()` for user data

```javascript
// Example pattern
async function apiCall() {
    try {
        const response = await fetch(`${API_BASE}/endpoint`, {
            headers: { 'X-Session-Id': state.sessionId }
        });
        if (!response.ok) throw new Error('Request failed');
        return await response.json();
    } catch (err) {
        showToast(err.message, 'error');
    }
}
```

### CSS

- **Organization**: Reset → Base → Components → Utilities
- **Naming**: Descriptive class names (`.upload-box`, `.btn-primary`)
- **Responsive**: Mobile-first with `@media (max-width: 768px)` breakpoints

## SAP Integration Details

### BAPIs Used

| BAPI | Purpose | Input | Output |
|------|---------|-------|--------|
| `BAPI_EQUI_DETAILS` | Get equipment master data | Equipment ID (18 chars, padded) | Plant, Cost Center, Company Code |
| `Z_MATREQ_COST_CENTER` | Get cost center details | Cost Center, Sales Org | AUGRU (Order Reason) |
| `BAPI_SALESORDER_CREATEFROMDAT2` | Create sales order | Header, Partners, Items, Schedules | Sales Order Number |
| `BAPI_TRANSACTION_COMMIT` | Commit transaction | WAIT='X' | - |

### Sales Order Grouping Logic

Rows are grouped by: `AUGRU + Sold To + Ship To`

Each group creates ONE sales order with multiple line items.

### Business Rules (in `config.py`)

- **Plant → Sales Org mapping**: US01 → US01, US65 → US65
- **Fixed values**: Distribution Channel = '99', Division = '01'
- **Partner derivation**: Based on plant configuration

## Configuration

### SAP System Configuration (`api/shared/config.py`)

```python
SAP_SYSTEMS = {
    'DEV': {
        'ashost': 'sap-dev.company.com',
        'sysnr': '00',
        'description': 'Development'
    },
    'QAS': {
        'ashost': 'sap-qas.company.com',
        'sysnr': '00',
        'description': 'Quality'
    },
    'PRD': {
        'ashost': 'sap-prd.company.com',
        'sysnr': '00',
        'description': 'Production'
    }
}
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AzureWebJobsStorage` | Azure Storage connection string | Yes |
| `ENCRYPTION_KEY` | Fernet key for password encryption | Yes |
| `SAP_LANG` | SAP language code (default: EN) | No |

## Common Tasks

### Adding a New SAP System

1. Edit `api/shared/config.py` - add to `SAP_SYSTEMS` dict
2. No frontend changes needed (systems loaded dynamically)

### Adding a New Plant Configuration

1. Edit `api/shared/config.py` - add to `PLANT_CONFIG` dict
2. Define: sales_org, sold_to, ship_to mappings

### Modifying Sales Order Creation Logic

1. Edit `api/shared/sap_sales_order.py`
2. Key functions: `create_sales_orders()`, `call_bapi_salesorder_create()`
3. Grouping logic is in `create_sales_orders()`

### Adding New File Columns

1. Edit `api/upload/__init__.py` - update `required_cols` list
2. Edit `api/shared/sap_equipment.py` - handle new fields in enrichment
3. Edit `frontend/js/app.js` - update table headers and row rendering

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Login fails | Wrong SAP credentials | Check user/password/client |
| Login fails | Wrong system selected | Verify SAP system dropdown |
| Session expired | 8-hour timeout | Re-login |
| Upload fails | Invalid file format | Use CSV or XLSX only |
| Equipment not found | Invalid equipment ID | Check ID exists in SAP |
| Order creation fails | Missing required fields | Ensure all enrichment succeeded |

### Debug Mode

```bash
# Enable verbose logging for Azure Functions
func start --verbose

# Check browser console for frontend errors
# Press F12 → Console tab
```

## Security Considerations

- **Password encryption**: User passwords encrypted with Fernet before session storage
- **Session expiry**: 8-hour maximum session lifetime
- **No credential storage**: Passwords never stored in plain text
- **Input validation**: All user inputs sanitized before SAP calls
- **HTTPS**: Always use HTTPS in production

## Important Notes for AI Assistants

1. **Never hardcode credentials** - Always use environment variables
2. **Test SAP connections** - Always validate before creating orders
3. **Handle errors gracefully** - Return meaningful error messages
4. **Maintain session security** - Always validate session before API calls
5. **Escape HTML** - Always escape user data in frontend
6. **Close SAP connections** - Use try/finally to ensure cleanup
7. **Commit transactions** - Always call BAPI_TRANSACTION_COMMIT after successful order creation
