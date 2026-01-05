// ========================================
// Configuration
// ========================================
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://kd3584-production.up.railway.app';

// ========================================
// Global State
// ========================================
let activeSeason = null;
let allContributions = [];
let filteredContributions = [];

// ========================================
// Utility Functions
// ========================================
function formatNumber(num) {
    if (!num) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="loading">${message}</div>`;
    }
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="error-message">❌ ${message}</div>`;
    }
}

// ========================================
// Load Active Season
// ========================================
async function loadActiveSeason() {
    try {
        const response = await fetch(`${API_URL}/admin/seasons/active`);
        const data = await response.json();

        if (data.success && data.season) {
            activeSeason = data.season;
            displaySeasonInfo();
            return true;
        } else {
            showError('season-info', 'No active season found');
            return false;
        }
    } catch (error) {
        console.error('Failed to load active season:', error);
        showError('season-info', 'Failed to load season information');
        return false;
    }
}

function displaySeasonInfo() {
    const seasonInfo = document.getElementById('season-info');
    seasonInfo.innerHTML = `
        <div class="season-banner">
            <div class="season-details">
                <h3>${activeSeason.season_name}</h3>
                <p><strong>Season ID:</strong> ${activeSeason.season_id}</p>
                <p><strong>Status:</strong> <span class="status-badge ${activeSeason.status}">${activeSeason.status}</span></p>
            </div>
            ${activeSeason.start_date ? `
                <div class="season-dates">
                    <p><strong>Started:</strong> ${new Date(activeSeason.start_date).toLocaleDateString()}</p>
                </div>
            ` : ''}
        </div>
    `;
}

// ========================================
// Load Verification Status
// ========================================
async function loadVerificationStatus() {
    if (!activeSeason) return;

    try {
        const response = await fetch(`${API_URL}/admin/verified-deaths/status/${activeSeason.season_id}`);
        const data = await response.json();

        if (data.success) {
            const percentage = data.verification_percentage || 0;
            const verified = data.verified_count || 0;
            const total = data.total_players || 0;
            const unverified = data.unverified_count || 0;

            const statusDiv = document.getElementById('verification-status');
            statusDiv.innerHTML = `
                <div class="verification-card">
                    <h3>📊 Death Verification Progress</h3>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="progress-text">${percentage.toFixed(1)}% Verified</div>
                    </div>
                    <div class="verification-stats">
                        <div class="stat-item verified">
                            <span class="stat-icon">✅</span>
                            <span class="stat-value">${verified}</span>
                            <span class="stat-label">Verified</span>
                        </div>
                        <div class="stat-item unverified">
                            <span class="stat-icon">⏳</span>
                            <span class="stat-value">${unverified}</span>
                            <span class="stat-label">Unverified</span>
                        </div>
                        <div class="stat-item total">
                            <span class="stat-icon">👥</span>
                            <span class="stat-value">${total}</span>
                            <span class="stat-label">Total</span>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load verification status:', error);
    }
}

// ========================================
// Load Contribution Leaderboard
// ========================================
async function loadContributions() {
    if (!activeSeason) return;

    showLoading('leaderboard-container', 'Loading contribution data...');

    try {
        const response = await fetch(
            `${API_URL}/admin/verified-deaths/contribution-scores/${activeSeason.season_id}?use_verified_deaths=true&limit=500`
        );
        const data = await response.json();

        if (data.success) {
            allContributions = data.contributions;
            filteredContributions = [...allContributions];
            displayLeaderboard();
            displayLeaderboardStats();
        } else {
            showError('leaderboard-container', data.error || 'Failed to load contributions');
        }
    } catch (error) {
        console.error('Failed to load contributions:', error);
        showError('leaderboard-container', error.message);
    }
}

// ========================================
// Display Leaderboard Stats
// ========================================
function displayLeaderboardStats() {
    const statsDiv = document.getElementById('leaderboard-stats');

    const totalKillScore = filteredContributions.reduce((sum, c) => sum + c.total_kill_score, 0);
    const totalDeathScore = filteredContributions.reduce((sum, c) => sum + c.total_death_score, 0);
    const totalContribution = filteredContributions.reduce((sum, c) => sum + c.total_contribution_score, 0);
    const verifiedCount = filteredContributions.filter(c => c.has_verified_deaths).length;

    statsDiv.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-content">
                    <div class="stat-value">${filteredContributions.length}</div>
                    <div class="stat-label">Players Shown</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚔️</div>
                <div class="stat-content">
                    <div class="stat-value">${formatNumber(totalKillScore)}</div>
                    <div class="stat-label">Total Kill Score</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💀</div>
                <div class="stat-content">
                    <div class="stat-value">${formatNumber(totalDeathScore)}</div>
                    <div class="stat-label">Total Death Score</div>
                </div>
            </div>
            <div class="stat-card primary">
                <div class="stat-icon">🏆</div>
                <div class="stat-content">
                    <div class="stat-value">${formatNumber(totalContribution)}</div>
                    <div class="stat-label">Total DKP</div>
                </div>
            </div>
        </div>
    `;
}

// ========================================
// Display Leaderboard Table
// ========================================
function displayLeaderboard() {
    const container = document.getElementById('leaderboard-container');

    if (filteredContributions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🏆</div>
                <h3>No players found</h3>
                <p>Try adjusting your filters or refresh the page.</p>
            </div>
        `;
        return;
    }

    const tableHTML = `
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th class="rank-col">Rank</th>
                    <th class="player-col">Player</th>
                    <th class="score-col">T4 Kills</th>
                    <th class="score-col">T5 Kills</th>
                    <th class="score-col">T4 Deaths</th>
                    <th class="score-col">T5 Deaths</th>
                    <th class="total-col">Total DKP</th>
                    <th class="status-col">Status</th>
                </tr>
            </thead>
            <tbody>
                ${filteredContributions.map((contribution, index) => {
                    const rank = index + 1;
                    const medalClass = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : '';
                    const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';

                    return `
                        <tr class="player-row ${medalClass}" data-rank="${rank}">
                            <td class="rank-col">
                                <div class="rank-display ${medalClass}">
                                    ${medal ? `<span class="medal">${medal}</span>` : `<span class="rank-number">#${rank}</span>`}
                                </div>
                            </td>
                            <td class="player-col">
                                <div class="player-info">
                                    <a href="player.html?id=${contribution.governor_id}" class="player-name-link">
                                        ${contribution.governor_name}
                                    </a>
                                    <span class="player-id">${contribution.governor_id}</span>
                                </div>
                            </td>
                            <td class="score-col">
                                <div class="score-breakdown">
                                    <span class="score-value">${formatNumber(contribution.t4_kill_score)}</span>
                                </div>
                            </td>
                            <td class="score-col">
                                <div class="score-breakdown">
                                    <span class="score-value">${formatNumber(contribution.t5_kill_score)}</span>
                                </div>
                            </td>
                            <td class="score-col">
                                <div class="score-breakdown">
                                    <span class="score-value ${contribution.has_verified_deaths ? '' : 'unverified'}">${formatNumber(contribution.t4_death_score)}</span>
                                </div>
                            </td>
                            <td class="score-col">
                                <div class="score-breakdown">
                                    <span class="score-value ${contribution.has_verified_deaths ? '' : 'unverified'}">${formatNumber(contribution.t5_death_score)}</span>
                                </div>
                            </td>
                            <td class="total-col">
                                <div class="total-score">
                                    <span class="total-value">${formatNumber(contribution.total_contribution_score)}</span>
                                </div>
                            </td>
                            <td class="status-col">
                                ${contribution.has_verified_deaths
                                    ? '<span class="status-badge verified">✅ Verified</span>'
                                    : '<span class="status-badge unverified">⏳ Unverified</span>'
                                }
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
}

// ========================================
// Filter Functions
// ========================================
function applyFilters() {
    const accountTypeFilter = document.getElementById('account-type-filter').value;
    const verificationFilter = document.getElementById('verification-filter').value;
    const searchTerm = document.getElementById('player-search').value.toLowerCase();

    filteredContributions = allContributions.filter(contribution => {
        // Search filter
        const matchesSearch = searchTerm === '' ||
            contribution.governor_name.toLowerCase().includes(searchTerm) ||
            contribution.governor_id.includes(searchTerm);

        // Verification filter
        const matchesVerification =
            verificationFilter === 'all' ||
            (verificationFilter === 'verified' && contribution.has_verified_deaths) ||
            (verificationFilter === 'unverified' && !contribution.has_verified_deaths);

        // Account type filter (for now, show all since we don't have account_type in contribution data)
        // This can be enhanced if account_type is added to the contribution endpoint
        const matchesAccountType = accountTypeFilter === 'all' || accountTypeFilter === 'main';

        return matchesSearch && matchesVerification && matchesAccountType;
    });

    displayLeaderboard();
    displayLeaderboardStats();
}

// ========================================
// Event Listeners
// ========================================
document.addEventListener('DOMContentLoaded', async () => {
    // Load active season first
    const loaded = await loadActiveSeason();

    if (loaded) {
        // Load all data
        await Promise.all([
            loadVerificationStatus(),
            loadContributions()
        ]);
    }

    // Setup filters
    document.getElementById('account-type-filter').addEventListener('change', applyFilters);
    document.getElementById('verification-filter').addEventListener('change', applyFilters);
    document.getElementById('player-search').addEventListener('input', applyFilters);

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', async () => {
        await loadVerificationStatus();
        await loadContributions();
    });
});
