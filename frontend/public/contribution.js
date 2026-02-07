// ========================================
// Configuration
// ========================================
// API_URL and utility functions (formatNumber, showLoading, showError) are now in utilities.js

// ========================================
// Global State
// ========================================
let activeSeason = null;
let allContributions = [];
let filteredContributions = [];

// ========================================
// Load Active Season
// ========================================
async function loadActiveSeason() {
    try {
        const response = await fetch(`${API_URL}/api/seasons/active`);
        const data = await response.json();

        if (data.success && (data.season || data.season_id)) {
            // Handle both response formats
            activeSeason = data.season || data;
            displaySeasonInfo();
            return true;
        } else {
            showError('season-info', t('leaderboard.noActiveSeason'));
            return false;
        }
    } catch (error) {
        console.error('Failed to load active season:', error);
        showError('season-info', t('leaderboard.failedLoadSeason'));
        return false;
    }
}

function displaySeasonInfo() {
    const seasonInfo = document.getElementById('season-info');
    seasonInfo.innerHTML = `
        <div class="season-banner">
            <div class="season-details">
                <h3>${activeSeason.season_name}</h3>
                <p><strong>${t('leaderboard.seasonId')}</strong> ${activeSeason.season_id}</p>
                <p><strong>${t('leaderboard.statusLabel')}</strong> <span class="status-badge ${activeSeason.status}">${activeSeason.status}</span></p>
            </div>
            ${activeSeason.start_date ? `
                <div class="season-dates">
                    <p><strong>${t('leaderboard.started')}</strong> ${new Date(activeSeason.start_date).toLocaleDateString()}</p>
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
                    <h3>${t('leaderboard.verificationProgress')}</h3>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="progress-text">${t('leaderboard.percentVerified', { pct: percentage.toFixed(1) })}</div>
                    </div>
                    <div class="verification-stats">
                        <div class="stat-item verified">
                            <span class="stat-icon">✅</span>
                            <span class="stat-value">${verified}</span>
                            <span class="stat-label">${t('common.verified')}</span>
                        </div>
                        <div class="stat-item unverified">
                            <span class="stat-icon">⏳</span>
                            <span class="stat-value">${unverified}</span>
                            <span class="stat-label">${t('common.unverified')}</span>
                        </div>
                        <div class="stat-item total">
                            <span class="stat-icon">👥</span>
                            <span class="stat-value">${total}</span>
                            <span class="stat-label">${t('common.total')}</span>
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

    showLoading('leaderboard-container', t('leaderboard.loadingContrib'));

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

    statsDiv.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-content">
                    <div class="stat-value">${filteredContributions.length}</div>
                    <div class="stat-label">${t('leaderboard.playersShown')}</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚔️</div>
                <div class="stat-content">
                    <div class="stat-value">${formatNumber(totalKillScore)}</div>
                    <div class="stat-label">${t('leaderboard.totalKillScore')}</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💀</div>
                <div class="stat-content">
                    <div class="stat-value">${formatNumber(totalDeathScore)}</div>
                    <div class="stat-label">${t('leaderboard.totalDeathScore')}</div>
                </div>
            </div>
            <div class="stat-card primary">
                <div class="stat-icon">🏆</div>
                <div class="stat-content">
                    <div class="stat-value">${formatNumber(totalContribution)}</div>
                    <div class="stat-label">${t('leaderboard.totalDKP')}</div>
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
                <h3>${t('leaderboard.noPlayersFound')}</h3>
                <p>${t('leaderboard.tryAdjusting')}</p>
            </div>
        `;
        return;
    }

    const tableHTML = `
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th class="rank-col">${t('common.rank')}</th>
                    <th class="player-col">${t('common.player')}</th>
                    <th class="score-col">${t('leaderboard.t4KillsGained')}</th>
                    <th class="score-col">${t('leaderboard.t5KillsGained')}</th>
                    <th class="score-col">${t('leaderboard.t4Deaths')}</th>
                    <th class="score-col">${t('leaderboard.t5Deaths')}</th>
                    <th class="total-col">${t('leaderboard.totalDKP')}</th>
                    <th class="status-col">${t('common.status')}</th>
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
                                    <a href="player-details.html?id=${contribution.governor_id}" class="player-name-link">
                                        ${contribution.governor_name}
                                    </a>
                                    <span class="player-id">${contribution.governor_id}</span>
                                </div>
                            </td>
                            <td class="score-col">
                                <div class="score-breakdown">
                                    <span class="score-value">${formatNumber(contribution.t4_kills_gained || 0)}</span>
                                </div>
                            </td>
                            <td class="score-col">
                                <div class="score-breakdown">
                                    <span class="score-value">${formatNumber(contribution.t5_kills_gained || 0)}</span>
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
                                    ? `<span class="status-badge verified">${t('leaderboard.verifiedBadge')}</span>`
                                    : `<span class="status-badge unverified">${t('leaderboard.unverifiedBadge')}</span>`
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

        return matchesSearch && matchesVerification;
    });

    displayLeaderboard();
    displayLeaderboardStats();
}

// ========================================
// Language change handler
// ========================================
window.addEventListener('languageChanged', () => {
    if (activeSeason) displaySeasonInfo();
    if (activeSeason) loadVerificationStatus();
    if (filteredContributions.length > 0) {
        displayLeaderboard();
        displayLeaderboardStats();
    }
});

// ========================================
// Event Listeners
// ========================================
document.addEventListener('DOMContentLoaded', async () => {
    await I18n.init();

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
    document.getElementById('verification-filter').addEventListener('change', applyFilters);
    document.getElementById('player-search').addEventListener('input', applyFilters);

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', async () => {
        await loadVerificationStatus();
        await loadContributions();
    });
});
