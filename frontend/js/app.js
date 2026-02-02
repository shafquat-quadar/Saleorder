// ============================================================================
// SAP Sales Order Agent - Main Application
// ============================================================================

// API Base URL - Change for production deployment
const API_BASE = '/api';  // Azure Functions API base URL

// State
let state = {
    isLoggedIn: false,
    sessionId: null,
    sapUser: null,
    sapSystem: null,
    selectedFile: null,
    enrichedData: [],
    selectedRows: new Set(),
    availableSystems: []
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadAvailableSystems();
    checkSession();
    setupEventListeners();
});

function setupEventListeners() {
    // Login
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

    // File Upload
    const uploadBox = document.getElementById('upload-box');
    const fileInput = document.getElementById('file-input');

    uploadBox.addEventListener('click', () => fileInput.click());
    uploadBox.addEventListener('dragover', handleDragOver);
    uploadBox.addEventListener('dragleave', handleDragLeave);
    uploadBox.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    document.getElementById('clear-file').addEventListener('click', clearFile);
    document.getElementById('process-btn').addEventListener('click', processFile);

    // Table Actions
    document.getElementById('header-checkbox').addEventListener('change', toggleAllRows);
    document.getElementById('select-all-btn').addEventListener('click', selectAllRows);
    document.getElementById('deselect-all-btn').addEventListener('click', deselectAllRows);
    document.getElementById('create-orders-btn').addEventListener('click', createSalesOrders);
}

// ============================================================================
// System Configuration
// ============================================================================

async function loadAvailableSystems() {
    try {
        const response = await fetch(`${API_BASE}/systems`);
        if (response.ok) {
            const data = await response.json();
            state.availableSystems = data.systems || [];
            populateSystemDropdown();
        } else {
            // Fallback to default systems if API not available
            state.availableSystems = [
                { id: 'DEV', description: 'Development' },
                { id: 'QAS', description: 'Quality' },
                { id: 'PRD', description: 'Production' }
            ];
            populateSystemDropdown();
        }
    } catch (e) {
        console.error('Failed to load systems:', e);
        // Fallback to default systems
        state.availableSystems = [
            { id: 'DEV', description: 'Development' },
            { id: 'QAS', description: 'Quality' },
            { id: 'PRD', description: 'Production' }
        ];
        populateSystemDropdown();
    }
}

function populateSystemDropdown() {
    const select = document.getElementById('sap-system');
    select.innerHTML = '<option value="">-- Select System --</option>';

    state.availableSystems.forEach(system => {
        const option = document.createElement('option');
        option.value = system.id;
        option.textContent = `${system.id} - ${system.description}`;
        option.dataset.system = system.id;
        select.appendChild(option);
    });
}

function getSystemBadgeClass(systemId) {
    switch (systemId?.toUpperCase()) {
        case 'DEV':
            return 'dev';
        case 'QAS':
            return 'qas';
        case 'PRD':
            return 'prd';
        default:
            return '';
    }
}

// ============================================================================
// Session Management
// ============================================================================

async function checkSession() {
    const sessionId = localStorage.getItem('sessionId');
    const savedSystem = localStorage.getItem('sapSystem');

    if (sessionId) {
        try {
            const response = await fetch(`${API_BASE}/session/validate`, {
                headers: { 'X-Session-Id': sessionId }
            });
            if (response.ok) {
                const data = await response.json();
                state.isLoggedIn = true;
                state.sessionId = sessionId;
                state.sapUser = data.user;
                state.sapSystem = data.system || savedSystem;
                showApp();
                return;
            }
        } catch (e) {
            console.error('Session validation failed:', e);
        }
        localStorage.removeItem('sessionId');
        localStorage.removeItem('sapSystem');
    }
    showLogin();
}

function showLogin() {
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('app-section').classList.add('hidden');
    document.getElementById('user-info').classList.add('hidden');
}

function showApp() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('app-section').classList.remove('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    document.getElementById('username-display').textContent = state.sapUser;

    // Display system badge
    const systemBadge = document.getElementById('system-display');
    systemBadge.textContent = state.sapSystem;
    systemBadge.className = `system-badge ${getSystemBadgeClass(state.sapSystem)}`;
}

// ============================================================================
// Authentication
// ============================================================================

async function handleLogin(e) {
    e.preventDefault();

    const system = document.getElementById('sap-system').value;
    const user = document.getElementById('sap-user').value.trim();
    const password = document.getElementById('sap-password').value;
    const client = document.getElementById('sap-client').value.trim();

    const loginBtn = document.getElementById('login-btn');
    const errorDiv = document.getElementById('login-error');

    // Validate system selection
    if (!system) {
        errorDiv.textContent = 'Please select a SAP system.';
        errorDiv.classList.remove('hidden');
        return;
    }

    setButtonLoading(loginBtn, true);
    errorDiv.classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ system, user, password, client })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            state.isLoggedIn = true;
            state.sessionId = data.sessionId;
            state.sapUser = user;
            state.sapSystem = system;
            localStorage.setItem('sessionId', data.sessionId);
            localStorage.setItem('sapSystem', system);
            showApp();
            showToast(`Login successful (${system})`, 'success');
        } else {
            errorDiv.textContent = data.error || 'Login failed. Check credentials.';
            errorDiv.classList.remove('hidden');
        }
    } catch (err) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('hidden');
    } finally {
        setButtonLoading(loginBtn, false);
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            headers: { 'X-Session-Id': state.sessionId }
        });
    } catch (e) {
        console.error('Logout error:', e);
    }

    localStorage.removeItem('sessionId');
    localStorage.removeItem('sapSystem');
    state = {
        isLoggedIn: false,
        sessionId: null,
        sapUser: null,
        sapSystem: null,
        selectedFile: null,
        enrichedData: [],
        selectedRows: new Set(),
        availableSystems: state.availableSystems  // Keep the systems list
    };

    showLogin();
    showToast('Logged out', 'info');
}

// ============================================================================
// File Upload
// ============================================================================

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        selectFile(files[0]);
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        selectFile(e.target.files[0]);
    }
}

function selectFile(file) {
    const validTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    if (!validTypes.includes(file.type) &&
        !file.name.endsWith('.csv') &&
        !file.name.endsWith('.xlsx') &&
        !file.name.endsWith('.xls')) {
        showToast('Invalid file type. Please upload CSV or Excel file.', 'error');
        return;
    }

    state.selectedFile = file;
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-info').classList.remove('hidden');
    document.getElementById('process-btn').classList.remove('hidden');
}

function clearFile() {
    state.selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-info').classList.add('hidden');
    document.getElementById('process-btn').classList.add('hidden');
    document.getElementById('data-section').classList.add('hidden');
}

// ============================================================================
// File Processing
// ============================================================================

async function processFile() {
    if (!state.selectedFile) return;

    const processBtn = document.getElementById('process-btn');
    const progressSection = document.getElementById('progress-section');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    setButtonLoading(processBtn, true);
    progressSection.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading file...';

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', state.selectedFile);

        progressFill.style.width = '20%';
        progressText.textContent = 'Parsing file...';

        // Upload and process
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            headers: { 'X-Session-Id': state.sessionId },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || error.error || 'Upload failed');
        }

        progressFill.style.width = '50%';
        progressText.textContent = 'Enriching data from SAP...';

        const data = await response.json();

        progressFill.style.width = '100%';
        progressText.textContent = 'Complete!';

        state.enrichedData = data.rows;
        state.selectedRows = new Set();

        renderDataTable();
        updateSummary();

        document.getElementById('data-section').classList.remove('hidden');

        showToast(`Processed ${data.rows.length} rows successfully`, 'success');

    } catch (err) {
        showToast(err.message || 'Processing failed', 'error');
    } finally {
        setButtonLoading(processBtn, false);
        setTimeout(() => {
            progressSection.classList.add('hidden');
        }, 1000);
    }
}

// ============================================================================
// Data Table
// ============================================================================

function renderDataTable() {
    const tbody = document.getElementById('data-table-body');
    tbody.innerHTML = '';

    state.enrichedData.forEach((row, index) => {
        const tr = document.createElement('tr');
        tr.dataset.index = index;

        if (state.selectedRows.has(index)) {
            tr.classList.add('selected');
        }

        if (row.status === 'Created') {
            tr.classList.add('success');
        } else if (row.status && row.status.startsWith('Error')) {
            tr.classList.add('error');
        }

        tr.innerHTML = `
            <td><input type="checkbox" class="row-checkbox" data-index="${index}"
                ${state.selectedRows.has(index) ? 'checked' : ''}
                ${row.sales_order ? 'disabled' : ''}></td>
            <td>${row.row_number || index + 1}</td>
            <td>${escapeHtml(row.equipment_id)}</td>
            <td>${escapeHtml(row.material)}</td>
            <td>${row.material_qty}</td>
            <td>${escapeHtml(row.plant || '')}</td>
            <td>${escapeHtml(row.sales_org || '')}</td>
            <td>${escapeHtml(row.dist_channel || '')}</td>
            <td>${escapeHtml(row.division || '')}</td>
            <td>${escapeHtml(row.cost_center || '')}</td>
            <td>${escapeHtml(row.augru || '')}</td>
            <td>${escapeHtml(row.sold_to || '')}</td>
            <td>${escapeHtml(row.ship_to || '')}</td>
            <td>${escapeHtml(row.batch || '')}</td>
            <td class="${getStatusClass(row.status)}">${escapeHtml(row.status || 'Ready')}</td>
            <td class="so-number">${escapeHtml(row.sales_order || '')}</td>
        `;

        tbody.appendChild(tr);
    });

    // Add checkbox listeners
    document.querySelectorAll('.row-checkbox').forEach(cb => {
        cb.addEventListener('change', handleRowSelect);
    });
}

function handleRowSelect(e) {
    const index = parseInt(e.target.dataset.index);

    if (e.target.checked) {
        state.selectedRows.add(index);
        e.target.closest('tr').classList.add('selected');
    } else {
        state.selectedRows.delete(index);
        e.target.closest('tr').classList.remove('selected');
    }

    updateSelectionCount();
}

function toggleAllRows(e) {
    const checked = e.target.checked;

    state.enrichedData.forEach((row, index) => {
        if (!row.sales_order) {  // Only toggle rows without SO
            if (checked) {
                state.selectedRows.add(index);
            } else {
                state.selectedRows.delete(index);
            }
        }
    });

    renderDataTable();
    updateSelectionCount();
}

function selectAllRows() {
    state.enrichedData.forEach((row, index) => {
        if (!row.sales_order) {
            state.selectedRows.add(index);
        }
    });
    document.getElementById('header-checkbox').checked = true;
    renderDataTable();
    updateSelectionCount();
}

function deselectAllRows() {
    state.selectedRows.clear();
    document.getElementById('header-checkbox').checked = false;
    renderDataTable();
    updateSelectionCount();
}

function updateSelectionCount() {
    const count = state.selectedRows.size;
    document.getElementById('selection-count').textContent = `${count} rows selected`;
    document.getElementById('create-orders-btn').disabled = count === 0;
}

function updateSummary() {
    const total = state.enrichedData.length;
    const success = state.enrichedData.filter(r => r.sales_order).length;
    const error = state.enrichedData.filter(r => r.status && r.status.startsWith('Error')).length;

    // Calculate groups
    const groups = new Set();
    state.enrichedData.forEach(row => {
        const key = `${row.augru}|${row.sold_to}|${row.ship_to}`;
        groups.add(key);
    });

    document.getElementById('total-rows').textContent = total;
    document.getElementById('total-groups').textContent = groups.size;
    document.getElementById('success-count').textContent = success;
    document.getElementById('error-count').textContent = error;
}

function getStatusClass(status) {
    if (!status || status === 'Ready') return 'status-pending';
    if (status === 'Created') return 'status-success';
    return 'status-error';
}

// ============================================================================
// Sales Order Creation
// ============================================================================

async function createSalesOrders() {
    if (state.selectedRows.size === 0) return;

    const createBtn = document.getElementById('create-orders-btn');
    setButtonLoading(createBtn, true);

    const selectedIndices = Array.from(state.selectedRows);
    const rowsToProcess = selectedIndices.map(i => state.enrichedData[i]);

    try {
        const response = await fetch(`${API_BASE}/create_orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-Id': state.sessionId
            },
            body: JSON.stringify({ rows: rowsToProcess })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || error.error || 'Failed to create orders');
        }

        const result = await response.json();

        // Update state with results
        result.rows.forEach(updatedRow => {
            const index = state.enrichedData.findIndex(
                r => r.row_number === updatedRow.row_number
            );
            if (index !== -1) {
                state.enrichedData[index] = updatedRow;
            }
        });

        state.selectedRows.clear();
        renderDataTable();
        updateSummary();
        updateSelectionCount();

        showToast(
            `Created ${result.orders_created} orders, ${result.orders_failed} failed`,
            result.orders_failed > 0 ? 'error' : 'success'
        );

    } catch (err) {
        showToast(err.message || 'Failed to create orders', 'error');
    } finally {
        setButtonLoading(createBtn, false);
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

function setButtonLoading(button, loading) {
    const textSpan = button.querySelector('.btn-text');
    const loaderSpan = button.querySelector('.btn-loader');

    if (loading) {
        button.disabled = true;
        if (textSpan) textSpan.classList.add('hidden');
        if (loaderSpan) loaderSpan.classList.remove('hidden');
    } else {
        button.disabled = false;
        if (textSpan) textSpan.classList.remove('hidden');
        if (loaderSpan) loaderSpan.classList.add('hidden');
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
