// ========================================
// Configuration
// ========================================
// Use localhost for development, production URL for deployed site
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://kd3584-production.up.railway.app';
const KVK_SEASON_ID = 'season_1';
const PLAYERS_PER_PAGE = 50;

// ========================================
// State
// ========================================
let allPlayers = [];
let currentPage = 1;
let filteredPlayers = [];

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
// Utility Functions
// ========================================

/**
 * Format number with space as thousand separator
 * Example: 6526578201 -> "6 526 578 201"
 */
function formatFullNumber(num) {
    if (!num && num !== 0) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/**
 * Format number for summary cards (shortened)
 * Example: 6526578201 -> "6.53B"
 */
function formatShortNumber(num) {
    if (!num && num !== 0) return '0';
    if (num >= 1000000000) return (num / 1000000000).toFixed(2) + 'B';
    if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

/**
 * Format delta number with space separators (full number)
 * Example: 125000000 -> "125 000 000"
 */
function formatDeltaNumber(num) {
    if (!num || num === 0) return '0';
    const absNum = Math.abs(num);
    return absNum.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

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
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
}

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
                    <div class="title">🏆 Top Kill Points</div>
                    <div class="name">${tops.kill_points?.name || 'N/A'}</div>
                    <div class="stat">${formatShortNumber(tops.kill_points?.value)}</div>
                </div>
                <div class="top-card blue">
                    <div class="title">💎 Top Power</div>
                    <div class="name">${tops.power?.name || 'N/A'}</div>
                    <div class="stat">${formatShortNumber(tops.power?.value)}</div>
                </div>
                <div class="top-card purple">
                    <div class="title">⚔️ Top T5 Kills</div>
                    <div class="name">${tops.t5_kills?.name || 'N/A'}</div>
                    <div class="stat">${formatShortNumber(tops.t5_kills?.value)}</div>
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
        
    } catch (error) {
        console.error('Failed to load leaderboard:', error);
        leaderboardBody.innerHTML = '<tr><td colspan="9" class="loading">⚠️ No data available</td></tr>';
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

        const stats = player.stats || {};
        const delta = player.delta || {};

        return `
            <tr class="${rowClass}" onclick="window.location.href='player.html?id=${player.governor_id}'">
                <td>${rankDisplay}</td>
                <td>
                    <div class="player-name">${player.governor_name}</div>
                    <div class="player-id">ID: ${player.governor_id}</div>
                </td>
                <td class="text-right">
                    <div class="stat-cell">
                        <span class="stat-value gained-stat">${formatFullNumber(delta.kill_points || 0)}</span>
                    </div>
                </td>
                <td class="text-right">
                    <div class="stat-cell">
                        <span class="stat-value gained-stat">${formatFullNumber(delta.deads || 0)}</span>
                    </div>
                </td>
                <td class="text-right">
                    ${createStatCell(stats.power, delta.power)}
                </td>
                <td class="text-right">
                    ${createStatCell(stats.kill_points, delta.kill_points)}
                </td>
                <td class="text-right">
                    ${createStatCell(stats.t5_kills, delta.t5_kills)}
                </td>
                <td class="text-right">
                    ${createStatCell(stats.t4_kills, delta.t4_kills)}
                </td>
                <td class="text-right">
                    ${createStatCell(stats.deads, delta.deads)}
                </td>
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

// Pagination button listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('first-page').addEventListener('click', () => goToPage(1));
    document.getElementById('prev-page').addEventListener('click', () => goToPage(currentPage - 1));
    document.getElementById('next-page').addEventListener('click', () => goToPage(currentPage + 1));
    document.getElementById('last-page').addEventListener('click', () => {
        const totalPages = Math.ceil(filteredPlayers.length / PLAYERS_PER_PAGE);
        goToPage(totalPages);
    });

    loadStats();
    loadLeaderboard();

    // Check table scroll on resize
    window.addEventListener('resize', checkTableScroll);
    // Initial check after a short delay to ensure table is rendered
    setTimeout(checkTableScroll, 500);
});