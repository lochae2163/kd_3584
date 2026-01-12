// ========================================
// Configuration
// ========================================
// API_URL, formatFullNumber, formatShortNumber, formatDeltaNumber, formatDate are now in utilities.js
let KVK_SEASON_ID = null; // Will be fetched from active season
const PLAYERS_PER_PAGE = 50;

// ========================================
// State
// ========================================
let allPlayers = [];
let currentPage = 1;
let filteredPlayers = [];
let currentSortBy = 'kill_points_gained';

// ========================================
// DOM Elements
// ========================================
const snapshotInfo = document.getElementById('snapshot-info');
const statsGrid = document.getElementById('stats-grid');
const topPlayers = document.getElementById('top-players');
const leaderboardBody = document.getElementById('leaderboard-body');
const playerCount = document.getElementById('player-count');
const searchInput = document.getElementById('search');
const sortSelect = document.getElementById('sort-by');

// ========================================
// Column Definitions
// ========================================
const COLUMNS = {
    'kill_points_gained': { label: 'Kill Points Gained', isGained: true, field: 'kill_points' },
    'fight_kp_gained': { label: 'Fight KP (Real Combat)', isGained: true, field: 'fight_kp_gained', isFightKP: true },
    'deads_gained': { label: 'Deaths Gained', isGained: true, field: 'deads' },
    'power': { label: 'Power', isGained: false, field: 'power' },
    'kill_points': { label: 'Kill Points', isGained: false, field: 'kill_points' },
    't5_kills': { label: 'T5 Kills', isGained: false, field: 't5_kills' },
    't4_kills': { label: 'T4 Kills', isGained: false, field: 't4_kills' },
    'deads': { label: 'Deaths', isGained: false, field: 'deads' }
};

/**
 * Get ordered columns based on current sort
 */
function getOrderedColumns(sortBy) {
    const allColumnKeys = Object.keys(COLUMNS);
    // Put sorted column first, then others in default order
    return [sortBy, ...allColumnKeys.filter(key => key !== sortBy)];
}

// ========================================
// Utility Functions
// ========================================
// Number formatting functions (formatFullNumber, formatShortNumber, formatDeltaNumber) moved to utilities.js

/**
 * Create stat cell HTML with delta badge above
 */
function createStatCell(value, delta) {
    const formattedValue = formatFullNumber(value);
    
    // If no delta or delta is 0, just show the value
    if (!delta || delta === 0) {
        return `
            <div class="stat-cell">
                <span class="stat-value">${formattedValue}</span>
            </div>
        `;
    }
    
    // Determine delta type
    const isPositive = delta > 0;
    const deltaClass = isPositive ? 'positive' : 'negative';
    const arrowClass = isPositive ? 'arrow-up' : 'arrow-down';
    const prefix = isPositive ? '+' : '-';
    const formattedDelta = formatDeltaNumber(delta);
    
    return `
        <div class="stat-cell">
            <span class="delta-badge ${deltaClass}">
                <span class="${arrowClass}"></span>
                ${prefix}${formattedDelta}
            </span>
            <span class="stat-value">${formattedValue}</span>
        </div>
    `;
}

/**
 * Format date for display in UTC
 * (Now defined in utilities.js)
 */

// ========================================
// Load Stats Summary
// ========================================
async function loadStats() {
    statsGrid.innerHTML = '<div class="loading">Loading stats...</div>';
    
    try {
        const response = await fetch(`${API_URL}/api/stats/summary?kvk_season_id=${KVK_SEASON_ID}`);
        
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const data = await response.json();
        const summary = data.summary || {};
        const totals = summary.totals || {};
        const tops = summary.top_players || {};
        
        statsGrid.innerHTML = `
            <div class="stat-card">
                <div class="label">👥 Total Players</div>
                <div class="value">${data.player_count || 0}</div>
            </div>
            <div class="stat-card">
                <div class="label">⚔️ Total Kill Points</div>
                <div class="value">${formatShortNumber(totals.kill_points)}</div>
            </div>
            <div class="stat-card">
                <div class="label">💪 Total Power</div>
                <div class="value">${formatShortNumber(totals.power)}</div>
            </div>
            <div class="stat-card">
                <div class="label">🎯 Total T5 Kills</div>
                <div class="value">${formatShortNumber(totals.t5_kills)}</div>
            </div>
        `;
        
        if (Object.keys(tops).length > 0) {
            topPlayers.innerHTML = `
                <div class="top-card">
                    <div class="title">🏆 Kill Points Gained</div>
                    <div class="name">${tops.kill_points?.name || 'N/A'}</div>
                    <div class="stat">${formatShortNumber(tops.kill_points?.value)}</div>
                </div>
                <div class="top-card purple">
                    <div class="title">⚔️ T5 Kills Gained</div>
                    <div class="name">${tops.t5_kills?.name || 'N/A'}</div>
                    <div class="stat">${formatShortNumber(tops.t5_kills?.value)}</div>
                </div>
                <div class="top-card green">
                    <div class="title">🎖️ T4 Kills Gained</div>
                    <div class="name">${tops.t4_kills?.name || 'N/A'}</div>
                    <div class="stat">${formatShortNumber(tops.t4_kills?.value)}</div>
                </div>
                <div class="top-card red">
                    <div class="title">💀 Deaths Gained</div>
                    <div class="name">${tops.deads?.name || 'N/A'}</div>
                    <div class="stat">${formatShortNumber(tops.deads?.value)}</div>
                </div>
            `;
        }
        
        // Update snapshot info
        snapshotInfo.innerHTML = `
            <p><strong>Baseline:</strong> ${formatDate(data.baseline_date)}</p>
            <p><strong>Last Updated:</strong> ${formatDate(data.current_date)}</p>
        `;
        
    } catch (error) {
        console.error('Failed to load stats:', error);
        statsGrid.innerHTML = '<div class="loading">⚠️ No data available. Admin needs to upload baseline first.</div>';
    }
}

// ========================================
// Load Leaderboard
// ========================================
async function loadLeaderboard(sortBy = 'kill_points_gained') {
    currentSortBy = sortBy;
    leaderboardBody.innerHTML = '<tr><td colspan="9" class="loading">Loading leaderboard...</td></tr>';

    try {
        const response = await fetch(
            `${API_URL}/api/leaderboard?kvk_season_id=${KVK_SEASON_ID}&sort_by=${sortBy}&limit=500`
        );

        if (!response.ok) throw new Error('Failed to fetch leaderboard');

        const data = await response.json();
        allPlayers = data.leaderboard || [];

        playerCount.textContent = `${allPlayers.length} players`;
        renderLeaderboard(allPlayers);
        updateTableHeaders(sortBy);

    } catch (error) {
        console.error('Failed to load leaderboard:', error);
        leaderboardBody.innerHTML = '<tr><td colspan="9" class="loading">⚠️ No data available</td></tr>';
    }
}

/**
 * Update table headers based on current sort
 */
function updateTableHeaders(sortBy) {
    const table = document.querySelector('.table-wrapper table thead tr');
    const orderedColumns = getOrderedColumns(sortBy);

    // Build header HTML
    const headersHTML = `
        <th>Rank</th>
        <th>Governor</th>
        ${orderedColumns.map(colKey => {
            const col = COLUMNS[colKey];
            const isSorted = colKey === sortBy;
            const sortIndicator = isSorted ? ' 🔽' : '';
            return `<th class="text-right ${isSorted ? 'sorted-column' : ''}">${col.label}${sortIndicator}</th>`;
        }).join('')}
    `;

    table.innerHTML = headersHTML;
}

/**
 * Render cell value based on column type
 */
function renderCellValue(colKey, player) {
    const col = COLUMNS[colKey];
    const stats = player.stats || {};
    const delta = player.delta || {};

    // Handle fight KP separately (stored directly on player object)
    if (col.isFightKP) {
        const fightKP = player.fight_kp_gained || 0;
        return `
            <div class="stat-cell">
                <span class="stat-value gained-stat" style="color: #10b981;">${formatFullNumber(fightKP)}</span>
            </div>
        `;
    }

    if (col.isGained) {
        // For "gained" columns, show only the delta value in green
        const deltaValue = delta[col.field] || 0;
        return `
            <div class="stat-cell">
                <span class="stat-value gained-stat">${formatFullNumber(deltaValue)}</span>
            </div>
        `;
    } else {
        // For regular columns, show stat value with delta badge above
        const statValue = stats[col.field] || 0;
        const deltaValue = delta[col.field] || 0;
        return createStatCell(statValue, deltaValue);
    }
}

/**
 * Render leaderboard table with pagination
 */
function renderLeaderboard(players) {
    filteredPlayers = players;

    if (players.length === 0) {
        leaderboardBody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <div class="icon">📊</div>
                    <p>No data available</p>
                </td>
            </tr>
        `;
        document.getElementById('pagination').style.display = 'none';
        return;
    }

    // Calculate pagination
    const totalPages = Math.ceil(players.length / PLAYERS_PER_PAGE);
    const startIndex = (currentPage - 1) * PLAYERS_PER_PAGE;
    const endIndex = startIndex + PLAYERS_PER_PAGE;
    const playersToShow = players.slice(startIndex, endIndex);

    // Show pagination if more than one page
    if (totalPages > 1) {
        document.getElementById('pagination').style.display = 'flex';
        updatePaginationControls(totalPages);
    } else {
        document.getElementById('pagination').style.display = 'none';
    }

    // Get column order based on current sort
    const orderedColumns = getOrderedColumns(currentSortBy);

    leaderboardBody.innerHTML = playersToShow.map(player => {
        // Rank display
        let rankDisplay = '';
        let rowClass = '';

        switch (player.rank) {
            case 1:
                rankDisplay = '<span class="rank-badge">🥇</span>';
                rowClass = 'rank-1';
                break;
            case 2:
                rankDisplay = '<span class="rank-badge">🥈</span>';
                rowClass = 'rank-2';
                break;
            case 3:
                rankDisplay = '<span class="rank-badge">🥉</span>';
                rowClass = 'rank-3';
                break;
            default:
                rankDisplay = `<span class="rank-number">#${player.rank}</span>`;
        }

        // Build dynamic columns
        const columnCells = orderedColumns.map(colKey => {
            const cellValue = renderCellValue(colKey, player);
            return `<td class="stat-col text-right"><div class="stat-value">${cellValue}</div></td>`;
        }).join('');

        return `
            <tr class="player-row ${rowClass}" onclick="window.location.href='player-details.html?id=${player.governor_id}'">
                <td class="rank-col">
                    <div class="rank-display ${rowClass}">
                        ${rankDisplay}
                    </div>
                </td>
                <td class="player-col">
                    <div class="player-info">
                        <div class="player-name">${player.governor_name}</div>
                        <div class="player-id">ID: ${player.governor_id}</div>
                    </div>
                </td>
                ${columnCells}
            </tr>
        `;
    }).join('');

    // Check if table needs scroll hint
    setTimeout(checkTableScroll, 100);
}

/**
 * Update pagination controls
 */
function updatePaginationControls(totalPages) {
    const pageInfo = document.getElementById('page-info');
    const firstBtn = document.getElementById('first-page');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const lastBtn = document.getElementById('last-page');

    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;

    // Disable/enable buttons
    firstBtn.disabled = currentPage === 1;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
    lastBtn.disabled = currentPage === totalPages;
}

/**
 * Go to specific page
 */
function goToPage(page) {
    const totalPages = Math.ceil(filteredPlayers.length / PLAYERS_PER_PAGE);

    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;

    currentPage = page;
    renderLeaderboard(filteredPlayers);

    // Scroll to top of leaderboard
    document.querySelector('.leaderboard').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Filter players by search term
 */
function filterPlayers(searchTerm) {
    const filtered = allPlayers.filter(player =>
        player.governor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        player.governor_id.includes(searchTerm)
    );
    currentPage = 1; // Reset to first page when searching
    renderLeaderboard(filtered);
}

// ========================================
// Event Listeners
// ========================================
searchInput.addEventListener('input', (e) => filterPlayers(e.target.value));
sortSelect.addEventListener('change', (e) => {
    currentPage = 1; // Reset to first page when sorting
    loadLeaderboard(e.target.value);
});

/**
 * Check if table needs horizontal scroll and show hint
 */
function checkTableScroll() {
    const tableWrapper = document.getElementById('table-wrapper');
    const scrollHint = document.getElementById('scroll-hint');

    if (tableWrapper && scrollHint) {
        // Check if table is scrollable (content wider than container)
        const needsScroll = tableWrapper.scrollWidth > tableWrapper.clientWidth;
        scrollHint.style.display = needsScroll ? 'block' : 'none';
    }
}

// Fetch active season and initialize
async function initializeApp() {
    try {
        // Fetch active season from public API endpoint
        const response = await fetch(`${API_URL}/api/seasons/active`);
        const data = await response.json();

        if (data.success && (data.season || data.season_id)) {
            // Handle both response formats
            KVK_SEASON_ID = data.season ? data.season.season_id : data.season_id;

            // Load data
            await loadStats();
            await loadLeaderboard();
        } else {
            console.error('No active season found');
            statsGrid.innerHTML = '<div class="loading">⚠️ No active season configured</div>';
        }
    } catch (error) {
        console.error('Failed to fetch active season:', error);
        statsGrid.innerHTML = '<div class="loading">⚠️ Failed to load season information</div>';
    }
}

// Pagination button listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('first-page').addEventListener('click', () => goToPage(1));
    document.getElementById('prev-page').addEventListener('click', () => goToPage(currentPage - 1));
    document.getElementById('next-page').addEventListener('click', () => goToPage(currentPage + 1));
    document.getElementById('last-page').addEventListener('click', () => {
        const totalPages = Math.ceil(filteredPlayers.length / PLAYERS_PER_PAGE);
        goToPage(totalPages);
    });

    initializeApp();

    // Check table scroll on resize
    window.addEventListener('resize', checkTableScroll);
    // Initial check after a short delay to ensure table is rendered
    setTimeout(checkTableScroll, 500);
});