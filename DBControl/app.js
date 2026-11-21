/* ============================================================
   Adhikar Saathi | DBControl & phpMyAdmin-Style Client Logic
   ============================================================ */

let sessionToken = localStorage.getItem('adhikar_user_token') || '';
let adminPassword = localStorage.getItem('adhikar_admin_pass') || '';
let currentUser = JSON.parse(localStorage.getItem('adhikar_user_data') || 'null');

let currentView = localStorage.getItem('adhikar_admin_current_view') || 'browse'; // 'structure' | 'browse' | 'sql' | 'insert'
let currentTable = localStorage.getItem('adhikar_admin_current_table') || 'users';
let currentTableData = null;
let currentTableSchema = [];
let tableRowsLimit = 25;
let tableRowsOffset = 0;
let tableSearchQuery = '';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  if (sessionToken || adminPassword) {
    const valid = await checkAuthValidity();
    if (valid) {
      hideAuthOverlay();
      initApp();
      return;
    }
  }
  showAuthOverlay('master');
});

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionToken) {
    headers['X-Admin-Token'] = sessionToken;
  }
  if (adminPassword) {
    headers['X-Admin-Password'] = adminPassword;
  }
  return headers;
}

async function checkAuthValidity() {
  try {
    const res = await fetch('/api/admin/verify-auth', {
      headers: getAuthHeaders()
    });
    return res.status === 200;
  } catch (e) {
    return false;
  }
}

/* ============================================================
   Auth (Registration, Login, Master Password)
   ============================================================ */

function showAuthOverlay(mode = 'login') {
  document.getElementById('auth-overlay').style.display = 'flex';
  switchAuthTab(mode);
}

function hideAuthOverlay() {
  document.getElementById('auth-overlay').style.display = 'none';
}

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });

  document.getElementById('form-login').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('form-register').style.display = tab === 'register' ? 'block' : 'none';
  document.getElementById('form-master').style.display = tab === 'master' ? 'block' : 'none';
  clearAuthMessages();
}

function clearAuthMessages() {
  document.querySelectorAll('.auth-message').forEach(el => {
    el.className = 'auth-message';
    el.innerText = '';
    el.style.display = 'none';
  });
}

function setAuthMessage(type, message, formId) {
  const box = document.querySelector(`#${formId} .auth-message`);
  if (box) {
    box.className = `auth-message ${type}`;
    box.innerText = message;
    box.style.display = 'block';
  }
}

// 1. Handle Registration
async function handleRegister(e) {
  e.preventDefault();
  clearAuthMessages();

  const name = document.getElementById('reg-name').value.trim();
  const contact = document.getElementById('reg-contact').value.trim();
  const dob = document.getElementById('reg-dob').value.trim();
  const password = document.getElementById('reg-password').value;

  if (!name || !contact || !dob || !password) {
    setAuthMessage('error', 'Please fill in all registration fields.', 'form-register');
    return;
  }

  try {
    const res = await fetch('/api/admin/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, contact, dob, password })
    });

    const data = await res.json();
    if (res.status === 200) {
      sessionToken = data.token;
      currentUser = data.user;
      localStorage.setItem('adhikar_user_token', sessionToken);
      localStorage.setItem('adhikar_user_data', JSON.stringify(currentUser));

      setAuthMessage('success', 'Registration successful! Entering console...', 'form-register');
      setTimeout(() => {
        hideAuthOverlay();
        initApp();
      }, 700);
    } else {
      setAuthMessage('error', data.detail || 'Registration failed.', 'form-register');
    }
  } catch (err) {
    setAuthMessage('error', 'Network error: ' + err.message, 'form-register');
  }
}

// 2. Handle Login
async function handleLogin(e) {
  e.preventDefault();
  clearAuthMessages();

  const contact = document.getElementById('login-contact').value.trim();
  const password = document.getElementById('login-password').value;

  if (!contact || !password) {
    setAuthMessage('error', 'Please enter your registered contact and password.', 'form-login');
    return;
  }

  try {
    const res = await fetch('/api/admin/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contact, password })
    });

    const data = await res.json();
    if (res.status === 200) {
      sessionToken = data.token;
      currentUser = data.user;
      localStorage.setItem('adhikar_user_token', sessionToken);
      localStorage.setItem('adhikar_user_data', JSON.stringify(currentUser));

      hideAuthOverlay();
      initApp();
    } else {
      setAuthMessage('error', data.detail || 'Login failed. Check your credentials.', 'form-login');
    }
  } catch (err) {
    setAuthMessage('error', 'Network error: ' + err.message, 'form-login');
  }
}

// 3. Handle Master Password
async function handleMasterLogin(e) {
  e.preventDefault();
  clearAuthMessages();

  const pass = document.getElementById('master-password-input').value.trim();
  if (!pass) return;

  try {
    const res = await fetch('/api/admin/verify-auth', {
      headers: { 'X-Admin-Password': pass }
    });
    if (res.status === 200) {
      adminPassword = pass;
      currentUser = { name: 'Super Admin', contact: 'admin@system', role: 'admin' };
      localStorage.setItem('adhikar_admin_pass', pass);
      localStorage.setItem('adhikar_user_data', JSON.stringify(currentUser));

      hideAuthOverlay();
      initApp();
    } else {
      setAuthMessage('error', 'Invalid ADMIN_PASSWORD.', 'form-master');
    }
  } catch (err) {
    setAuthMessage('error', 'Network error: ' + err.message, 'form-master');
  }
}

function handleLogout() {
  localStorage.removeItem('adhikar_user_token');
  localStorage.removeItem('adhikar_admin_pass');
  localStorage.removeItem('adhikar_user_data');
  sessionToken = '';
  adminPassword = '';
  currentUser = null;
  location.reload();
}

/* ============================================================
   App Initialization & Navigation
   ============================================================ */

async function initApp() {
  updateUserDisplay();
  const savedTable = localStorage.getItem('adhikar_admin_current_table') || 'users';
  const savedView = localStorage.getItem('adhikar_admin_current_view') || 'browse';
  currentTable = savedTable;
  await refreshSidebarTables();
  switchView(savedView);
}

function updateUserDisplay() {
  const nameEl = document.getElementById('display-user-name');
  const contactEl = document.getElementById('display-user-contact');
  if (currentUser) {
    if (nameEl) nameEl.innerText = currentUser.name || 'Admin User';
    if (contactEl) contactEl.innerText = currentUser.contact || 'Registered';
  } else {
    if (nameEl) nameEl.innerText = 'Admin';
    if (contactEl) contactEl.innerText = 'Master Session';
  }
}

async function refreshSidebarTables() {
  try {
    const res = await fetch('/api/admin/db/tables-summary', {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;
    const tables = await res.json();

    const listEl = document.getElementById('sidebar-table-list');
    listEl.innerHTML = '';

    tables.forEach(t => {
      const li = document.createElement('li');
      li.className = `table-item ${t.name === currentTable ? 'active' : ''}`;
      li.dataset.table = t.name;
      li.innerHTML = `
        <span>📄 ${t.name}</span>
        <span class="table-item-badge">${t.rows}</span>
      `;
      li.onclick = () => selectSidebarTable(t.name);
      listEl.appendChild(li);
    });
  } catch (err) {
    console.error('Failed to load tables summary:', err);
  }
}

function filterSidebarTables(e) {
  const query = e.target.value.toLowerCase();
  document.querySelectorAll('#sidebar-table-list .table-item').forEach(item => {
    const name = item.dataset.table.toLowerCase();
    item.style.display = name.includes(query) ? 'flex' : 'none';
  });
}

function selectSidebarTable(tableName) {
  currentTable = tableName;
  localStorage.setItem('adhikar_admin_current_table', tableName);
  tableRowsOffset = 0;
  tableSearchQuery = '';

  document.querySelectorAll('#sidebar-table-list .table-item').forEach(el => {
    el.classList.toggle('active', el.dataset.table === tableName);
  });

  updateBreadcrumbs();
  switchView('browse');
}

function updateBreadcrumbs() {
  document.getElementById('breadcrumb-db').innerText = 'adhikar_saathi';
  const tableSep = document.getElementById('breadcrumb-table-sep');
  const tableEl = document.getElementById('breadcrumb-table');

  if (currentView === 'structure' && !currentTable) {
    tableSep.style.display = 'none';
    tableEl.style.display = 'none';
  } else {
    tableSep.style.display = 'inline';
    tableEl.style.display = 'inline';
    tableEl.innerText = currentTable || 'tables';
  }
}

function selectDatabaseNode() {
  currentTable = null;
  localStorage.removeItem('adhikar_admin_current_table');
  localStorage.setItem('adhikar_admin_current_view', 'structure');
  document.querySelectorAll('#sidebar-table-list .table-item').forEach(el => el.classList.remove('active'));
  updateBreadcrumbs();
  switchView('structure');
}

function switchView(viewName) {
  currentView = viewName;
  localStorage.setItem('adhikar_admin_current_view', viewName);
  if (currentTable) {
    localStorage.setItem('adhikar_admin_current_table', currentTable);
  }

  document.querySelectorAll('.pma-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.view === viewName);
  });

  const contentArea = document.getElementById('view-container');
  contentArea.innerHTML = '<div style="padding: 2rem; color: #64748b;">Loading view...</div>';

  updateBreadcrumbs();

  if (viewName === 'structure') {
    if (currentTable) {
      renderTableStructureView(currentTable);
    } else {
      renderDatabaseStructureView();
    }
  } else if (viewName === 'browse') {
    renderBrowseView();
  } else if (viewName === 'sql') {
    renderSqlConsoleView();
  } else if (viewName === 'insert') {
    openColumnInsertModal(currentTable);
  } else if (viewName === 'review') {
    renderReviewQueueView();
  } else if (viewName === 'pipeline') {
    renderPipelineIngestionView();
  }
}

/* ============================================================
   View 1: Database Structure (Img 3)
   ============================================================ */

async function renderDatabaseStructureView() {
  try {
    const res = await fetch('/api/admin/db/tables-summary', {
      headers: getAuthHeaders()
    });
    const tables = await res.json();

    let totalRows = 0;
    let totalSizeKb = 0;

    let html = `
      <div style="margin-bottom: 1rem;">
        <h2 style="font-size: 1.15rem; font-weight: 700; color: var(--pma-blue-dark); margin-bottom: 0.35rem;">
          Database: <code>adhikar_saathi.db</code>
        </h2>
        <p style="font-size: 0.8rem; color: var(--pma-text-muted);">
          SQLite Production Database Tables & Structure
        </p>
      </div>

      <div class="pma-toolbar">
        <div class="toolbar-group">
          <label style="font-weight: 600;">Filters containing:</label>
          <input type="text" class="toolbar-input" id="structure-filter" placeholder="Filter tables..." oninput="filterStructureTables(event)">
        </div>
        <div class="toolbar-group">
          <button class="btn btn-secondary" onclick="syncDatabase()">🔄 Sync Files to DB</button>
        </div>
      </div>

      <div class="pma-table-wrapper">
        <table class="pma-grid" id="structure-table">
          <thead>
            <tr>
              <th style="width: 30px;"><input type="checkbox" onchange="toggleCheckAll(event)"></th>
              <th>Table</th>
              <th>Action</th>
              <th style="text-align: right;">Rows</th>
              <th>Type</th>
              <th>Collation</th>
              <th style="text-align: right;">Size</th>
            </tr>
          </thead>
          <tbody>
    `;

    tables.forEach(t => {
      totalRows += t.rows;
      totalSizeKb += t.size_kb;

      html += `
        <tr data-table-name="${t.name}">
          <td><input type="checkbox" class="row-checkbox"></td>
          <td>
            <a href="javascript:void(0)" onclick="selectSidebarTable('${t.name}')" style="color: var(--pma-blue); font-weight: 700; text-decoration: none;">
              📄 ${t.name}
            </a>
          </td>
          <td>
            <div class="action-cell">
              <span class="action-link action-edit" onclick="selectSidebarTable('${t.name}')">🔍 Browse</span>
              <span class="action-link action-copy" onclick="openStructureModal('${t.name}')">🏗️ Structure</span>
              <span class="action-link action-copy" onclick="openColumnInsertModal('${t.name}')">➕ Insert</span>
              <span class="action-link action-delete" onclick="emptyTableAction('${t.name}')">🗑️ Empty</span>
              ${t.name !== 'schemes' && t.name !== 'users' ? `<span class="action-link action-delete" onclick="dropTableAction('${t.name}')">❌ Drop</span>` : ''}
            </div>
          </td>
          <td style="text-align: right; font-weight: 700;">${t.rows.toLocaleString()}</td>
          <td style="color: #64748b;">${t.type}</td>
          <td style="color: #64748b;">${t.collation}</td>
          <td style="text-align: right; font-family: var(--font-mono);">${t.size_kb.toFixed(1)} KiB</td>
        </tr>
      `;
    });

    html += `
          </tbody>
          <tfoot>
            <tr style="background: #e9ecef; font-weight: 700;">
              <td></td>
              <td>${tables.length} table(s)</td>
              <td>Total Database Footprint</td>
              <td style="text-align: right;">${totalRows.toLocaleString()}</td>
              <td>SQLite 3</td>
              <td>utf8_general_ci</td>
              <td style="text-align: right; font-family: var(--font-mono);">${totalSizeKb.toFixed(1)} KiB</td>
            </tr>
          </tfoot>
        </table>
      </div>
    `;

    document.getElementById('view-container').innerHTML = html;
  } catch (err) {
    document.getElementById('view-container').innerHTML = `<div style="color: red; padding: 2rem;">Error: ${err.message}</div>`;
  }
}

function filterStructureTables(e) {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('#structure-table tbody tr').forEach(row => {
    const name = row.dataset.tableName.toLowerCase();
    row.style.display = name.includes(q) ? '' : 'none';
  });
}

/* ============================================================
   View 2: Browse Table Rows (Img 4)
   ============================================================ */

async function renderBrowseView() {
  try {
    const url = `/api/admin/db/table/${currentTable}?limit=${tableRowsLimit}&offset=${tableRowsOffset}${tableSearchQuery ? '&search=' + encodeURIComponent(tableSearchQuery) : ''}`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    const data = await res.json();

    currentTableData = data;
    currentTableSchema = data.schema || [];

    const startIdx = data.total_rows === 0 ? 0 : data.offset + 1;
    const endIdx = Math.min(data.offset + data.rows.length, data.total_rows);

    let html = `
      <!-- phpMyAdmin Green Success Banner (Img 4) -->
      <div class="query-success-banner">
        <span>✅</span>
        <span>Showing rows ${startIdx} - ${endIdx} (${data.total_rows} total, Query took ${data.query_time_seconds} seconds.)</span>
      </div>

      <!-- SQL Box (Img 4) -->
      <div class="sql-display-box">
        ${escapeHtml(data.query_sql)}
      </div>

      <!-- Table Toolbar Options -->
      <div class="pma-toolbar">
        <div class="toolbar-group">
          <label><input type="checkbox" id="show-all-cb" onchange="toggleShowAll(event)"> Show all</label>
          <span style="color: #cbd5e1;">|</span>
          <label>Number of rows:</label>
          <select class="toolbar-select" onchange="changeLimit(event)">
            <option value="10" ${tableRowsLimit === 10 ? 'selected' : ''}>10</option>
            <option value="25" ${tableRowsLimit === 25 ? 'selected' : ''}>25</option>
            <option value="50" ${tableRowsLimit === 50 ? 'selected' : ''}>50</option>
            <option value="100" ${tableRowsLimit === 100 ? 'selected' : ''}>100</option>
          </select>
          <span style="color: #cbd5e1;">|</span>
          <label>Filter rows:</label>
          <input type="text" class="toolbar-input" placeholder="Search table..." value="${tableSearchQuery}" onkeydown="if(event.key==='Enter') executeTableSearch(this.value)">
          <button class="btn btn-secondary" onclick="executeTableSearch(this.previousElementSibling.value)">Search</button>
        </div>

        <div class="toolbar-group">
          <button class="btn btn-primary" onclick="openColumnInsertModal('${currentTable}')">➕ Insert New Row</button>
        </div>
      </div>

      <!-- Main Data Table Grid (Clean Production View with Double-Click Inline Editing) -->
      <div class="pma-table-wrapper">
        <table class="pma-grid">
          <thead>
            <tr>
              <th style="width: 30px;"><input type="checkbox" onchange="toggleCheckAll(event)"></th>
    `;

    data.columns.forEach(col => {
      const isPk = col === data.primary_key;
      html += `<th>${col.toUpperCase()}${isPk ? ' 🔑' : ''}</th>`;
    });

    html += `
            </tr>
          </thead>
          <tbody>
    `;

    if (data.rows.length === 0) {
      html += `<tr><td colspan="${data.columns.length + 1}" style="text-align: center; padding: 2.5rem; color: #94a3b8;">No matching records found in table '${currentTable}'.</td></tr>`;
    } else {
      data.rows.forEach(row => {
        const pkVal = row[data.primary_key];
        const rowJsonStr = encodeURIComponent(JSON.stringify(row));

        html += `
          <tr>
            <td><input type="checkbox" class="row-checkbox" data-pk="${pkVal}" data-row="${rowJsonStr}"></td>
        `;

        data.columns.forEach(col => {
          const val = row[col];
          const isPk = col === data.primary_key;
          if (col === 'tier' || col === 'status') {
            const badgeClass = val === 'verified' ? 'badge-verified' : (val === 'rejected' ? 'badge-rejected' : 'badge-extracted');
            html += `<td class="editable-cell" data-col="${col}" data-pk="${pkVal}" ondblclick="handleCellDblClick(this, '${currentTable}', '${data.primary_key}', '${pkVal}', '${col}')" title="Double click to edit"><span class="badge ${badgeClass}">${val}</span></td>`;
          } else if (col === 'password_hash') {
            html += `<td class="editable-cell" data-col="${col}" data-pk="${pkVal}" ondblclick="handleCellDblClick(this, '${currentTable}', '${data.primary_key}', '${pkVal}', '${col}')" style="color: #64748b;" title="Double click to change password">[PBKDF2 SHA256 HASH]</td>`;
          } else {
            const strVal = val !== null && val !== undefined ? String(val) : '';
            html += `<td class="editable-cell" data-col="${col}" data-pk="${pkVal}" ondblclick="handleCellDblClick(this, '${currentTable}', '${data.primary_key}', '${pkVal}', '${col}')" title="Double click to edit">${escapeHtml(strVal)}</td>`;
          }
        });

        html += `</tr>`;
      });
    }

    html += `
          </tbody>
        </table>
      </div>

      <!-- Pagination and Bulk Options (Matching Img 6) -->
      <div class="table-footer-bar">
        <div class="bulk-actions-container">
          <input type="checkbox" id="check-all-footer" onchange="toggleCheckAll(event)">
          <label for="check-all-footer" style="font-weight: 600; cursor: pointer;">Check all</label>
          <span style="color: #64748b; font-style: italic; margin-left: 0.5rem; margin-right: 0.25rem;">With selected:</span>
          <button class="bulk-action-link" onclick="bulkActionEdit()" title="Edit selected row">✏️ Edit</button>
          <button class="bulk-action-link" onclick="bulkActionCopy()" title="Copy selected row">📋 Copy</button>
          <button class="bulk-action-link bulk-delete" onclick="bulkActionDelete()" title="Delete selected rows">⛔ Delete</button>
          <button class="bulk-action-link" onclick="bulkActionExport()" title="Export selected rows as JSON">📊 Export</button>
          ${currentTable === 'schemes' ? `<button class="bulk-action-link bulk-verify" onclick="bulkActionVerify()" title="Verify selected schemes">⭐ Verify</button>` : ''}
        </div>

        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <button class="btn btn-secondary" ${data.offset === 0 ? 'disabled' : ''} onclick="paginateOffset(-${tableRowsLimit})">« Previous</button>
          <span>Page ${Math.floor(data.offset / tableRowsLimit) + 1} of ${Math.max(1, Math.ceil(data.total_rows / tableRowsLimit))}</span>
          <button class="btn btn-secondary" ${data.offset + data.rows.length >= data.total_rows ? 'disabled' : ''} onclick="paginateOffset(${tableRowsLimit})">Next »</button>
        </div>
      </div>
    `;

    document.getElementById('view-container').innerHTML = html;
  } catch (err) {
    document.getElementById('view-container').innerHTML = `<div style="color: red; padding: 2rem;">Error loading table: ${err.message}</div>`;
  }
}

function paginateOffset(delta) {
  tableRowsOffset = Math.max(0, tableRowsOffset + delta);
  renderBrowseView();
}

function changeLimit(e) {
  tableRowsLimit = parseInt(e.target.value, 10);
  tableRowsOffset = 0;
  renderBrowseView();
}

function toggleShowAll(e) {
  if (e.target.checked) {
    tableRowsLimit = 500;
  } else {
    tableRowsLimit = 25;
  }
  tableRowsOffset = 0;
  renderBrowseView();
}

function executeTableSearch(val) {
  tableSearchQuery = val.trim();
  tableRowsOffset = 0;
  renderBrowseView();
}

function toggleCheckAll(e) {
  const checked = e.target.checked;
  document.querySelectorAll('.row-checkbox').forEach(cb => cb.checked = checked);
  const footerCb = document.getElementById('check-all-footer');
  if (footerCb && footerCb !== e.target) footerCb.checked = checked;
}

function getSelectedRows() {
  const checkboxes = document.querySelectorAll('.row-checkbox:checked');
  const results = [];
  checkboxes.forEach(cb => {
    const pk = cb.dataset.pk;
    const rowStr = cb.dataset.row;
    if (pk) {
      let rowObj = null;
      if (rowStr) {
        try { rowObj = JSON.parse(decodeURIComponent(rowStr)); } catch (e) {}
      }
      if (!rowObj && currentTableData?.rows) {
        rowObj = currentTableData.rows.find(r => String(r[currentTableData.primary_key]) === String(pk));
      }
      results.push({ pk, row: rowObj });
    }
  });
  return results;
}

function bulkActionEdit() {
  const selected = getSelectedRows();
  if (selected.length === 0) {
    alert('Please select a row using the checkbox to edit.');
    return;
  }
  const first = selected[0];
  openColumnEditModal(currentTable, currentTableData.primary_key, JSON.stringify(first.row));
}

function bulkActionCopy() {
  const selected = getSelectedRows();
  if (selected.length === 0) {
    alert('Please select a row using the checkbox to copy.');
    return;
  }
  const first = selected[0];
  openColumnCopyModal(currentTable, JSON.stringify(first.row));
}

async function bulkActionDelete() {
  const selected = getSelectedRows();
  if (selected.length === 0) {
    alert('Please select at least one row using the checkboxes to delete.');
    return;
  }

  if (!confirm(`Are you sure you want to permanently DELETE ${selected.length} record(s) from table '${currentTable}'?`)) {
    return;
  }

  const pkCol = currentTableData.primary_key;
  for (const item of selected) {
    try {
      await fetch(`/api/admin/db/table/${currentTable}/row?pk_col=${encodeURIComponent(pkCol)}&pk_val=${encodeURIComponent(item.pk)}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
    } catch (e) {
      console.error(e);
    }
  }

  renderBrowseView();
  refreshSidebarTables();
}

function bulkActionExport() {
  const selected = getSelectedRows();
  const rowsToExport = selected.length > 0 ? selected.map(s => s.row) : (currentTableData?.rows || []);
  if (rowsToExport.length === 0) {
    alert('No rows available to export.');
    return;
  }
  const blob = new Blob([JSON.stringify(rowsToExport, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentTable}_export_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

async function bulkActionVerify() {
  const selected = getSelectedRows();
  if (selected.length === 0) {
    alert('Please select at least one scheme using the checkbox to verify.');
    return;
  }
  for (const item of selected) {
    await promoteScheme(item.pk);
  }
  renderBrowseView();
  refreshSidebarTables();
}

/* ============================================================
   Double-Click Inline Cell Editing
   Directly updates the cell value and sends PUT to SQLite
   ============================================================ */

function handleCellDblClick(td, tableName, pkCol, pkVal, colName) {
  // Prevent duplicate inputs if already editing
  if (td.querySelector('.inline-cell-input') || td.querySelector('.inline-cell-textarea')) return;

  // Don't allow editing auto-increment integer PK directly
  if (colName === pkCol) {
    const pkSchema = (currentTableSchema || []).find(c => c.name === pkCol);
    if (pkSchema && pkSchema.type.toUpperCase() === 'INTEGER') {
      alert('Primary key ID is auto-generated and cannot be modified inline.');
      return;
    }
  }

  // Find original raw value from currentTableData.rows
  const rowObj = (currentTableData?.rows || []).find(r => String(r[pkCol]) === String(pkVal));
  let origVal = rowObj ? rowObj[colName] : (td.getAttribute('data-raw') || td.innerText);
  if (origVal === null || origVal === undefined) origVal = '';

  const origDisplayHtml = td.innerHTML;
  const isMultiLine = typeof origVal === 'string' && (origVal.length > 50 || origVal.includes('\n') || colName.includes('json') || colName === 'criteria' || colName === 'raw_json');

  let inputEl;
  if (isMultiLine) {
    inputEl = document.createElement('textarea');
    inputEl.className = 'inline-cell-textarea';
    inputEl.value = typeof origVal === 'object' ? JSON.stringify(origVal, null, 2) : origVal;
  } else {
    inputEl = document.createElement('input');
    inputEl.type = (colName === 'dob' || colName.includes('date')) ? 'date' : (colName === 'password_hash' ? 'password' : 'text');
    inputEl.className = 'inline-cell-input';
    inputEl.value = typeof origVal === 'object' ? JSON.stringify(origVal) : origVal;
    if (colName === 'password_hash') inputEl.placeholder = 'Enter new password...';
  }

  td.innerHTML = '';
  td.appendChild(inputEl);
  inputEl.focus();
  if (inputEl.select && inputEl.type !== 'date') inputEl.select();

  let committed = false;

  async function commitChange() {
    if (committed) return;
    committed = true;

    const newVal = inputEl.value.trim();
    if (colName !== 'password_hash' && newVal === String(origVal).trim()) {
      td.innerHTML = origDisplayHtml;
      return;
    }

    if (colName === 'password_hash' && !newVal) {
      td.innerHTML = origDisplayHtml;
      return;
    }

    // Try parsing if json
    let finalVal = newVal;
    if (colName.includes('json') || colName === 'criteria' || colName === 'raw_json') {
      try {
        finalVal = JSON.parse(newVal);
      } catch (e) {
        alert('Invalid JSON: ' + e.message);
        td.innerHTML = origDisplayHtml;
        return;
      }
    }

    try {
      const res = await fetch(`/api/admin/db/table/${tableName}/row`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          pk_col: pkCol,
          pk_val: pkVal,
          data: { [colName]: finalVal }
        })
      });

      const resData = await res.json();
      if (res.ok && resData.status === 'success') {
        if (rowObj) rowObj[colName] = finalVal;
        if (colName === 'password_hash') {
          td.innerHTML = `<span style="color: #64748b;" title="Password updated">[PBKDF2 SHA256 HASH]</span>`;
        } else if (colName === 'tier' || colName === 'status') {
          const badgeClass = finalVal === 'verified' ? 'badge-verified' : (finalVal === 'rejected' ? 'badge-rejected' : 'badge-extracted');
          td.innerHTML = `<span class="badge ${badgeClass}">${finalVal}</span>`;
        } else {
          const displayStr = typeof finalVal === 'object' ? JSON.stringify(finalVal) : String(finalVal);
          td.innerText = displayStr;
          td.title = displayStr;
        }
        td.classList.add('cell-updated-success');
        setTimeout(() => td.classList.remove('cell-updated-success'), 1600);
      } else {
        alert('Update failed: ' + (resData.detail || 'Unknown error'));
        td.innerHTML = origDisplayHtml;
      }
    } catch (err) {
      alert('Network error: ' + err.message);
      td.innerHTML = origDisplayHtml;
    }
  }

  function cancelEdit() {
    if (committed) return;
    committed = true;
    td.innerHTML = origDisplayHtml;
  }

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      commitChange();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  });

  inputEl.addEventListener('blur', () => {
    setTimeout(commitChange, 120);
  });
}

/* ============================================================
   View 3: Field-by-Field Column Edit & Insert (Modal Form)
   Addresses: "If table has columns then I wont be able to get it"
   ============================================================ */

async function openColumnEditModal(tableName, pkCol, rowJsonStr) {
  const row = JSON.parse(rowJsonStr);
  const pkVal = row[pkCol];

  const res = await fetch(`/api/admin/db/table/${tableName}/structure`, { headers: getAuthHeaders() });
  const schema = await res.json();

  let formHtml = `
    <form onsubmit="submitColumnEdit(event, '${tableName}', '${pkCol}', '${pkVal}')">
      <table class="column-form-table">
        <thead>
          <tr>
            <th style="width: 25%;">Column</th>
            <th style="width: 15%;">Type</th>
            <th style="width: 60%;">Value</th>
          </tr>
        </thead>
        <tbody>
  `;

  schema.forEach(col => {
    const isPk = col.pk;
    const currentVal = row[col.name];
    const isJson = col.name.includes('json') || col.name === 'criteria' || col.name === 'raw_json';

    formHtml += `
      <tr>
        <td>
          <div class="column-name-label">${col.name} ${isPk ? '🔑' : ''}</div>
          ${isPk ? '<span style="font-size: 0.7rem; color: #dc2626;">(Primary Key)</span>' : ''}
        </td>
        <td><span class="column-type-label">${col.type}</span></td>
        <td>
    `;

    if (col.name === 'password_hash') {
      formHtml += `
        <input type="password" class="column-input" name="${col.name}" placeholder="Enter new password to re-hash, or leave blank to keep unchanged">
        <div style="font-size: 0.72rem; color: #64748b; margin-top: 0.25rem;">Stored securely in PBKDF2 salt$hash format</div>
      `;
    } else if (isJson) {
      let formatted = '';
      try {
        formatted = typeof currentVal === 'object' ? JSON.stringify(currentVal, null, 2) : (currentVal ? JSON.stringify(JSON.parse(currentVal), null, 2) : '');
      } catch (e) {
        formatted = currentVal || '';
      }
      formHtml += `<textarea class="column-textarea" name="${col.name}" style="height: 140px;">${escapeHtml(formatted)}</textarea>`;
    } else if (col.type.toUpperCase() === 'INTEGER' || col.type.toUpperCase() === 'REAL') {
      formHtml += `<input type="number" step="any" class="column-input" name="${col.name}" value="${currentVal !== null && currentVal !== undefined ? currentVal : ''}" ${isPk ? 'readonly style="background: #f1f5f9;"' : ''}>`;
    } else if (col.name === 'dob' || col.name.includes('date')) {
      formHtml += `<input type="date" class="column-input" name="${col.name}" value="${currentVal || ''}">`;
    } else {
      formHtml += `<input type="text" class="column-input" name="${col.name}" value="${currentVal !== null && currentVal !== undefined ? escapeHtml(String(currentVal)) : ''}" ${isPk ? 'readonly style="background: #f1f5f9;"' : ''}>`;
    }

    formHtml += `</td></tr>`;
  });

  formHtml += `
        </tbody>
      </table>
      <div class="modal-footer" style="padding-right: 0; padding-left: 0; border: none; margin-top: 1.5rem;">
        <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Changes to Database</button>
      </div>
    </form>
  `;

  document.getElementById('modal-title').innerText = `✏️ Edit Row in '${tableName}' (where ${pkCol} = ${pkVal})`;
  document.getElementById('modal-body-content').innerHTML = formHtml;
  document.getElementById('generic-modal').style.display = 'flex';
}

async function submitColumnEdit(e, tableName, pkCol, pkVal) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const data = {};

  for (const [key, val] of formData.entries()) {
    if (key === 'password_hash' && !val.trim()) continue; // keep unchanged
    data[key] = val;
  }

  try {
    const res = await fetch(`/api/admin/db/table/${tableName}/row`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ pk_col: pkCol, pk_val: pkVal, data })
    });

    const result = await res.json();
    if (res.status === 200) {
      alert(`✅ Row updated successfully in table '${tableName}'!`);
      closeGenericModal();
      renderBrowseView();
      refreshSidebarTables();
    } else {
      alert(`Error updating row: ${result.detail || JSON.stringify(result)}`);
    }
  } catch (err) {
    alert('Network error: ' + err.message);
  }
}

async function openColumnInsertModal(tableName) {
  const res = await fetch(`/api/admin/db/table/${tableName}/structure`, { headers: getAuthHeaders() });
  const schema = await res.json();
  const nowIso = new Date().toISOString();

  let formHtml = `
    <form onsubmit="submitColumnInsert(event, '${tableName}')">
      <table class="column-form-table">
        <thead>
          <tr>
            <th style="width: 25%;">Column</th>
            <th style="width: 15%;">Type</th>
            <th style="width: 60%;">Value</th>
          </tr>
        </thead>
        <tbody>
  `;

  schema.forEach(col => {
    const isAutoPk = col.pk && col.type.toUpperCase() === 'INTEGER';
    const isJson = col.name.includes('json') || col.name === 'criteria' || col.name === 'raw_json';
    const isCreatedAt = col.name.toLowerCase().includes('created_at') || col.name.toLowerCase().includes('updated_at');

    formHtml += `
      <tr>
        <td>
          <div class="column-name-label">${col.name} ${col.pk ? '🔑' : ''}</div>
          ${isAutoPk ? '<span style="font-size: 0.7rem; color: #16a34a;">(Auto-Increment)</span>' : ''}
        </td>
        <td><span class="column-type-label">${col.type}</span></td>
        <td>
    `;

    if (isAutoPk) {
      formHtml += `<input type="text" class="column-input" placeholder="Auto-generated ID on insert" disabled style="background: #f1f5f9;">`;
    } else if (col.name === 'password_hash') {
      formHtml += `<input type="password" class="column-input" name="${col.name}" placeholder="Enter password (will be securely PBKDF2 hashed)" required>`;
    } else if (isCreatedAt) {
      formHtml += `<input type="text" class="column-input" name="${col.name}" value="${nowIso}" placeholder="${nowIso}">`;
    } else if (tableName === 'users' && col.name === 'role') {
      formHtml += `
        <select class="column-input" name="${col.name}">
          <option value="user" selected>user</option>
          <option value="admin">admin</option>
        </select>
      `;
    } else if (isJson) {
      formHtml += `<textarea class="column-textarea" name="${col.name}" placeholder="Enter valid JSON array or object..."></textarea>`;
    } else if (col.type.toUpperCase() === 'INTEGER' || col.type.toUpperCase() === 'REAL') {
      formHtml += `<input type="number" step="any" class="column-input" name="${col.name}" placeholder="Numeric value">`;
    } else if (col.name === 'dob' || col.name.includes('date')) {
      formHtml += `<input type="date" class="column-input" name="${col.name}">`;
    } else {
      formHtml += `<input type="text" class="column-input" name="${col.name}" placeholder="Value for ${col.name}">`;
    }

    formHtml += `</td></tr>`;
  });

  formHtml += `
        </tbody>
      </table>
      <div class="modal-footer" style="padding-right: 0; padding-left: 0; border: none; margin-top: 1.5rem;">
        <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Insert Record into Database</button>
      </div>
    </form>
  `;

  document.getElementById('modal-title').innerText = `➕ Insert New Row into '${tableName}'`;
  document.getElementById('modal-body-content').innerHTML = formHtml;
  document.getElementById('generic-modal').style.display = 'flex';
}

async function submitColumnInsert(e, tableName) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const data = {};

  for (const [key, val] of formData.entries()) {
    if (val.trim()) data[key] = val;
  }

  try {
    const res = await fetch(`/api/admin/db/table/${tableName}/row`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });

    const result = await res.json();
    if (res.status === 200) {
      alert(`✅ New row inserted into table '${tableName}'! (ID: ${result.inserted_id})`);
      closeGenericModal();
      renderBrowseView();
      refreshSidebarTables();
    } else {
      alert(`Insert error: ${result.detail || JSON.stringify(result)}`);
    }
  } catch (err) {
    alert('Network error: ' + err.message);
  }
}

function openColumnCopyModal(tableName, rowJsonStr) {
  openColumnInsertModal(tableName).then(() => {
    const row = JSON.parse(rowJsonStr);
    const form = document.querySelector('#modal-body-content form');
    if (!form) return;
    document.getElementById('modal-title').innerText = `📋 Copy / Duplicate Record into '${tableName}'`;

    const nowIso = new Date().toISOString();
    for (const [key, val] of Object.entries(row)) {
      const input = form.elements[key];
      if (input && key !== 'id') {
        if (key.toLowerCase().includes('created_at') || key.toLowerCase().includes('updated_at')) {
          input.value = nowIso;
        } else {
          input.value = typeof val === 'object' ? JSON.stringify(val) : (val !== null ? val : '');
        }
      }
    }
  });
}

/* ============================================================
   Table Structure View (Matching Img 5)
   ============================================================ */

async function renderTableStructureView(tableName) {
  try {
    const res = await fetch(`/api/admin/db/table/${tableName}/structure`, { headers: getAuthHeaders() });
    const cols = await res.json();

    let html = `
      <!-- Table Structure Top Subbar (Matching Img 5) -->
      <div class="structure-subbar">
        <button class="subbar-btn active">📑 Table structure: <strong>${escapeHtml(tableName)}</strong></button>
        <button class="subbar-btn" onclick="switchView('browse')">🔍 Browse Table Data</button>
        <button class="subbar-btn" onclick="openColumnInsertModal('${tableName}')">➕ Insert New Row</button>
      </div>

      <!-- Main Structure Table Grid (Img 5) -->
      <div class="pma-table-wrapper">
        <table class="pma-grid">
          <thead>
            <tr>
              <th style="width: 25px;"><input type="checkbox" onchange="toggleCheckAll(event)"></th>
              <th style="width: 35px;">#</th>
              <th>Name</th>
              <th>Type</th>
              <th>Collation</th>
              <th>Attributes</th>
              <th>Null</th>
              <th>Default</th>
              <th>Comments</th>
              <th>Extra</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
    `;

    cols.forEach((col, idx) => {
      const isPk = !!col.pk;
      const isAutoPk = isPk && (col.type || '').toUpperCase() === 'INTEGER';
      const isNotNull = !!col.notnull;
      const dfltVal = col.dflt_value !== null && col.dflt_value !== undefined 
        ? String(col.dflt_value) 
        : (isNotNull ? 'None' : 'NULL');

      html += `
        <tr>
          <td><input type="checkbox" class="row-checkbox" data-col="${escapeHtml(col.name)}"></td>
          <td style="font-family: var(--font-mono); color: #64748b;">${idx + 1}</td>
          <td>
            <strong style="color: var(--pma-blue-dark);">${escapeHtml(col.name)}</strong>
            ${isPk ? ' 🔑' : ''}
          </td>
          <td style="font-family: var(--font-mono);">${escapeHtml(col.type || 'TEXT')}</td>
          <td style="font-family: var(--font-mono); color: #64748b;">utf8mb4_general_ci</td>
          <td style="color: #64748b;">—</td>
          <td>${isNotNull ? '<span style="color: #dc2626; font-weight: 700;">No</span>' : '<span style="color: #16a34a; font-weight: 700;">Yes</span>'}</td>
          <td style="font-family: var(--font-mono); color: #475569; font-style: italic;">${escapeHtml(dfltVal)}</td>
          <td style="color: #94a3b8;">—</td>
          <td style="font-family: var(--font-mono); font-size: 0.75rem; color: #0284c7;">
            ${isAutoPk ? 'AUTO_INCREMENT' : '—'}
          </td>
          <td>
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <span class="action-link-small" onclick="openColumnInsertModal('${tableName}')">✏️ Change</span>
              <span class="action-link-small action-drop" onclick="alert('Dropping table columns is restricted on live SQLite production databases.')">⛔ Drop</span>
              ${isPk ? '<span style="color: #d97706; font-weight: 700; font-size: 0.72rem;">🔑 Primary</span>' : '<span class="action-link-small" onclick="alert(\'Index defined in database catalog\')">More</span>'}
            </div>
          </td>
        </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>

      <!-- Structure Footer Options (Matching Img 5) -->
      <div class="table-footer-bar">
        <div class="bulk-actions-container">
          <input type="checkbox" onchange="toggleCheckAll(event)">
          <label style="font-weight: 600;">Check all</label>
          <span style="color: #64748b; font-style: italic; margin-left: 0.5rem;">With selected:</span>
          <button class="bulk-action-link" onclick="switchView('browse')">📄 Browse</button>
          <button class="bulk-action-link" onclick="alert('Column alterations can be executed via the SQL console.')">✏️ Change</button>
          <button class="bulk-action-link bulk-delete" onclick="alert('Column dropping restricted on live tables.')">⛔ Drop</button>
          <button class="bulk-action-link" style="color: #d97706;">🔑 Primary</button>
        </div>
      </div>
    `;

    document.getElementById('view-container').innerHTML = html;
  } catch (err) {
    document.getElementById('view-container').innerHTML = `<div style="color: red; padding: 2rem;">Error loading structure: ${err.message}</div>`;
  }
}

async function openStructureModal(tableName) {
  currentTable = tableName;
  switchView('structure');
}

function closeGenericModal() {
  document.getElementById('generic-modal').style.display = 'none';
}

/* ============================================================
   Row & Table Actions (Delete, Empty, Drop, Verify, Sync)
   ============================================================ */

async function deleteTableRowAction(tableName, pkCol, pkVal) {
  if (!confirm(`Are you sure you want to permanently DELETE the row where ${pkCol} = '${pkVal}' from table '${tableName}'?`)) return;

  try {
    const res = await fetch(`/api/admin/db/table/${tableName}/row?pk_col=${encodeURIComponent(pkCol)}&pk_val=${encodeURIComponent(pkVal)}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (res.status === 200) {
      renderBrowseView();
      refreshSidebarTables();
    } else {
      const err = await res.json();
      alert('Delete failed: ' + (err.detail || JSON.stringify(err)));
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function emptyTableAction(tableName) {
  if (!confirm(`⚠️ CAUTION: Are you sure you want to EMPTY table '${tableName}'? All records will be permanently deleted.`)) return;

  try {
    const res = await fetch(`/api/admin/db/table/${tableName}/empty`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (res.status === 200) {
      alert(`Table '${tableName}' has been emptied.`);
      renderBrowseView();
      refreshSidebarTables();
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function dropTableAction(tableName) {
  if (!confirm(`🚨 DANGER: Are you sure you want to DROP table '${tableName}'? The table will be permanently deleted.`)) return;

  try {
    const res = await fetch(`/api/admin/db/table/${tableName}/drop`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (res.status === 200) {
      alert(`Table '${tableName}' dropped.`);
      switchView('structure');
      refreshSidebarTables();
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function promoteScheme(schemeId) {
  if (!confirm(`Promote scheme '${schemeId}' to Tier 1 Verified?`)) return;
  try {
    const res = await fetch(`/api/admin/review/${schemeId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ action: 'promote', reviewer: currentUser ? currentUser.name : 'admin', notes: 'Verified via DBControl' })
    });
    if (res.status === 200) {
      alert(`✅ Scheme '${schemeId}' promoted to Tier 1 Verified!`);
      renderBrowseView();
      refreshSidebarTables();
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function syncDatabase() {
  try {
    const res = await fetch('/api/admin/db/sync', {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const data = await res.json();
    alert(`✅ SQLite Synchronized with JSON files:\nVerified: ${data.synced.synced_verified}\nExtracted: ${data.synced.synced_extracted}`);
    refreshSidebarTables();
    if (currentView === 'structure') renderDatabaseStructureView();
    else if (currentView === 'browse') renderBrowseView();
  } catch (err) {
    alert('Sync error: ' + err.message);
  }
}

/* ============================================================
   View 4: SQL Console
   ============================================================ */

function renderSqlConsoleView() {
  const html = `
    <div style="margin-bottom: 1rem;">
      <h2 style="font-size: 1.15rem; font-weight: 700; color: var(--pma-blue-dark); margin-bottom: 0.35rem;">
        Run SQL query/queries on database <code>adhikar_saathi</code>
      </h2>
    </div>

    <div class="sql-editor-container">
      <textarea id="sql-query-box" class="sql-textarea" placeholder="SELECT * FROM schemes WHERE tier = 'verified' LIMIT 20;"></textarea>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <button class="btn btn-primary" onclick="runDirectSql()">▶ Execute Query</button>
        <span style="font-size: 0.75rem; color: #64748b; font-family: var(--font-mono);">Supports SELECT, INSERT, UPDATE, DELETE, and PRAGMA</span>
      </div>
    </div>

    <div id="sql-execution-output"></div>
  `;

  document.getElementById('view-container').innerHTML = html;
}

async function runDirectSql() {
  const query = document.getElementById('sql-query-box').value.trim();
  if (!query) return;

  const outputDiv = document.getElementById('sql-execution-output');
  outputDiv.innerHTML = '<div style="color: #64748b; padding: 1rem;">Executing query...</div>';

  try {
    const res = await fetch('/api/admin/db/query', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query })
    });
    const data = await res.json();

    if (res.status === 200) {
      if (data.type === 'select') {
        let resHtml = `
          <div class="query-success-banner" style="margin-top: 1rem;">
            <span>✅</span>
            <span>Query executed successfully. ${data.row_count} row(s) returned.</span>
          </div>
          <div class="pma-table-wrapper" style="margin-top: 1rem;">
            <table class="pma-grid">
              <thead>
                <tr>${data.columns.map(c => `<th>${c.toUpperCase()}</th>`).join('')}</tr>
              </thead>
              <tbody>
        `;
        if (data.rows.length === 0) {
          resHtml += `<tr><td colspan="${data.columns.length}" style="text-align: center; padding: 2rem; color: #94a3b8;">Empty result set (0 rows).</td></tr>`;
        } else {
          data.rows.forEach(r => {
            resHtml += `<tr>${data.columns.map(c => `<td>${escapeHtml(String(r[c] !== null && r[c] !== undefined ? r[c] : ''))}</td>`).join('')}</tr>`;
          });
        }
        resHtml += `</tbody></table></div>`;
        outputDiv.innerHTML = resHtml;
      } else {
        outputDiv.innerHTML = `
          <div class="query-success-banner" style="margin-top: 1rem;">
            <span>✅</span>
            <span>Mutation executed. ${data.rows_affected} row(s) affected.</span>
          </div>
        `;
        refreshSidebarTables();
      }
    } else {
      outputDiv.innerHTML = `<div style="background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; padding: 1rem; border-radius: 4px; margin-top: 1rem;"><strong>SQL Error:</strong> ${data.detail || 'Execution failed'}</div>`;
    }
  } catch (err) {
    outputDiv.innerHTML = `<div style="color: red; padding: 1rem;">Network Error: ${err.message}</div>`;
  }
}

function escapeHtml(str) {
  if (typeof str !== 'string') return String(str);
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/* ============================================================
   Phase 5: Scheme Curation & Review Queue
   ============================================================ */

let currentCurationFilter = 'all';

async function renderReviewQueueView(filter = currentCurationFilter) {
  currentCurationFilter = filter;
  try {
    const url = filter === 'all' ? '/api/admin/review' : `/api/admin/review?status=${filter}`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    const schemes = await res.json();

    // Fetch all for counts
    const resAll = await fetch('/api/admin/review', { headers: getAuthHeaders() });
    const allSchemes = await resAll.json();
    const countTotal = allSchemes.length;
    const countUnverified = allSchemes.filter(s => s.status === 'unverified' || s.tier === 'extracted').length;
    const countVerified = allSchemes.filter(s => s.status === 'verified' && s.tier === 'verified').length;
    const countRejected = allSchemes.filter(s => s.status === 'rejected').length;

    let html = `
      <div class="curation-header">
        <div>
          <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--pma-blue-dark); margin-bottom: 0.25rem;">
            ⚖️ Scheme Curation & Review Queue
          </h2>
          <p style="font-size: 0.8rem; color: var(--pma-text-muted);">
            Human-in-the-loop review: approve extracted records to Tier 1 Verified, edit eligibility criteria, or mark rejected.
          </p>
        </div>

        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <button class="btn btn-secondary" onclick="switchView('pipeline')">
            🚀 Ingestion Pipeline
          </button>
          <button class="btn btn-primary" onclick="renderReviewQueueView()">
            🔄 Refresh Queue
          </button>
        </div>
      </div>

      <!-- Filter Pills -->
      <div class="curation-filters" style="margin-bottom: 1.25rem;">
        <button class="curation-filter-btn ${filter === 'all' ? 'active' : ''}" onclick="renderReviewQueueView('all')">
          All Records (${countTotal})
        </button>
        <button class="curation-filter-btn ${filter === 'unverified' ? 'active' : ''}" onclick="renderReviewQueueView('unverified')">
          ⚠️ Needs Review / Extracted (${countUnverified})
        </button>
        <button class="curation-filter-btn ${filter === 'verified' ? 'active' : ''}" onclick="renderReviewQueueView('verified')">
          ✅ Tier 1 Verified (${countVerified})
        </button>
        <button class="curation-filter-btn ${filter === 'rejected' ? 'active' : ''}" onclick="renderReviewQueueView('rejected')">
          ❌ Rejected (${countRejected})
        </button>
      </div>
    `;

    if (schemes.length === 0) {
      html += `
        <div style="text-align: center; padding: 3rem; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 8px; color: #64748b;">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎉</div>
          <div style="font-weight: 700; font-size: 1rem; color: #334155;">No records in '${filter}' queue</div>
          <div style="font-size: 0.8rem; margin-top: 0.25rem;">All documents in this category have been processed or none match the filter.</div>
        </div>
      `;
    } else {
      html += `<div class="curation-grid">`;
      schemes.forEach(s => {
        const confPct = Math.round((s.confidence || 0) * 100);
        const confClass = confPct >= 85 ? 'confidence-fill-high' : (confPct >= 60 ? 'confidence-fill-med' : 'confidence-fill-low');
        const isVerified = s.tier === 'verified' && s.status === 'verified';
        const isRejected = s.status === 'rejected';

        html += `
          <div class="curation-card">
            <div>
              <div class="curation-card-header">
                <div>
                  <div class="curation-title">${escapeHtml(s.name_en || s.id)}</div>
                  <div class="curation-slug">${escapeHtml(s.id)}</div>
                </div>
                <div>
                  <span class="badge ${isVerified ? 'badge-verified' : (isRejected ? 'badge-rejected' : 'badge-extracted')}">
                    ${isVerified ? 'Tier 1 Verified' : (isRejected ? 'Rejected' : 'Tier 2 Extracted')}
                  </span>
                </div>
              </div>

              <!-- Confidence Meter -->
              <div class="confidence-meter" title="Extraction confidence: ${confPct}%">
                <span style="font-size: 0.72rem; font-weight: 700; font-family: var(--font-mono); color: #475569;">${confPct}%</span>
                <div class="confidence-bar-bg">
                  <div class="confidence-bar-fill ${confClass}" style="width: ${confPct}%;"></div>
                </div>
                <span style="font-size: 0.7rem; color: #64748b;">Confidence</span>
              </div>

              <!-- Meta info -->
              <div class="curation-meta-row">
                <span>🏛️ ${escapeHtml(s.department || 'Government of Karnataka')}</span>
                <span>•</span>
                <span>📌 ${escapeHtml(s.level || 'State')}</span>
                ${s.is_placeholder ? '<span style="background: #f1f5f9; padding: 1px 5px; border-radius: 3px; color: #64748b; font-size: 0.68rem;">PLACEHOLDER</span>' : ''}
              </div>

              <!-- Summary -->
              <div class="curation-summary">
                ${escapeHtml(s.summary_en || 'No plain-language summary provided.')}
              </div>
            </div>

            <!-- Card Actions -->
            <div class="curation-card-actions">
              <button class="btn btn-primary" onclick="openCurationModal('${escapeHtml(s.id)}')" style="font-size: 0.75rem; padding: 0.35rem 0.65rem;">
                🔍 Curate & Inspect
              </button>

              ${!isVerified ? `
                <button class="btn btn-secondary" onclick="submitCurationDecision('${escapeHtml(s.id)}', 'promote')" style="font-size: 0.75rem; padding: 0.35rem 0.65rem; color: #16a34a; border-color: #86efac;">
                  ⭐ Approve (Tier 1)
                </button>
              ` : ''}

              ${!isRejected ? `
                <button class="btn btn-secondary" onclick="submitCurationDecision('${escapeHtml(s.id)}', 'reject')" style="font-size: 0.75rem; padding: 0.35rem 0.65rem; color: #dc2626; border-color: #fca5a5;">
                  ⛔ Reject
                </button>
              ` : ''}
            </div>
          </div>
        `;
      });
      html += `</div>`;
    }

    document.getElementById('view-container').innerHTML = html;
  } catch (err) {
    document.getElementById('view-container').innerHTML = `<div style="color: red; padding: 2rem;">Error loading curation queue: ${err.message}</div>`;
  }
}

async function openCurationModal(schemeId) {
  try {
    const res = await fetch(`/api/admin/review/${schemeId}`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Scheme not found');
    const data = await res.json();
    const scheme = data.parsed_json || data.scheme || JSON.parse(data.raw_json || '{}');
    const criteria = scheme.eligibility?.criteria || [];
    const exclusions = scheme.eligibility?.exclusions || [];

    const rawJsonPretty = JSON.stringify(scheme, null, 2);

    let modalHtml = `
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <!-- Header Info -->
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div>
              <h4 style="font-size: 1.05rem; font-weight: 700; color: #0f172a;">${escapeHtml(scheme.names?.en || scheme.id)}</h4>
              <p style="font-family: var(--font-mono); font-size: 0.75rem; color: #64748b;">${escapeHtml(scheme.id)}</p>
            </div>
            <div>
              <span class="badge ${scheme.tier === 'verified' ? 'badge-verified' : 'badge-extracted'}">
                Tier: ${scheme.tier} | Status: ${scheme.status}
              </span>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; font-size: 0.8rem; margin-top: 0.75rem;">
            <div><span style="color: #64748b;">Department:</span> <strong>${escapeHtml(scheme.department || '—')}</strong></div>
            <div><span style="color: #64748b;">Level / State:</span> <strong>${escapeHtml(scheme.level || 'state')} (${escapeHtml(scheme.state || 'Karnataka')})</strong></div>
            <div><span style="color: #64748b;">Confidence:</span> <strong>${Math.round((scheme.confidence || 0) * 100)}%</strong></div>
            <div><span style="color: #64748b;">Official URL:</span> <a href="${escapeHtml(scheme.official_url || '#')}" target="_blank" style="color: #0284c7; text-decoration: underline;">Portal Link ↗</a></div>
          </div>
        </div>

        <!-- Section 1: Summary & Benefit -->
        <div>
          <h5 style="font-weight: 700; font-size: 0.85rem; color: #1e293b; margin-bottom: 0.35rem;">Plain-Language Summary & Benefit</h5>
          <p style="font-size: 0.82rem; color: #334155; line-height: 1.45; background: #ffffff; border: 1px solid #e2e8f0; padding: 0.75rem; border-radius: 4px;">
            ${escapeHtml(scheme.summary_en || 'No summary')}
          </p>
          <div style="font-size: 0.8rem; margin-top: 0.4rem; color: #475569;">
            <strong>Benefit:</strong> ${escapeHtml(scheme.benefit?.description || 'N/A')} (${escapeHtml(scheme.benefit?.type || 'cash')})
          </div>
        </div>

        <!-- Section 2: Structured Eligibility Rules (Editable Criteria) -->
        <div>
          <h5 style="font-weight: 700; font-size: 0.85rem; color: #1e293b; margin-bottom: 0.35rem;">
            Structured Eligibility Rules (${criteria.length} Criteria, ${exclusions.length} Exclusions)
          </h5>
          <div class="pma-table-wrapper" style="max-height: 220px;">
            <table class="pma-grid">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Field</th>
                  <th>Operator</th>
                  <th>Target Value</th>
                  <th>Human Explanation</th>
                </tr>
              </thead>
              <tbody>
    `;

    criteria.forEach(c => {
      modalHtml += `
        <tr>
          <td><span style="color: #16a34a; font-weight: 700;">Criterion</span></td>
          <td><code style="font-weight: 700;">${escapeHtml(c.field)}</code></td>
          <td><code>${escapeHtml(c.op)}</code></td>
          <td><code>${escapeHtml(JSON.stringify(c.value))}</code></td>
          <td style="color: #475569;">${escapeHtml(c.text_en || '—')}</td>
        </tr>
      `;
    });

    exclusions.forEach(e => {
      modalHtml += `
        <tr>
          <td><span style="color: #dc2626; font-weight: 700;">Exclusion</span></td>
          <td><code style="font-weight: 700;">${escapeHtml(e.field)}</code></td>
          <td><code>${escapeHtml(e.op)}</code></td>
          <td><code>${escapeHtml(JSON.stringify(e.value))}</code></td>
          <td style="color: #475569;">${escapeHtml(e.text_en || '—')}</td>
        </tr>
      `;
    });

    modalHtml += `
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 3: Raw JSON Definition (Editable) -->
        <div>
          <h5 style="font-weight: 700; font-size: 0.85rem; color: #1e293b; margin-bottom: 0.35rem;">
            Raw Scheme Definition & Extracted JSON Payload
          </h5>
          <textarea id="curation-json-payload" class="column-textarea" style="height: 180px; font-family: var(--font-mono); font-size: 0.78rem;">${escapeHtml(rawJsonPretty)}</textarea>
        </div>

        <!-- Section 4: Review Decision Form -->
        <div style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 1rem;">
          <h5 style="font-weight: 700; font-size: 0.85rem; color: #1e293b; margin-bottom: 0.5rem;">Curation Officer Sign-off</h5>
          <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 0.75rem; margin-bottom: 0.85rem;">
            <div>
              <label style="font-size: 0.75rem; font-weight: 600; color: #475569; display: block; margin-bottom: 0.2rem;">Reviewer Identity:</label>
              <input type="text" id="curation-reviewer-name" class="column-input" value="${escapeHtml(currentUser ? currentUser.name : 'Divya Patel')}" placeholder="Reviewer name">
            </div>
            <div>
              <label style="font-size: 0.75rem; font-weight: 600; color: #475569; display: block; margin-bottom: 0.2rem;">Review Notes / Official Gazette Reference:</label>
              <input type="text" id="curation-review-notes" class="column-input" value="${escapeHtml(data.review_notes || 'Verified against official department gazette')}" placeholder="Enter audit notes...">
            </div>
          </div>

          <div style="display: flex; gap: 0.5rem; justify-content: flex-end; flex-wrap: wrap;">
            <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
            <button type="button" class="btn btn-danger" onclick="submitCurationDecision('${schemeId}', 'reject')">
              ❌ Reject Scheme
            </button>
            <button type="button" class="btn btn-secondary" onclick="submitCurationDecision('${schemeId}', 'update')">
              💾 Save & Update Changes
            </button>
            <button type="button" class="btn btn-primary" onclick="submitCurationDecision('${schemeId}', 'promote')" style="background: #15803d;">
              ⭐ Approve & Promote to Tier 1
            </button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-title').innerText = `🛡️ Curate Scheme: ${scheme.names?.en || schemeId}`;
    document.getElementById('modal-body-content').innerHTML = modalHtml;
    document.getElementById('generic-modal').style.display = 'flex';
  } catch (err) {
    alert('Failed to load scheme for curation: ' + err.message);
  }
}

async function submitCurationDecision(schemeId, action) {
  let reviewer = currentUser ? currentUser.name : 'Divya Patel';
  let notes = 'Processed via DBControl Curation Console';
  let updatedData = null;

  const reviewerInput = document.getElementById('curation-reviewer-name');
  if (reviewerInput && reviewerInput.value.trim()) reviewer = reviewerInput.value.trim();

  const notesInput = document.getElementById('curation-review-notes');
  if (notesInput && notesInput.value.trim()) notes = notesInput.value.trim();

  const jsonInput = document.getElementById('curation-json-payload');
  if (jsonInput) {
    try {
      updatedData = JSON.parse(jsonInput.value.trim());
    } catch (e) {
      alert('Invalid JSON in payload editor: ' + e.message);
      return;
    }
  }

  const promptMsg = action === 'promote' 
    ? `Approve scheme '${schemeId}' and promote to Tier 1 Verified?`
    : (action === 'reject' ? `Mark scheme '${schemeId}' as REJECTED?` : `Save updates to scheme '${schemeId}'?`);

  if (!confirm(promptMsg)) return;

  try {
    const res = await fetch(`/api/admin/review/${schemeId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        action,
        reviewer,
        notes,
        updated_data: updatedData
      })
    });

    const resData = await res.json();
    if (res.ok && resData.status === 'success') {
      alert(`✅ Curation action '${action}' completed successfully for '${schemeId}'!`);
      closeGenericModal();
      refreshSidebarTables();
      if (currentView === 'review') renderReviewQueueView();
      else if (currentView === 'browse') renderBrowseView();
    } else {
      alert('Curation failed: ' + (resData.detail || JSON.stringify(resData)));
    }
  } catch (err) {
    alert('Network error: ' + err.message);
  }
}

/* ============================================================
   Phase 5: Document Ingestion Pipeline Runner
   ============================================================ */

async function renderPipelineIngestionView() {
  try {
    const res = await fetch('/api/admin/rejections', { headers: getAuthHeaders() });
    const rejections = await res.json();

    let html = `
      <div style="margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--pma-blue-dark); margin-bottom: 0.25rem;">
          🚀 Document Ingestion Pipeline
        </h2>
        <p style="font-size: 0.8rem; color: var(--pma-text-muted);">
          Offline/local pipeline turns government policy documents from <code>data/raw/</code> into structured Tier 2 schemes with zero hallucination.
        </p>
      </div>

      <div class="pipeline-panel">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;">
          Pipeline Execution Controls
        </h4>
        <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 1rem;">
          Pipeline steps: <strong>1. DocumentReader</strong> (PDF / TXT extraction) ➔ <strong>2. LLM Extractor</strong> (JSON Schema mapping) ➔ <strong>3. SchemeValidator</strong> (strict bounds & official URL check) ➔ <strong>4. Embedding Indexer</strong>.
        </p>

        <div style="display: flex; gap: 0.6rem; flex-wrap: wrap;">
          <button class="btn btn-primary" onclick="runPipelineIngestion(false, false)" id="btn-ingest-run">
            ▶️ Run Full Pipeline Ingestion
          </button>
          <button class="btn btn-secondary" onclick="runPipelineIngestion(true, false)" id="btn-ingest-dry">
            🧪 Dry Run Test
          </button>
          <button class="btn btn-secondary" onclick="runPipelineIngestion(false, true)" id="btn-ingest-force">
            🔄 Force Re-process All Files
          </button>
        </div>

        <div class="pipeline-terminal" id="pipeline-terminal-output">
[Ingestion Pipeline Ready]
Target directory: data/raw/
Output schema: Tier 2 (schemes_extracted.json)
Embedding index: ChromaDB / scheme_embeddings.json
Click "Run Full Pipeline Ingestion" to process new documents.
        </div>
      </div>

      <!-- Rejected Documents Section -->
      <div class="pipeline-panel">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;">
          Rejection Repository (${rejections.length} items)
        </h4>
        <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 1rem;">
          Documents rejected by the SchemeValidator (missing official URLs, impossible eligibility ages, or currency confusion):
        </p>

        <div class="pma-table-wrapper">
          <table class="pma-grid">
            <thead>
              <tr>
                <th>Document File</th>
                <th>Rejection Reason</th>
                <th>Rejected At</th>
              </tr>
            </thead>
            <tbody>
    `;

    if (rejections.length === 0) {
      html += `<tr><td colspan="3" style="text-align: center; color: #94a3b8; padding: 1.5rem;">No rejected documents in repository. All processed documents are valid.</td></tr>`;
    } else {
      rejections.forEach(r => {
        html += `
          <tr>
            <td><code style="font-weight: 700;">${escapeHtml(r.filename || r.id || 'document')}</code></td>
            <td style="color: #dc2626;">${escapeHtml(r.reason || 'Failed schema validation')}</td>
            <td style="color: #64748b;">${escapeHtml(r.rejected_at || '—')}</td>
          </tr>
        `;
      });
    }

    html += `
            </tbody>
          </table>
        </div>
      </div>
    `;

    document.getElementById('view-container').innerHTML = html;
  } catch (err) {
    document.getElementById('view-container').innerHTML = `<div style="color: red; padding: 2rem;">Error loading pipeline view: ${err.message}</div>`;
  }
}

async function runPipelineIngestion(dryRun = false, reprocess = false) {
  const terminal = document.getElementById('pipeline-terminal-output');
  if (terminal) {
    terminal.innerText = `[${new Date().toLocaleTimeString()}] Starting pipeline execution (dry_run=${dryRun}, reprocess=${reprocess})...\nScanning data/raw/...`;
  }

  const btn = document.getElementById('btn-ingest-run');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`/api/admin/ingest?dry_run=${dryRun}&reprocess=${reprocess}`, {
      method: 'POST',
      headers: getAuthHeaders()
    });

    const data = await res.json();
    if (res.ok) {
      let log = `[${new Date().toLocaleTimeString()}] Pipeline completed successfully!\n`;
      log += `Total Files Checked: ${data.total}\n\n`;
      (data.results || []).forEach((r, idx) => {
        log += `[#${idx + 1}] File: ${r.file_path}\n`;
        log += `    Status: ${r.status}\n`;
        if (r.scheme_id) log += `    Extracted Scheme ID: ${r.scheme_id}\n`;
        if (r.error) log += `    Warning/Error: ${r.error}\n`;
        log += `------------------------------------------------------------\n`;
      });
      if (terminal) terminal.innerText = log;
      refreshSidebarTables();
    } else {
      if (terminal) terminal.innerText = `[Error] Ingestion failed: ${data.detail || JSON.stringify(data)}`;
    }
  } catch (err) {
    if (terminal) terminal.innerText = `[Network Error] ${err.message}`;
  } finally {
    if (btn) btn.disabled = false;
  }
}
