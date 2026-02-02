# SAP Sales Order Agent

A web application for creating SAP Sales Orders from equipment data files. Users can upload CSV/Excel files, enrich data with SAP master data, and create sales orders in bulk.

## Architecture Overview

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

## Features

- **Multi-System Support**: Connect to DEV, QAS, or PRD SAP systems
- **File Upload**: Support for CSV and Excel (.xlsx, .xls) files
- **Data Enrichment**: Automatic lookup of equipment master data from SAP
- **Bulk Order Creation**: Create multiple sales orders with proper grouping
- **Real-time Status**: Track order creation progress and results

## Prerequisites

### For Local Development
- Python 3.9 or higher
- Node.js 16+ (for Azure Functions Core Tools)
- SAP RFC SDK (for PyRFC)
- Azure Storage Emulator or Azurite

### For Production
- Azure Subscription
- Azure Functions (Python runtime)
- Azure Static Web Apps
- Azure Storage Account
- Network connectivity to SAP systems

---

# Local Development Deployment

## Step 1: Install Required Tools

### 1.1 Install Azure Functions Core Tools

```bash
# Windows (using npm)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# macOS (using Homebrew)
brew tap azure/functions
brew install azure-functions-core-tools@4

# Linux (Ubuntu/Debian)
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

### 1.2 Install Azurite (Local Azure Storage Emulator)

```bash
npm install -g azurite
```

### 1.3 Install SAP NW RFC SDK

Download the SAP NW RFC SDK from SAP Support Portal and follow PyRFC installation instructions:
- https://github.com/SAP/PyRFC#installation

## Step 2: Clone and Configure the Project

### 2.1 Clone the Repository

```bash
git clone <repository-url>
cd sap-sales-order-agent
```

### 2.2 Set Up Python Virtual Environment

```bash
cd api
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2.3 Configure Local Settings

Create `api/local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ENCRYPTION_KEY": "your-fernet-key-here",
    "SAP_LANG": "EN"
  },
  "Host": {
    "CORS": "*",
    "CORSCredentials": false
  }
}
```

### 2.4 Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and replace `your-fernet-key-here` in `local.settings.json`.

### 2.5 Configure SAP Systems

Edit `api/shared/config.py` to configure your SAP systems:

```python
SAP_SYSTEMS = {
    'DEV': {
        'ashost': 'your-sap-dev-server.com',
        'sysnr': '00',
        'description': 'Development'
    },
    'QAS': {
        'ashost': 'your-sap-qas-server.com',
        'sysnr': '00',
        'description': 'Quality'
    },
    'PRD': {
        'ashost': 'your-sap-prd-server.com',
        'sysnr': '00',
        'description': 'Production'
    }
}
```

## Step 3: Start Local Services

### 3.1 Start Azurite (Storage Emulator)

Open a new terminal:

```bash
azurite --silent --location ./azurite --debug ./azurite/debug.log
```

### 3.2 Start Azure Functions

In the `api` directory with virtual environment activated:

```bash
func start
```

You should see output like:
```
Functions:
    login: [POST] http://localhost:7071/api/login
    logout: [POST] http://localhost:7071/api/logout
    upload: [POST] http://localhost:7071/api/upload
    create_orders: [POST] http://localhost:7071/api/create_orders
    ...
```

### 3.3 Serve Frontend

Open another terminal and serve the frontend:

```bash
cd frontend

# Option 1: Python HTTP Server
python -m http.server 8080

# Option 2: Node.js HTTP Server
npx http-server -p 8080

# Option 3: VS Code Live Server Extension
# Right-click index.html → "Open with Live Server"
```

### 3.4 Update API Base URL for Local Development

Edit `frontend/js/app.js` and update the API_BASE:

```javascript
const API_BASE = 'http://localhost:7071/api';  // Local development
```

## Step 4: Test the Application

1. Open `http://localhost:8080` in your browser
2. Select a SAP system from the dropdown (DEV/QAS/PRD)
3. Enter your SAP credentials
4. Upload a test CSV file with columns: `equipment_id`, `material`, `material_qty`
5. Verify data enrichment and create test orders

### Sample Test Data (test.csv)

```csv
equipment_id,material,material_qty
10000001,MAT001,5
10000002,MAT002,10
10000003,MAT001,3
```

---

# Production Deployment

## Step 1: Azure Resources Setup

### 1.1 Create Resource Group

```bash
az login
az group create --name rg-sap-sales-order --location eastus
```

### 1.2 Create Storage Account

```bash
az storage account create \
  --name stsapsalesorder \
  --resource-group rg-sap-sales-order \
  --location eastus \
  --sku Standard_LRS
```

### 1.3 Create Azure Functions App

```bash
# Create App Service Plan (or use Consumption plan)
az functionapp plan create \
  --name asp-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --location eastus \
  --sku B1 \
  --is-linux

# Create Function App
az functionapp create \
  --name func-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --storage-account stsapsalesorder \
  --plan asp-sap-sales-order \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4
```

### 1.4 Create Static Web App

```bash
az staticwebapp create \
  --name swa-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --location eastus2
```

## Step 2: Configure Application Settings

### 2.1 Generate Production Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2.2 Set Function App Settings

```bash
# Get Storage Connection String
STORAGE_CONN=$(az storage account show-connection-string \
  --name stsapsalesorder \
  --resource-group rg-sap-sales-order \
  --query connectionString -o tsv)

# Set Application Settings
az functionapp config appsettings set \
  --name func-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --settings \
    "AzureWebJobsStorage=$STORAGE_CONN" \
    "ENCRYPTION_KEY=your-production-fernet-key" \
    "SAP_LANG=EN"
```

### 2.3 Configure CORS

```bash
az functionapp cors add \
  --name func-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --allowed-origins "https://your-static-webapp-url.azurestaticapps.net"
```

## Step 3: Deploy Backend (Azure Functions)

### 3.1 Deploy Using Azure Functions Core Tools

```bash
cd api
func azure functionapp publish func-sap-sales-order
```

### 3.2 Alternative: Deploy Using VS Code

1. Install Azure Functions extension
2. Sign in to Azure
3. Right-click on `api` folder → "Deploy to Function App"
4. Select your function app

### 3.3 Verify Deployment

```bash
az functionapp function list \
  --name func-sap-sales-order \
  --resource-group rg-sap-sales-order
```

## Step 4: Deploy Frontend (Static Web App)

### 4.1 Update API Base URL

Edit `frontend/js/app.js`:

```javascript
const API_BASE = 'https://func-sap-sales-order.azurewebsites.net/api';
```

### 4.2 Deploy Using Azure CLI

```bash
cd frontend
az staticwebapp upload \
  --name swa-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --source .
```

### 4.3 Alternative: Deploy via GitHub Actions

Create `.github/workflows/azure-static-web-apps.yml`:

```yaml
name: Deploy Static Web App

on:
  push:
    branches: [main]
    paths: ['frontend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "/frontend"
          output_location: ""
```

## Step 5: Network Configuration (SAP Connectivity)

### 5.1 VNet Integration (Required for SAP Access)

```bash
# Create VNet
az network vnet create \
  --name vnet-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --address-prefix 10.0.0.0/16 \
  --subnet-name subnet-functions \
  --subnet-prefix 10.0.1.0/24

# Integrate Function App with VNet
az functionapp vnet-integration add \
  --name func-sap-sales-order \
  --resource-group rg-sap-sales-order \
  --vnet vnet-sap-sales-order \
  --subnet subnet-functions
```

### 5.2 Configure NSG Rules (if needed)

Ensure network security group allows outbound traffic to SAP servers on RFC ports (typically 3300-3399).

## Step 6: Post-Deployment Verification

### 6.1 Test Backend Health

```bash
curl https://func-sap-sales-order.azurewebsites.net/api/health
```

### 6.2 Test Frontend

Open the Static Web App URL in browser and verify:
1. Login page loads
2. System dropdown shows DEV/QAS/PRD options
3. Login with SAP credentials works
4. File upload and enrichment works
5. Order creation works

### 6.3 Monitor Logs

```bash
az functionapp log tail \
  --name func-sap-sales-order \
  --resource-group rg-sap-sales-order
```

---

# Configuration Reference

## SAP System Configuration

The SAP system configuration is maintained in `api/shared/config.py`:

```python
SAP_SYSTEMS = {
    'DEV': {
        'ashost': 'sap-dev-server.company.com',
        'sysnr': '00',
        'description': 'Development'
    },
    'QAS': {
        'ashost': 'sap-qas-server.company.com',
        'sysnr': '00',
        'description': 'Quality'
    },
    'PRD': {
        'ashost': 'sap-prd-server.company.com',
        'sysnr': '00',
        'description': 'Production'
    }
}
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AzureWebJobsStorage` | Azure Storage connection string | Yes | - |
| `ENCRYPTION_KEY` | Fernet encryption key for password storage | Yes | - |
| `SAP_LANG` | SAP language code | No | EN |

## File Format Requirements

### Input CSV/Excel Columns

| Column | Required | Description |
|--------|----------|-------------|
| `equipment_id` | Yes | SAP Equipment ID |
| `material` | Yes | Material number |
| `material_qty` | Yes | Quantity |
| `batch` | No | Batch number |

---

# Troubleshooting

## Common Issues

### PyRFC Installation Fails
- Ensure SAP NW RFC SDK is installed
- Set `SAPNWRFC_HOME` environment variable
- See: https://github.com/SAP/PyRFC#installation

### Connection to SAP Fails
- Verify network connectivity to SAP server
- Check firewall rules for RFC ports
- Verify SAP credentials are correct

### Session Expired Errors
- Sessions expire after 8 hours
- Re-login to create new session

### CORS Errors in Browser
- Ensure CORS is configured on Function App
- Check allowed origins include your frontend URL

---

# Security Best Practices

1. **Never commit `local.settings.json`** - It contains sensitive credentials
2. **Use managed identities** where possible
3. **Rotate encryption keys** periodically
4. **Enable Azure AD authentication** for production
5. **Use VNet integration** for SAP connectivity
6. **Enable HTTPS only** on Function App
7. **Implement rate limiting** for login endpoint

---

# Support

For issues and questions:
- Check the troubleshooting section above
- Review Azure Functions logs
- Check SAP RFC connection logs
