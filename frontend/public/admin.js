// ========================================
// Configuration
// ========================================
// API_URL, formatDate, formatNumber, showMessage are now in utilities.js

// ========================================
// Authentication Helper
// ========================================
function getAuthHeaders() {
    const token = localStorage.getItem('admin_token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

function handleAuthError(response) {
    if (response.status === 401 || response.status === 403) {
        // Token invalid or expired, redirect to login
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_username');
        window.location.href = 'admin-login.html';
        return true;
    }
    return false;
}

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
// Utility functions (showMessage, formatDate, formatNumber) moved to utilities.js

// ========================================
// Load Data Status
// ========================================
async function loadDataStatus() {
    if (!activeSeason) {
        dataStatus.innerHTML = '<div class="loading">Loading...</div>';
        return;
    }

    const seasonId = activeSeason.season_id;

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
    if (!activeSeason) {
        historyList.innerHTML = '<div class="loading">Loading...</div>';
        return;
    }

    const seasonId = activeSeason.season_id;

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

    if (!activeSeason) {
        container.innerHTML = '<div class="loading">No active season</div>';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/data-status/${activeSeason.season_id}`);
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

    if (!activeSeason) {
        container.innerHTML = '<div class="loading">No active season</div>';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/history/${activeSeason.season_id}`);
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
// Season Management
// ========================================
let activeSeason = null;

async function loadSeasons() {
    const seasonManagement = document.getElementById('season-management');

    try {
        // Use public API endpoints (no auth required for reading season info)
        const [allResponse, activeResponse] = await Promise.all([
            fetch(`${API_URL}/api/seasons/all`),
            fetch(`${API_URL}/api/seasons/active`)
        ]);

        const allData = await allResponse.json();
        const activeData = await activeResponse.json();

        // Handle different response structures
        activeSeason = activeData.season || activeData; // activeData might be the season itself
        const seasons = allData.seasons || [];

        // Auto-populate season fields
        if (activeSeason) {
            document.getElementById('baseline-season').value = activeSeason.season_id;
            document.getElementById('current-season').value = activeSeason.season_id;
        }

        let html = `
            <div class="season-header">
                <div class="active-season-banner">
                    <h3>🎯 Active Season: ${activeSeason ? activeSeason.season_name : 'None'}</h3>
                    <p>All uploads will go to: <strong>${activeSeason ? activeSeason.season_id : 'N/A'}</strong></p>
                </div>
                <button class="create-season-btn" onclick="showCreateSeasonModal()">➕ Create New Season</button>
            </div>

            <div class="seasons-grid">
        `;

        seasons.forEach(season => {
            const isActive = season.is_active;
            const isArchived = season.is_archived;
            const statusClass = isArchived ? 'archived' : isActive ? 'active' : season.status;
            const statusEmoji = isArchived ? '🔒' : isActive ? '✅' : season.status === 'preparing' ? '⏳' : '✓';

            const startDateValue = season.start_date ? new Date(season.start_date).toISOString().split('T')[0] : '';
            const endDateValue = season.end_date ? new Date(season.end_date).toISOString().split('T')[0] : '';

            html += `
                <div class="season-card ${statusClass}">
                    <div class="season-header-card">
                        <h4>${season.season_name}</h4>
                        <span class="season-badge ${statusClass}">${statusEmoji} ${isArchived ? 'Archived' : isActive ? 'Active' : season.status}</span>
                    </div>
                    <div class="season-stats">
                        <p><strong>Season ID:</strong> ${season.season_id}</p>
                        <p><strong>Players:</strong> ${formatNumber(season.player_count)}</p>
                        <p><strong>Uploads:</strong> ${season.total_uploads}</p>
                        <p><strong>Baseline:</strong> ${season.has_baseline ? '✅' : '❌'}</p>
                        <p><strong>Current Data:</strong> ${season.has_current_data ? '✅' : '❌'}</p>

                        <div class="season-dates-edit">
                            <div class="date-edit-group">
                                <label><strong>📅 Start Date:</strong></label>
                                <input type="date" id="start-date-${season.season_id}" value="${startDateValue}"
                                    ${isArchived ? 'disabled' : ''}
                                    onchange="updateSeasonDates('${season.season_id}')">
                            </div>
                            <div class="date-edit-group">
                                <label><strong>🏁 End Date:</strong></label>
                                <input type="date" id="end-date-${season.season_id}" value="${endDateValue}"
                                    ${isArchived ? 'disabled' : ''}
                                    onchange="updateSeasonDates('${season.season_id}')">
                            </div>
                        </div>
                    </div>
                    <div class="season-actions">
                        ${!isActive && !isArchived ? `
                            <button class="activate-btn" onclick="activateSeason('${season.season_id}')">
                                🎯 Activate
                            </button>
                        ` : ''}
                        ${isActive && !season.final_data_uploaded ? `
                            <button class="mark-final-btn" onclick="markFinalDataUploaded('${season.season_id}')">
                                ✓ Mark Final Data
                            </button>
                        ` : ''}
                        ${!isArchived && season.status === 'completed' ? `
                            <button class="archive-btn" onclick="archiveSeason('${season.season_id}')">
                                🔒 Archive
                            </button>
                        ` : ''}
                        <button class="view-stats-btn" onclick="viewSeasonStats('${season.season_id}')">
                            📊 View Stats
                        </button>
                    </div>
                </div>
            `;
        });

        html += `</div>`;

        seasonManagement.innerHTML = html;

        // Load player classification after activeSeason is set
        await loadPlayerClassification();

    } catch (error) {
        seasonManagement.innerHTML = `<div class="message error">Failed to load seasons: ${error.message}</div>`;
    }
}

async function activateSeason(seasonId) {
    if (!confirm(`Activate ${seasonId}? This will deactivate all other seasons.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/seasons/activate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ season_id: seasonId })
        });

        if (handleAuthError(response)) return;

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ ${seasonId} is now active!`);
            await loadSeasons();
            await loadDataStatus();
        } else {
            throw new Error(result.error || 'Activation failed');
        }
    } catch (error) {
        alert(`❌ Activation failed: ${error.message}`);
    }
}

async function archiveSeason(seasonId) {
    if (!confirm(`⚠️ Archive ${seasonId}? This will make the season READ-ONLY. You cannot upload new data after archiving. Continue?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/seasons/archive`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ season_id: seasonId, confirm: true })
        });

        if (handleAuthError(response)) return;

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ ${seasonId} has been archived!`);
            await loadSeasons();
        } else {
            throw new Error(result.error || 'Archive failed');
        }
    } catch (error) {
        alert(`❌ Archive failed: ${error.message}`);
    }
}

async function markFinalDataUploaded(seasonId) {
    if (!confirm(`Mark final data as uploaded for ${seasonId}? This indicates KvK is complete.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/seasons/${seasonId}/mark-final-uploaded`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ Final data marked for ${seasonId}!`);
            await loadSeasons();
        } else {
            throw new Error(result.error || 'Mark failed');
        }
    } catch (error) {
        alert(`❌ Mark failed: ${error.message}`);
    }
}

async function updateSeasonDates(seasonId) {
    const startDateInput = document.getElementById(`start-date-${seasonId}`);
    const endDateInput = document.getElementById(`end-date-${seasonId}`);

    const startDate = startDateInput.value ? `${startDateInput.value}T00:00:00` : null;
    const endDate = endDateInput.value ? `${endDateInput.value}T23:59:59` : null;

    try {
        const response = await fetch(`${API_URL}/admin/seasons/${seasonId}/update-dates`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate
            })
        });

        if (handleAuthError(response)) return;

        const result = await response.json();

        if (response.ok && result.success) {
            // Show success notification (subtle, non-intrusive)
            const notification = document.createElement('div');
            notification.className = 'date-update-notification';
            notification.textContent = `✅ Dates updated for ${seasonId}`;
            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 12px 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 10000; animation: slideIn 0.3s ease;';
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 2000);

            // Reload seasons to show updated data
            await loadSeasons();
        } else {
            throw new Error(result.error || 'Date update failed');
        }
    } catch (error) {
        alert(`❌ Failed to update dates: ${error.message}`);
    }
}

async function viewSeasonStats(seasonId) {
    try {
        // Use public API endpoint (no auth required)
        const response = await fetch(`${API_URL}/api/seasons/${seasonId}/stats`);
        const result = await response.json();

        if (response.ok && result.success) {
            const stats = result.stats;
            alert(`📊 ${seasonId} Stats:\n\n` +
                `Players: ${stats.player_count}\n` +
                `Uploads: ${stats.total_uploads}\n` +
                `Has Baseline: ${stats.has_baseline ? 'Yes' : 'No'}\n` +
                `Has Current Data: ${stats.has_current_data ? 'Yes' : 'No'}\n` +
                `Final Data: ${stats.final_data_uploaded ? 'Yes' : 'No'}\n` +
                `Status: ${stats.status}\n` +
                `Active: ${stats.is_active ? 'Yes' : 'No'}\n` +
                `Archived: ${stats.is_archived ? 'Yes' : 'No'}`
            );
        } else {
            throw new Error(result.error || 'Failed to get stats');
        }
    } catch (error) {
        alert(`❌ Failed to load stats: ${error.message}`);
    }
}

function showCreateSeasonModal() {
    const seasonName = prompt('Enter season name (e.g., "KvK 7 - Kingdom 3584"):');
    if (!seasonName) return;

    const description = prompt('Enter description (optional):') || '';

    createSeason(seasonName, description);
}

async function createSeason(seasonName, description) {
    try {
        const response = await fetch(`${API_URL}/admin/seasons/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                season_name: seasonName,
                description: description,
                kingdom_id: '3584'
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ Created ${result.season.season_id}: ${seasonName}`);
            await loadSeasons();
        } else {
            throw new Error(result.error || 'Creation failed');
        }
    } catch (error) {
        alert(`❌ Creation failed: ${error.message}`);
    }
}

// ========================================
// Player Classification
// ========================================
async function loadPlayerClassification() {
    const playerClassification = document.getElementById('player-classification');

    if (!activeSeason) {
        playerClassification.innerHTML = `<div class="message warning">No active season. Please activate a season first.</div>`;
        return;
    }

    try {
        const [playersResponse, summaryResponse] = await Promise.all([
            fetch(`${API_URL}/admin/players/all-with-classification/${activeSeason.season_id}`, {
                headers: getAuthHeaders()
            }),
            fetch(`${API_URL}/admin/players/stats/classification-summary/${activeSeason.season_id}`, {
                headers: getAuthHeaders()
            })
        ]);

        if (!playersResponse.ok || !summaryResponse.ok) {
            throw new Error(`API error: ${playersResponse.status} / ${summaryResponse.status}`);
        }

        const playersData = await playersResponse.json();
        const summaryData = await summaryResponse.json();


        const players = playersData.players || [];
        const summary = summaryData.summary || {};

        let html = `
            <div class="classification-header">
                <div class="classification-summary">
                    <h3>Classification Summary</h3>
                    <div class="summary-stats">
                        <div class="stat-item">
                            <span class="stat-label">Total Players:</span>
                            <span class="stat-value">${summary.total_players || 0}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Main Accounts:</span>
                            <span class="stat-value main">${summary.main_accounts || 0}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Farm Accounts:</span>
                            <span class="stat-value farm">${summary.farm_accounts || 0}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Vacation:</span>
                            <span class="stat-value vacation">${summary.vacation_accounts || 0}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Farm Links:</span>
                            <span class="stat-value">${summary.total_farm_links || 0}</span>
                        </div>
                    </div>
                </div>
                <div class="classification-filters">
                    <input type="text" id="player-search" placeholder="🔍 Search player name or ID..." class="player-search-input">
                    <select id="type-filter" class="type-filter">
                        <option value="all">All Types</option>
                        <option value="main">Main Accounts</option>
                        <option value="farm">Farm Accounts</option>
                        <option value="vacation">Vacation</option>
                    </select>
                </div>
            </div>

            <div class="players-table-container">
                <table class="players-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Governor</th>
                            <th>ID</th>
                            <th>Type</th>
                            <th>Power</th>
                            <th>KP Gained</th>
                            <th>Farm Links</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="players-tbody">
                        ${renderPlayerRows(players)}
                    </tbody>
                </table>
            </div>
        `;

        playerClassification.innerHTML = html;

        // Add event listeners
        document.getElementById('player-search').addEventListener('input', filterPlayers);
        document.getElementById('type-filter').addEventListener('change', filterPlayers);

    } catch (error) {
        playerClassification.innerHTML = `<div class="message error">Failed to load players: ${error.message}</div>`;
    }
}

function renderPlayerRows(players) {
    if (!players || players.length === 0) {
        return '<tr><td colspan="8" style="text-align: center; padding: 20px;">No players found</td></tr>';
    }

    return players.map(player => {
        const accountType = player.account_type || 'main';
        const typeClass = accountType;
        const typeBadge = {
            'main': '👤 Main',
            'farm': '🌾 Farm',
            'vacation': '🏖️ Vacation'
        }[accountType] || '👤 Main';

        const linkedInfo = player.linked_to_main ?
            `<span class="linked-badge">→ Linked to ${player.linked_to_main}</span>` : '';

        const farmCount = (player.farm_accounts || []).length;
        const farmBadge = farmCount > 0 ?
            `<span class="farm-count-badge">${farmCount} ${farmCount === 1 ? 'farm' : 'farms'}</span>` :
            '<span class="no-farms">No farms</span>';

        return `
            <tr class="player-row ${typeClass}" data-governor-id="${player.governor_id}">
                <td>${player.rank || '-'}</td>
                <td>
                    <div class="player-name">${player.governor_name}</div>
                    ${linkedInfo}
                </td>
                <td><code>${player.governor_id}</code></td>
                <td><span class="type-badge ${typeClass}">${typeBadge}</span></td>
                <td>${formatNumber(player.power)}</td>
                <td>${formatNumber(player.kill_points_gained)}</td>
                <td>${farmBadge}</td>
                <td>
                    <button class="classify-btn" onclick="openClassifyModal('${player.governor_id}', '${player.governor_name}')">
                        ⚙️ Classify
                    </button>
                    ${accountType === 'main' ? `
                        <button class="link-farm-btn" onclick="openLinkFarmModal('${player.governor_id}', '${player.governor_name}')">
                            🔗 Link Farm
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function filterPlayers() {
    const searchTerm = document.getElementById('player-search').value.toLowerCase();
    const typeFilter = document.getElementById('type-filter').value;

    const rows = document.querySelectorAll('.player-row');

    rows.forEach(row => {
        const name = row.querySelector('.player-name').textContent.toLowerCase();
        const id = row.querySelector('code').textContent;
        const type = row.classList.contains('farm') ? 'farm' :
                     row.classList.contains('vacation') ? 'vacation' : 'main';

        const matchesSearch = name.includes(searchTerm) || id.includes(searchTerm);
        const matchesType = typeFilter === 'all' || type === typeFilter;

        if (matchesSearch && matchesType) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function openClassifyModal(governorId, governorName) {
    const accountType = prompt(
        `Classify ${governorName} (${governorId})\n\n` +
        `Enter account type:\n` +
        `1 = Main Account\n` +
        `2 = Farm Account\n` +
        `3 = Vacation (excluded from contribution)\n\n` +
        `Enter number (1-3):`
    );

    // User clicked Cancel
    if (accountType === null) return;

    const typeMap = {
        '1': 'main',
        '2': 'farm',
        '3': 'vacation'
    };

    const type = typeMap[accountType.trim()];
    if (!type) {
        alert('Invalid selection. Please enter 1, 2, or 3.');
        return;
    }

    classifyPlayer(governorId, type, false, '');
}

async function classifyPlayer(governorId, accountType, isDeadWeight, notes) {
    try {
        const response = await fetch(`${API_URL}/admin/players/classify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                governor_id: governorId,
                kvk_season_id: activeSeason.season_id,
                account_type: accountType,
                is_dead_weight: isDeadWeight,
                classification_notes: notes
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ Player classified as ${accountType}!`);
            await loadPlayerClassification();
        } else {
            throw new Error(result.error || 'Classification failed');
        }
    } catch (error) {
        alert(`❌ Classification failed: ${error.message}`);
    }
}

function openLinkFarmModal(mainGovernorId, mainGovernorName) {
    const farmId = prompt(
        `Link Farm to ${mainGovernorName}\n\n` +
        `Enter the Governor ID of the farm account to link:`
    );

    if (!farmId) return;

    linkFarmAccount(farmId, mainGovernorId);
}

async function linkFarmAccount(farmGovernorId, mainGovernorId) {
    try {
        const response = await fetch(`${API_URL}/admin/players/link-farm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                farm_governor_id: farmGovernorId,
                main_governor_id: mainGovernorId,
                kvk_season_id: activeSeason.season_id
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`✅ Farm ${farmGovernorId} linked to main ${mainGovernorId}!`);
            await loadPlayerClassification();
        } else {
            throw new Error(result.error || 'Link failed');
        }
    } catch (error) {
        alert(`❌ Link failed: ${error.message}`);
    }
}

// ========================================
// Verified Deaths Upload
// ========================================
async function loadVerificationStatus() {
    if (!activeSeason) return;

    const statusDiv = document.getElementById('verification-status');

    try {
        const response = await fetch(`${API_URL}/admin/verified-deaths/status/${activeSeason}`);
        const data = await response.json();

        if (data.success) {
            const percentage = data.verification_percentage || 0;
            const verified = data.verified_count || 0;
            const total = data.total_players || 0;
            const unverified = data.unverified_count || 0;

            statusDiv.innerHTML = `
                <div class="status-card">
                    <div class="status-header">
                        <h3>📊 Verification Progress</h3>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="progress-text">${percentage.toFixed(1)}% Complete</div>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-label">✅ Verified</span>
                            <span class="stat-value">${verified}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">❌ Unverified</span>
                            <span class="stat-value">${unverified}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">👥 Total Players</span>
                            <span class="stat-value">${total}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load verification status:', error);
        statusDiv.innerHTML = '<div class="error">Failed to load verification status</div>';
    }
}

// Handle verified deaths form submission
const verifiedDeathsForm = document.getElementById('verified-deaths-form');
const verifiedDeathsMessage = document.getElementById('verified-deaths-message');
const verifiedDeathsResults = document.getElementById('verified-deaths-results');
const verifiedDeathsResultsContent = document.getElementById('verified-deaths-results-content');

if (verifiedDeathsForm) {
    verifiedDeathsForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!activeSeason) {
            showMessage(verifiedDeathsMessage, 'error', 'No active season. Please activate a season first.');
            return;
        }

        const fileInput = document.getElementById('verified-deaths-file');
        const file = fileInput.files[0];

        if (!file) {
            showMessage(verifiedDeathsMessage, 'error', 'Please select an Excel file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showMessage(verifiedDeathsMessage, 'info', '⏳ Uploading and processing...');

        try {
            const response = await fetch(`${API_URL}/admin/verified-deaths/upload/${activeSeason}`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                const stats = result.results;
                const status = result.verification_status;

                showMessage(verifiedDeathsMessage, 'success',
                    `✅ ${result.message}`
                );

                // Display results
                verifiedDeathsResults.style.display = 'block';
                verifiedDeathsResultsContent.innerHTML = `
                    <div class="upload-summary">
                        <h4>Upload Summary</h4>
                        <div class="summary-stats">
                            <div class="summary-stat success">
                                <span class="stat-icon">✅</span>
                                <span class="stat-number">${stats.success_count}</span>
                                <span class="stat-label">Updated</span>
                            </div>
                            <div class="summary-stat warning">
                                <span class="stat-icon">⚠️</span>
                                <span class="stat-number">${stats.not_found_count}</span>
                                <span class="stat-label">Not Found</span>
                            </div>
                            <div class="summary-stat error">
                                <span class="stat-icon">❌</span>
                                <span class="stat-number">${stats.error_count}</span>
                                <span class="stat-label">Errors</span>
                            </div>
                        </div>
                    </div>

                    ${stats.players_updated.length > 0 ? `
                        <div class="players-updated">
                            <h4>✅ Successfully Updated (${stats.players_updated.length})</h4>
                            <div class="players-list">
                                ${stats.players_updated.slice(0, 10).map(p => `
                                    <div class="player-item">
                                        <span class="player-name">${p.governor_name}</span>
                                        <span class="player-deaths">T4: ${formatNumber(p.t4_deaths)} | T5: ${formatNumber(p.t5_deaths)}</span>
                                    </div>
                                `).join('')}
                                ${stats.players_updated.length > 10 ? `
                                    <div class="more-players">... and ${stats.players_updated.length - 10} more</div>
                                ` : ''}
                            </div>
                        </div>
                    ` : ''}

                    ${stats.players_not_found.length > 0 ? `
                        <div class="players-not-found">
                            <h4>⚠️ Players Not Found (${stats.players_not_found.length})</h4>
                            <div class="players-list">
                                ${stats.players_not_found.map(p => `
                                    <div class="player-item error">
                                        <span class="player-id">ID: ${p.governor_id}</span>
                                        <span class="row-number">Row ${p.row}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    ${stats.errors.length > 0 ? `
                        <div class="upload-errors">
                            <h4>❌ Errors (${stats.errors.length})</h4>
                            <div class="errors-list">
                                ${stats.errors.map(e => `
                                    <div class="error-item">
                                        <span class="error-row">Row ${e.row}</span>
                                        <span class="error-message">${e.error}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                `;

                // Reload verification status
                await loadVerificationStatus();

                // Clear file input
                fileInput.value = '';
            } else {
                showMessage(verifiedDeathsMessage, 'error', `❌ ${result.error || 'Upload failed'}`);
            }
        } catch (error) {
            console.error('Upload error:', error);
            showMessage(verifiedDeathsMessage, 'error', `❌ Upload failed: ${error.message}`);
        }
    });
}

// ========================================
// Final KvK Data Upload
// ========================================
const finalKvKForm = document.getElementById('final-kvk-form');
const finalKvKMessage = document.getElementById('final-kvk-message');
const finalKvKResults = document.getElementById('final-kvk-results');
const finalKvKResultsContent = document.getElementById('final-kvk-results-content');
const markCompleteSection = document.getElementById('mark-complete-section');
const markCompleteBtn = document.getElementById('mark-complete-btn');
const markCompleteMessage = document.getElementById('mark-complete-message');

if (finalKvKForm) {
    finalKvKForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!activeSeason) {
            showMessage(finalKvKMessage, 'error', 'No active season. Please activate a season first.');
            return;
        }

        const fileInput = document.getElementById('final-kvk-file');
        const file = fileInput.files[0];

        if (!file) {
            showMessage(finalKvKMessage, 'error', 'Please select an Excel file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showMessage(finalKvKMessage, 'info', '⏳ Uploading final KvK data...');
        finalKvKResults.style.display = 'none';
        markCompleteSection.style.display = 'none';

        try {
            const response = await fetch(`${API_URL}/admin/final-kvk/upload/${activeSeason.season_id}`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                const stats = result.results;
                const finalStats = result.final_stats;

                showMessage(finalKvKMessage, 'success',
                    `✅ ${result.message}`
                );

                // Display detailed results
                finalKvKResults.style.display = 'block';
                finalKvKResultsContent.innerHTML = `
                    <div class="upload-summary">
                        <h4>🏆 Final KvK Data Upload Complete</h4>
                        <div class="summary-stats">
                            <div class="summary-stat success">
                                <span class="stat-icon">👥</span>
                                <span class="stat-number">${stats.players_processed}</span>
                                <span class="stat-label">Players Processed</span>
                            </div>
                            <div class="summary-stat">
                                <span class="stat-icon">⚙️</span>
                                <span class="stat-number">${stats.classifications_updated}</span>
                                <span class="stat-label">Classified</span>
                            </div>
                            <div class="summary-stat">
                                <span class="stat-icon">🔗</span>
                                <span class="stat-number">${stats.farms_linked}</span>
                                <span class="stat-label">Farms Linked</span>
                            </div>
                            <div class="summary-stat">
                                <span class="stat-icon">💀</span>
                                <span class="stat-number">${stats.deaths_verified}</span>
                                <span class="stat-label">Deaths Verified</span>
                            </div>
                        </div>
                    </div>

                    <div class="final-stats-summary">
                        <h4>📊 Final Statistics</h4>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">Total Players:</span>
                                <span class="stat-value">${finalStats.total_players}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Main Accounts:</span>
                                <span class="stat-value main">${finalStats.main_accounts}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Farm Accounts:</span>
                                <span class="stat-value farm">${finalStats.farm_accounts}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Vacation:</span>
                                <span class="stat-value vacation">${finalStats.vacation_accounts}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Farms Linked:</span>
                                <span class="stat-value">${finalStats.farms_linked}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Deaths Verified:</span>
                                <span class="stat-value">${finalStats.deaths_verified}</span>
                            </div>
                        </div>
                    </div>

                    ${stats.warnings.length > 0 ? `
                        <div class="upload-warnings">
                            <h4>⚠️ Warnings (${stats.warnings.length})</h4>
                            <div class="warnings-list">
                                ${stats.warnings.map(w => `
                                    <div class="warning-item">
                                        <span class="warning-row">Row ${w.row}</span>
                                        <span class="warning-governor">${w.governor_id || ''}</span>
                                        <span class="warning-message">${w.warning}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    ${stats.errors.length > 0 ? `
                        <div class="upload-errors">
                            <h4>❌ Errors (${stats.errors.length})</h4>
                            <div class="errors-list">
                                ${stats.errors.map(e => `
                                    <div class="error-item">
                                        <span class="error-row">Row ${e.row || 'N/A'}</span>
                                        <span class="error-governor">${e.governor_id || ''}</span>
                                        <span class="error-message">${e.error}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                `;

                // Show mark complete section
                markCompleteSection.style.display = 'block';

                // Reload relevant sections
                await loadPlayerClassification();
                await loadVerificationStatus();

                // Clear file input
                fileInput.value = '';
            } else {
                showMessage(finalKvKMessage, 'error', `❌ ${result.error || result.detail || 'Upload failed'}`);
            }
        } catch (error) {
            console.error('Final KvK upload error:', error);
            showMessage(finalKvKMessage, 'error', `❌ Upload failed: ${error.message}`);
        }
    });
}

if (markCompleteBtn) {
    markCompleteBtn.addEventListener('click', async () => {
        if (!activeSeason) {
            showMessage(markCompleteMessage, 'error', 'No active season');
            return;
        }

        const confirmed = confirm(
            `Mark ${activeSeason.season_name} as completed?\n\n` +
            `This indicates that:\n` +
            `• All final data has been uploaded\n` +
            `• Season is ready to be archived\n` +
            `• No more regular uploads should occur\n\n` +
            `Continue?`
        );

        if (!confirmed) return;

        showMessage(markCompleteMessage, 'info', '⏳ Marking season as completed...');

        try {
            const response = await fetch(`${API_URL}/admin/final-kvk/mark-complete/${activeSeason.season_id}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                showMessage(markCompleteMessage, 'success',
                    `✅ ${result.message}<br>` +
                    `Season is now ready for archiving.`
                );

                // Reload seasons to reflect new status
                await loadSeasons();

                // Hide mark complete section after successful marking
                markCompleteSection.style.display = 'none';
            } else {
                showMessage(markCompleteMessage, 'error', `❌ ${result.error || result.detail || 'Failed to mark complete'}`);
            }
        } catch (error) {
            console.error('Mark complete error:', error);
            showMessage(markCompleteMessage, 'error', `❌ Failed: ${error.message}`);
        }
    });
}

// ========================================
// Initialize
// ========================================
// ========================================
// Fight Period Management
// ========================================

async function loadFightPeriods() {
    const listContainer = document.getElementById('fight-periods-list');
    const seasonInfoContainer = document.getElementById('fight-period-season-info');

    try {
        // Get active season
        const seasonResponse = await fetch(`${API_URL}/api/seasons/active`);
        const seasonData = await seasonResponse.json();

        if (!seasonData.success || !seasonData.season_id) {
            seasonInfoContainer.innerHTML = `
                <div class="message error">No active season found. Create a season first.</div>
            `;
            listContainer.innerHTML = '';
            return;
        }

        const seasonId = seasonData.season_id;
        const seasonName = seasonData.season_name || seasonId;

        // Display season info
        seasonInfoContainer.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>Active Season:</strong> ${seasonName}
                    <span style="color: #6ee7b7; margin-left: 10px;">(${seasonId})</span>
                </div>
                <span style="color: #10b981;">● Active</span>
            </div>
        `;

        // Load fight periods for this season
        const response = await fetch(`${API_URL}/api/fight-periods/${seasonId}`);
        const data = await response.json();

        if (!data.success || data.count === 0) {
            listContainer.innerHTML = `
                <div class="message info">
                    <strong>No fight periods defined yet.</strong><br>
                    Create fight periods to track real combat KP vs trading KP.
                </div>
            `;
            return;
        }

        // Display fight periods
        let html = '<div class="fight-periods-grid">';

        for (const fight of data.fight_periods) {
            const startTime = new Date(fight.start_time).toLocaleString();
            const endTime = fight.end_time ? new Date(fight.end_time).toLocaleString() : 'Ongoing';
            const statusColor = fight.status === 'completed' ? '#10b981' : fight.status === 'active' ? '#f59e0b' : '#6b7280';
            const statusIcon = fight.status === 'completed' ? '✅' : fight.status === 'active' ? '⚔️' : '📅';

            html += `
                <div class="fight-period-card" style="border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 15px; background: rgba(16, 185, 129, 0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <div>
                            <h4 style="margin: 0 0 5px 0; color: #10b981;">
                                ${statusIcon} Fight ${fight.fight_number}: ${fight.fight_name}
                            </h4>
                            <span style="color: ${statusColor}; font-size: 0.9em;">
                                ${fight.status.toUpperCase()}
                            </span>
                        </div>
                        <div style="display: flex; gap: 5px;">
                            <button class="icon-btn edit-fight-btn" data-season="${seasonId}" data-fight="${fight.fight_number}" title="Edit">
                                ✏️
                            </button>
                            <button class="icon-btn delete-fight-btn" data-season="${seasonId}" data-fight="${fight.fight_number}" title="Delete">
                                🗑️
                            </button>
                        </div>
                    </div>
                    <div style="font-size: 0.9em; color: #94a3b8;">
                        <div><strong>Start:</strong> ${startTime}</div>
                        <div><strong>End:</strong> ${endTime}</div>
                        ${fight.description ? `<div style="margin-top: 8px; font-style: italic;">${fight.description}</div>` : ''}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        listContainer.innerHTML = html;

        // Setup delete/edit buttons
        setupFightPeriodButtons();

    } catch (error) {
        console.error('Failed to load fight periods:', error);
        listContainer.innerHTML = '<div class="message error">Failed to load fight periods</div>';
    }
}

function setupFightPeriodButtons() {
    // Delete buttons
    document.querySelectorAll('.delete-fight-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const seasonId = btn.dataset.season;
            const fightNumber = btn.dataset.fight;

            if (!confirm(`Are you sure you want to delete Fight ${fightNumber}? This will affect KP calculations!`)) {
                return;
            }

            try {
                const token = localStorage.getItem('admin_token');
                const response = await fetch(`${API_URL}/admin/fight-periods/${seasonId}/${fightNumber}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('delete-fight-message', 'Fight period deleted successfully!', 'success');
                    loadFightPeriods(); // Reload
                } else {
                    showMessage('delete-fight-message', `Error: ${data.error}`, 'error');
                }
            } catch (error) {
                showMessage('delete-fight-message', 'Failed to delete fight period', 'error');
            }
        });
    });

    // Edit buttons
    document.querySelectorAll('.edit-fight-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const seasonId = btn.dataset.season;
            const fightNumber = btn.dataset.fight;

            // Fetch current fight period data
            try {
                const response = await fetch(`${API_URL}/api/fight-periods/${seasonId}/${fightNumber}`);
                const data = await response.json();

                if (!data.success) {
                    alert('Failed to load fight period data');
                    return;
                }

                const fight = data.fight_period;

                // Show edit modal
                showEditFightModal(seasonId, fightNumber, fight);
            } catch (error) {
                alert('Failed to load fight period data');
            }
        });
    });
}

function showEditFightModal(seasonId, fightNumber, fight) {
    // Create modal HTML
    const modalHtml = `
        <div id="edit-fight-modal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 9999;">
            <div style="background: #1e293b; border-radius: 12px; padding: 30px; max-width: 500px; width: 90%; max-height: 90vh; overflow-y: auto;">
                <h3 style="margin: 0 0 20px 0; color: #10b981;">✏️ Edit Fight Period ${fightNumber}</h3>

                <form id="edit-fight-form">
                    <div class="form-group">
                        <label for="edit-fight-name">Fight Name *</label>
                        <input type="text" id="edit-fight-name" value="${fight.fight_name}" required>
                    </div>

                    <div class="form-group">
                        <label for="edit-fight-start-time">Start Time *</label>
                        <input type="datetime-local" id="edit-fight-start-time" value="${formatDateTimeLocal(fight.start_time)}" required>
                    </div>

                    <div class="form-group">
                        <label for="edit-fight-end-time">End Time</label>
                        <input type="datetime-local" id="edit-fight-end-time" value="${fight.end_time ? formatDateTimeLocal(fight.end_time) : ''}">
                        <small style="color: #6ee7b7; margin-top: 5px; display: block;">
                            Leave empty for ongoing fights
                        </small>
                    </div>

                    <div class="form-group">
                        <label for="edit-fight-description">Description</label>
                        <textarea id="edit-fight-description" rows="2">${fight.description || ''}</textarea>
                    </div>

                    <div id="edit-fight-message"></div>

                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button type="submit" class="upload-btn" style="background: #10b981;">
                            💾 Save Changes
                        </button>
                        <button type="button" id="cancel-edit-btn" class="back-link" style="padding: 10px 20px;">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Setup form handlers
    const modal = document.getElementById('edit-fight-modal');
    const form = document.getElementById('edit-fight-form');
    const cancelBtn = document.getElementById('cancel-edit-btn');

    // Close modal
    const closeModal = () => {
        modal.remove();
    };

    cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fightName = document.getElementById('edit-fight-name').value;
        const startTime = document.getElementById('edit-fight-start-time').value;
        const endTime = document.getElementById('edit-fight-end-time').value;
        const description = document.getElementById('edit-fight-description').value;

        // Convert datetime-local format to ISO format (add seconds if missing)
        const formatToISO = (datetimeLocal) => {
            if (!datetimeLocal) return null;
            // If it doesn't have seconds, add :00
            const withSeconds = datetimeLocal.includes(':00:00') ? datetimeLocal : datetimeLocal + ':00';
            return new Date(withSeconds).toISOString();
        };

        const requestBody = {
            fight_name: fightName,
            start_time: formatToISO(startTime),
            description: description || null
        };

        // Only include end_time if provided
        if (endTime) {
            requestBody.end_time = formatToISO(endTime);
        }

        try {
            const token = localStorage.getItem('admin_token');
            const response = await fetch(`${API_URL}/admin/fight-periods/${seasonId}/${fightNumber}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (data.success) {
                showMessage('edit-fight-message', 'Fight period updated successfully! ✅', 'success');
                setTimeout(() => {
                    closeModal();
                    loadFightPeriods(); // Reload list
                }, 1000);
            } else {
                showMessage('edit-fight-message', `Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Failed to update fight period:', error);
            showMessage('edit-fight-message', 'Failed to update fight period', 'error');
        }
    });
}

function formatDateTimeLocal(isoString) {
    // Convert ISO string to datetime-local format (YYYY-MM-DDTHH:MM)
    if (!isoString) return '';
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function setupCreateFightForm() {
    const toggleBtn = document.getElementById('toggle-create-fight-btn');
    const formContainer = document.getElementById('create-fight-form-container');
    const cancelBtn = document.getElementById('cancel-fight-btn');
    const form = document.getElementById('create-fight-form');

    // Toggle form visibility
    toggleBtn.addEventListener('click', () => {
        const isHidden = formContainer.style.display === 'none';
        formContainer.style.display = isHidden ? 'block' : 'none';
        toggleBtn.textContent = isHidden ? '❌ Cancel' : '➕ Create New Fight Period';

        if (isHidden) {
            // Scroll to form
            formContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });

    cancelBtn.addEventListener('click', () => {
        formContainer.style.display = 'none';
        toggleBtn.textContent = '➕ Create New Fight Period';
        form.reset();
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fightNumber = parseInt(document.getElementById('fight-number').value);
        const fightName = document.getElementById('fight-name').value;
        const startTime = document.getElementById('fight-start-time').value;
        const endTime = document.getElementById('fight-end-time').value;
        const description = document.getElementById('fight-description').value;

        // Get active season
        const seasonResponse = await fetch(`${API_URL}/api/seasons/active`);
        const seasonData = await seasonResponse.json();

        if (!seasonData.success) {
            showMessage('create-fight-message', 'No active season found', 'error');
            return;
        }

        // Convert datetime-local format to ISO format (add seconds if missing)
        const formatToISO = (datetimeLocal) => {
            if (!datetimeLocal) return null;
            // If it doesn't have seconds, add :00
            const withSeconds = datetimeLocal.includes(':00:00') ? datetimeLocal : datetimeLocal + ':00';
            return new Date(withSeconds).toISOString();
        };

        const requestBody = {
            season_id: seasonData.season_id,
            fight_number: fightNumber,
            fight_name: fightName,
            start_time: formatToISO(startTime),
            description: description || null
        };

        // Only include end_time if provided
        if (endTime) {
            requestBody.end_time = formatToISO(endTime);
        }

        try {
            const token = localStorage.getItem('admin_token');
            const response = await fetch(`${API_URL}/admin/fight-periods`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (data.success) {
                showMessage('create-fight-message', 'Fight period created successfully! ⚔️', 'success');
                form.reset();
                formContainer.style.display = 'none';
                toggleBtn.textContent = '➕ Create New Fight Period';
                loadFightPeriods(); // Reload list
            } else {
                showMessage('create-fight-message', `Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Failed to create fight period:', error);
            showMessage('create-fight-message', 'Failed to create fight period', 'error');
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    // Display username
    const adminUsername = localStorage.getItem('admin_username');
    const usernameDisplay = document.getElementById('admin-username-display');
    if (usernameDisplay && adminUsername) {
        usernameDisplay.textContent = `👤 ${adminUsername}`;
    }

    // Setup logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_username');
            window.location.href = 'admin-login.html';
        });
    }

    // Load seasons first (this will also load player classification)
    await loadSeasons();

    // Load other sections
    loadDataStatus();
    loadHistory();
    loadFileManagement();
    loadVerificationStatus();

    // Load fight periods
    loadFightPeriods();
    setupCreateFightForm();
});