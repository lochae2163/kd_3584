// ========================================
// Configuration
// ========================================
// Use localhost for development, production URL for deployed site
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://kd3584-production.up.railway.app';

// ========================================
// DOM Elements
// ========================================
const dataStatus = document.getElementById('data-status');
const baselineForm = document.getElementById('baseline-form');
const baselineMessage = document.getElementById('baseline-message');
const currentForm = document.getElementById('current-form');
const currentMessage = document.getElementById('current-message');
const historyList = document.getElementById('history-list');

// ========================================
// Utility Functions
// ========================================
function showMessage(element, type, message) {
    element.innerHTML = `<div class="message ${type}">${message}</div>`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        timeZone: 'UTC',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    }) + ' UTC';
}

function formatNumber(num) {
    if (!num) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

// ========================================
// Load Data Status
// ========================================
async function loadDataStatus() {
    const seasonId = document.getElementById('baseline-season').value || 'season_1';

    try {
        const response = await fetch(`${API_URL}/admin/data-status/${seasonId}`);
        const data = await response.json();

        let html = `
            <div class="status-grid">
                <div class="status-card ${data.has_baseline ? 'active' : 'inactive'}">
                    <h3>${data.has_baseline ? '✅' : '❌'} Baseline</h3>
                    ${data.has_baseline ? `
                        <p><strong>File:</strong> ${data.baseline_info.file_name}</p>
                        <p><strong>Players:</strong> ${data.baseline_info.player_count}</p>
                        <p><strong>Uploaded:</strong> ${formatDate(data.baseline_info.timestamp)}</p>
                        <button class="delete-btn" onclick="deleteBaseline()">🗑️ Delete Baseline</button>
                    ` : `
                        <p>No baseline uploaded yet</p>
                    `}
                </div>
                <div class="status-card ${data.has_current ? 'active' : 'inactive'}">
                    <h3>${data.has_current ? '✅' : '❌'} Current Data</h3>
                    ${data.has_current ? `
                        <p><strong>File:</strong> ${data.current_info.file_name}</p>
                        <p><strong>Players:</strong> ${data.current_info.player_count}</p>
                        <p><strong>Description:</strong> ${data.current_info.description || 'N/A'}</p>
                        <p><strong>Updated:</strong> ${formatDate(data.current_info.timestamp)}</p>
                        <button class="delete-btn" onclick="deleteCurrent()">🗑️ Delete Current Data</button>
                    ` : `
                        <p>No current data uploaded yet</p>
                    `}
                </div>
            </div>
            ${data.has_baseline || data.has_current ? `
                <div class="danger-zone">
                    <h4>⚠️ Danger Zone</h4>
                    <p>Delete ALL data for this season (baseline + current + history). This cannot be undone!</p>
                    <button class="delete-all-btn" onclick="deleteAllData()">💥 Delete All Data</button>
                </div>
            ` : ''}
        `;

        dataStatus.innerHTML = html;

    } catch (error) {
        dataStatus.innerHTML = `<div class="message error">Failed to load status: ${error.message}</div>`;
    }
}

// ========================================
// Load Upload History
// ========================================
async function loadHistory() {
    const seasonId = document.getElementById('baseline-season').value || 'season_1';
    
    try {
        const response = await fetch(`${API_URL}/admin/history/${seasonId}`);
        const data = await response.json();
        
        if (data.history.length === 0) {
            historyList.innerHTML = '<div class="empty-history">No uploads yet</div>';
            return;
        }
        
        historyList.innerHTML = data.history.map((item, index) => `
            <div class="history-item">
                <div class="history-number">#${data.history.length - index}</div>
                <div class="history-info">
                    <div class="history-desc">${item.description || 'No description'}</div>
                    <div class="history-meta">
                        <span>📁 ${item.file_name}</span>
                        <span>👥 ${item.player_count} players</span>
                        <span>🕐 ${formatDate(item.timestamp)}</span>
                    </div>
                    ${item.summary ? `
                        <div class="history-summary">
                            Total KP: ${formatNumber(item.summary.totals?.kill_points || 0)} • 
                            Total Power: ${formatNumber(item.summary.totals?.power || 0)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        historyList.innerHTML = `<div class="message error">Failed to load history: ${error.message}</div>`;
    }
}

// ========================================
// Upload Baseline
// ========================================
baselineForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = document.getElementById('baseline-file').files[0];
    const seasonId = document.getElementById('baseline-season').value;
    
    if (!file) {
        showMessage(baselineMessage, 'error', '❌ Please select a CSV file');
        return;
    }
    
    // Show loading
    showMessage(baselineMessage, 'info', '⏳ Uploading...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(
            `${API_URL}/admin/upload/baseline?kvk_season_id=${seasonId}`,
            { 
                method: 'POST', 
                body: formData,
                mode: 'cors'  // Add this
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const result = await response.json();
        
        showMessage(baselineMessage, 'success', `
            ✅ Baseline uploaded successfully!<br>
            <strong>Players:</strong> ${result.player_count}<br>
            <strong>Season:</strong> ${result.kvk_season_id}
        `);
        document.getElementById('baseline-file').value = '';
        loadDataStatus();
        loadHistory();
        loadFileManagement();
        
    } catch (error) {
        showMessage(baselineMessage, 'error', `❌ Upload failed: ${error.message}`);
    }
});

// ========================================
// Upload Current Data
// ========================================
currentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = document.getElementById('current-file').files[0];
    const seasonId = document.getElementById('current-season').value;
    const description = document.getElementById('description').value;
    
    if (!file) {
        showMessage(currentMessage, 'error', '❌ Please select a CSV file');
        return;
    }
    
    // Show loading
    showMessage(currentMessage, 'info', '⏳ Uploading...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(
            `${API_URL}/admin/upload/current?kvk_season_id=${seasonId}&description=${encodeURIComponent(description)}`,
            { 
                method: 'POST', 
                body: formData,
                mode: 'cors'  // Add this
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const result = await response.json();
        
        showMessage(currentMessage, 'success', `
            ✅ Current data uploaded successfully!<br>
            <strong>Players:</strong> ${result.player_count}<br>
            <strong>Description:</strong> ${result.description || 'N/A'}
        `);
        document.getElementById('current-file').value = '';
        document.getElementById('description').value = '';
        loadDataStatus();
        loadHistory();
        loadFileManagement();
        
    } catch (error) {
        showMessage(currentMessage, 'error', `❌ Upload failed: ${error.message}`);
    }
});

// ========================================
// Season ID Change Handler
// ========================================
document.getElementById('baseline-season').addEventListener('change', () => {
    loadDataStatus();
    loadHistory();
});

document.getElementById('current-season').addEventListener('change', (e) => {
    document.getElementById('baseline-season').value = e.target.value;
    loadDataStatus();
    loadHistory();
});

// ========================================
// Delete Functions
// ========================================
async function deleteBaseline() {
    const seasonId = document.getElementById('baseline-season').value || 'season_1';

    const confirmed = confirm(
        '⚠️ WARNING: Delete Baseline?\n\n' +
        'This will remove the baseline reference point.\n' +
        'Current data comparisons will fail without a baseline.\n\n' +
        'Are you sure you want to delete the baseline?'
    );

    if (!confirmed) return;

    try {
        const response = await fetch(
            `${API_URL}/admin/delete/baseline/${seasonId}`,
            { method: 'DELETE' }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }

        const result = await response.json();

        alert(`✅ ${result.message}\n\nDeleted file: ${result.deleted_file}\nPlayers: ${result.deleted_player_count}`);

        loadDataStatus();
        loadHistory();

    } catch (error) {
        alert(`❌ Delete failed: ${error.message}`);
    }
}

async function deleteCurrent() {
    const seasonId = document.getElementById('baseline-season').value || 'season_1';

    const confirmed = confirm(
        '⚠️ WARNING: Delete Current Data?\n\n' +
        'This will remove:\n' +
        '• Current data snapshot\n' +
        '• All upload history entries\n\n' +
        'Baseline will remain intact.\n\n' +
        'Are you sure you want to delete?'
    );

    if (!confirmed) return;

    try {
        const response = await fetch(
            `${API_URL}/admin/delete/current/${seasonId}`,
            { method: 'DELETE' }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }

        const result = await response.json();

        alert(
            `✅ ${result.message}\n\n` +
            `Deleted file: ${result.deleted_file}\n` +
            `History entries removed: ${result.deleted_history_count}`
        );

        loadDataStatus();
        loadHistory();

    } catch (error) {
        alert(`❌ Delete failed: ${error.message}`);
    }
}

async function deleteAllData() {
    const seasonId = document.getElementById('baseline-season').value || 'season_1';

    const firstConfirm = confirm(
        '🚨 DANGER: Delete ALL Data?\n\n' +
        'This will PERMANENTLY delete:\n' +
        '• Baseline data\n' +
        '• Current data\n' +
        '• All upload history\n\n' +
        'This action CANNOT be undone!\n\n' +
        'Are you absolutely sure?'
    );

    if (!firstConfirm) return;

    // Second confirmation for extra safety
    const secondConfirm = confirm(
        `🚨 FINAL WARNING!\n\n` +
        `You are about to delete ALL data for ${seasonId}.\n\n` +
        `Type the season ID in your mind to confirm: ${seasonId}\n\n` +
        `Click OK to proceed with PERMANENT deletion.`
    );

    if (!secondConfirm) return;

    try {
        const response = await fetch(
            `${API_URL}/admin/delete/all/${seasonId}`,
            { method: 'DELETE' }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }

        const result = await response.json();

        alert(
            `✅ ${result.message}\n\n` +
            `Baseline deleted: ${result.deleted_baseline}\n` +
            `Current deleted: ${result.deleted_current}\n` +
            `History deleted: ${result.deleted_history}\n` +
            `Total records removed: ${result.total_deleted}`
        );

        loadDataStatus();
        loadHistory();

    } catch (error) {
        alert(`❌ Delete failed: ${error.message}`);
    }
}

// ========================================
// File Management
// ========================================
async function loadFileManagement() {
    await loadBaselineFiles();
    await loadHistoryFiles();
}

async function loadBaselineFiles() {
    const container = document.getElementById('baseline-files-table');

    try {
        const response = await fetch(`${API_URL}/admin/data-status/season_1`);
        const data = await response.json();

        if (data.baseline_info) {
            const baseline = data.baseline_info;
            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>File Name</th>
                            <th>Players</th>
                            <th>Uploaded (UTC)</th>
                            <th>Sheet</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>${baseline.file_name}</strong></td>
                            <td>${baseline.player_count} players</td>
                            <td>${formatDate(baseline.timestamp)}</td>
                            <td>${baseline.sheet_used || 'N/A'}</td>
                            <td>
                                <button class="file-delete-btn" onclick="deleteBaseline()">
                                    🗑️ Delete
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            `;
        } else {
            container.innerHTML = '<div class="empty-files">No baseline data uploaded yet</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-files">Error loading baseline files</div>';
        console.error('Error loading baseline files:', error);
    }
}

async function loadHistoryFiles() {
    const container = document.getElementById('history-files-table');

    try {
        const response = await fetch(`${API_URL}/admin/history/season_1`);
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            const rows = data.history.map((item, index) => `
                <tr>
                    <td><strong>#${data.history.length - index}</strong></td>
                    <td>${item.file_name}</td>
                    <td>${item.player_count} players</td>
                    <td>${item.description || 'No description'}</td>
                    <td>${formatDate(item.timestamp)}</td>
                    <td>${item.sheet_used || 'N/A'}</td>
                    <td>
                        <button class="file-delete-btn" onclick="deleteHistoryFile('${item._id}', '${item.file_name}')">
                            🗑️ Delete
                        </button>
                    </td>
                </tr>
            `).join('');

            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>File Name</th>
                            <th>Players</th>
                            <th>Description</th>
                            <th>Uploaded (UTC)</th>
                            <th>Sheet</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            `;
        } else {
            container.innerHTML = '<div class="empty-files">No current data uploaded yet</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-files">Error loading history files</div>';
        console.error('Error loading history files:', error);
    }
}

async function deleteHistoryFile(historyId, fileName) {
    if (!confirm(`Delete "${fileName}"?\n\nThis will remove this upload from history but won't affect the current leaderboard unless this was the most recent upload.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/delete/history/${historyId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ File deleted successfully: ${fileName}`);
            // Reload both tables
            await loadFileManagement();
        } else {
            throw new Error(result.error || 'Delete failed');
        }
    } catch (error) {
        alert(`❌ Delete failed: ${error.message}`);
    }
}

// ========================================
// Initialize
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    loadDataStatus();
    loadHistory();
    loadFileManagement();
});