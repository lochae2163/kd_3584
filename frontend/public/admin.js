// ========================================
// Configuration
// ========================================
const API_URL = 'https://kd3584-production.up.railway.app';

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
    return new Date(dateString).toLocaleString();
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
                    ` : `
                        <p>No current data uploaded yet</p>
                    `}
                </div>
            </div>
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
// Initialize
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    loadDataStatus();
    loadHistory();
});