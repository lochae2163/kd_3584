// ========================================
// Configuration
// ========================================
// Use localhost for development, production URL for deployed site
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://kd3584-production.up.railway.app';
let KVK_SEASON_ID = null;

// ========================================
// Get Player ID from URL
// ========================================
const urlParams = new URLSearchParams(window.location.search);
const governorId = urlParams.get('id');

if (!governorId) {
    window.location.href = 'index.html';
}

// ========================================
// DOM Elements
// ========================================
const playerName = document.getElementById('player-name');
const playerId = document.getElementById('player-id');
const rankSection = document.getElementById('rank-section');
const statsCards = document.getElementById('stats-cards');
const deltaGrid = document.getElementById('delta-grid');

// ========================================
// Utility Functions
// ========================================
function formatFullNumber(num) {
    if (!num && num !== 0) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

function formatShortNumber(num) {
    if (!num && num !== 0) return '0';
    if (num >= 1000000000) return (num / 1000000000).toFixed(2) + 'B';
    if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function getDeltaClass(value) {
    if (value > 0) return 'positive';
    if (value < 0) return 'negative';
    return 'neutral';
}

function getDeltaArrow(value) {
    if (value > 0) return '↑';
    if (value < 0) return '↓';
    return '→';
}

function getDeltaPrefix(value) {
    if (value > 0) return '+';
    return '';
}

// ========================================
// Load Player Data
// ========================================
async function loadPlayerData() {
    try {
        const response = await fetch(
            `${API_URL}/api/player/${governorId}?kvk_season_id=${KVK_SEASON_ID}`
        );
        
        if (!response.ok) {
            throw new Error('Player not found');
        }
        
        const data = await response.json();
        const player = data.player;
        
        if (!player) {
            throw new Error('Player data not found');
        }
        
        renderPlayerData(player);
        renderCharts(player);
        
    } catch (error) {
        console.error('Failed to load player:', error);
        statsCards.innerHTML = `
            <div class="error-message">
                <h3>❌ Player Not Found</h3>
                <p>Could not find player with ID: ${governorId}</p>
                <a href="index.html" class="back-btn">← Back to Leaderboard</a>
            </div>
        `;
    }
}

// ========================================
// Render Player Data
// ========================================
function renderPlayerData(player) {
    const stats = player.stats || {};
    const delta = player.delta || {};
    
    // Header
    playerName.textContent = `🎮 ${player.governor_name}`;
    playerId.textContent = `Governor ID: ${player.governor_id}`;
    
    // Rank Badge
    let rankBadge = '';
    if (player.rank === 1) {
        rankBadge = '<div class="rank-badge-large gold">🥇 #1</div>';
    } else if (player.rank === 2) {
        rankBadge = '<div class="rank-badge-large silver">🥈 #2</div>';
    } else if (player.rank === 3) {
        rankBadge = '<div class="rank-badge-large bronze">🥉 #3</div>';
    } else if (player.rank) {
        rankBadge = `<div class="rank-badge-large">Rank #${player.rank}</div>`;
    }
    rankSection.innerHTML = rankBadge;
    
    // Stats Cards
    const statsData = [
        { label: 'Power', icon: '💪', value: stats.power, delta: delta.power, color: 'blue' },
        { label: 'Kill Points', icon: '⚔️', value: stats.kill_points, delta: delta.kill_points, color: 'green' },
        { label: 'T5 Kills', icon: '🎯', value: stats.t5_kills, delta: delta.t5_kills, color: 'purple' },
        { label: 'T4 Kills', icon: '🏹', value: stats.t4_kills, delta: delta.t4_kills, color: 'orange' },
        { label: 'Deaths', icon: '💀', value: stats.deads, delta: delta.deads, color: 'red' }
    ];
    
    statsCards.innerHTML = statsData.map(stat => `
        <div class="player-stat-card ${stat.color}">
            <div class="stat-icon">${stat.icon}</div>
            <div class="stat-info">
                <div class="stat-label">${stat.label}</div>
                <div class="stat-main-value">${formatFullNumber(stat.value)}</div>
                ${stat.delta !== 0 ? `
                    <div class="stat-delta ${getDeltaClass(stat.delta)}">
                        ${getDeltaArrow(stat.delta)} ${getDeltaPrefix(stat.delta)}${formatFullNumber(Math.abs(stat.delta))}
                    </div>
                ` : '<div class="stat-delta neutral">No change</div>'}
            </div>
        </div>
    `).join('');
    
    // Delta Summary
    const deltaData = [
        { label: 'T5 Kills', icon: '🎯', value: delta.t5_kills },
        { label: 'T4 Kills', icon: '🏹', value: delta.t4_kills },
        { label: 'Deaths', icon: '💀', value: delta.deads },
        { label: 'Kill Points', icon: '⚔️', value: delta.kill_points },
        { label: 'Power', icon: '💪', value: delta.power }
    ];
    
    deltaGrid.innerHTML = deltaData.map(stat => `
        <div class="delta-card ${getDeltaClass(stat.value)}">
            <div class="delta-icon">${stat.icon}</div>
            <div class="delta-label">${stat.label}</div>
            <div class="delta-value">
                ${getDeltaArrow(stat.value)} ${getDeltaPrefix(stat.value)}${formatFullNumber(Math.abs(stat.value || 0))}
            </div>
        </div>
    `).join('');
}

// ========================================
// Render Charts
// ========================================
function renderCharts(player) {
    const stats = player.stats || {};
    const delta = player.delta || {};
    
    // Chart 1: T5 vs T4 Kills (Donut)
    renderKillsDonutChart(stats);
    
    // Chart 2: KvK Contribution Delta (Bar)
    renderDeltaBarChart(delta);
}

// ========================================
// Chart 1: T5 vs T4 Kills Distribution
// ========================================
function renderKillsDonutChart(stats) {
    const ctx = document.getElementById('kills-chart').getContext('2d');
    
    const t5Kills = stats.t5_kills || 0;
    const t4Kills = stats.t4_kills || 0;
    const total = t5Kills + t4Kills;
    
    const t5Percent = total > 0 ? ((t5Kills / total) * 100).toFixed(1) : 0;
    const t4Percent = total > 0 ? ((t4Kills / total) * 100).toFixed(1) : 0;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [`T5 Kills (${t5Percent}%)`, `T4 Kills (${t4Percent}%)`],
            datasets: [{
                data: [t5Kills, t4Kills],
                backgroundColor: [
                    'rgba(168, 85, 247, 0.85)',
                    'rgba(249, 115, 22, 0.85)'
                ],
                borderColor: [
                    'rgba(168, 85, 247, 1)',
                    'rgba(249, 115, 22, 1)'
                ],
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e2e8f0',
                        padding: 15,
                        font: { size: 13, weight: '500' }
                    }
                },
                title: {
                    display: true,
                    text: 'T5 vs T4 Kill Distribution',
                    color: '#ffffff',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 15 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${formatFullNumber(context.raw)} kills`;
                        }
                    }
                }
            }
        }
    });
}

// ========================================
// Chart 2: KvK Contribution Delta (Horizontal Bar)
// ========================================
function renderDeltaBarChart(delta) {
    const ctx = document.getElementById('delta-chart').getContext('2d');
    
    const data = [
        { label: 'T5 Kills', value: delta.t5_kills || 0 },
        { label: 'T4 Kills', value: delta.t4_kills || 0 },
        { label: 'Deaths', value: delta.deads || 0 }
    ];
    
    const colors = data.map(d => {
        // For deaths, positive is bad (red), negative is good (green)
        if (d.label === 'Deaths') {
            if (d.value > 0) return 'rgba(239, 68, 68, 0.85)';
            if (d.value < 0) return 'rgba(34, 197, 94, 0.85)';
        } else {
            if (d.value > 0) return 'rgba(34, 197, 94, 0.85)';
            if (d.value < 0) return 'rgba(239, 68, 68, 0.85)';
        }
        return 'rgba(100, 116, 139, 0.85)';
    });
    
    const borderColors = data.map(d => {
        if (d.label === 'Deaths') {
            if (d.value > 0) return 'rgba(239, 68, 68, 1)';
            if (d.value < 0) return 'rgba(34, 197, 94, 1)';
        } else {
            if (d.value > 0) return 'rgba(34, 197, 94, 1)';
            if (d.value < 0) return 'rgba(239, 68, 68, 1)';
        }
        return 'rgba(100, 116, 139, 1)';
    });
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                label: 'Change from Baseline',
                data: data.map(d => d.value),
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'KvK Contribution (Change from Baseline)',
                    color: '#ffffff',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 15 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const prefix = value >= 0 ? '+' : '';
                            return `${prefix}${formatFullNumber(value)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            if (value === 0) return '0';
                            return formatShortNumber(value);
                        }
                    },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                },
                y: {
                    ticks: { 
                        color: '#e2e8f0',
                        font: { size: 13, weight: '500' }
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

// ========================================
// Load and Render Timeline
// ========================================
async function loadPlayerTimeline() {
    try {
        const response = await fetch(
            `${API_URL}/api/player/${governorId}/timeline?kvk_season_id=${KVK_SEASON_ID}`
        );

        if (!response.ok) {
            console.log('No timeline data available');
            return;
        }

        const data = await response.json();

        if (!data.success || !data.timeline || data.timeline.length < 2) {
            console.log('Insufficient timeline data');
            return;
        }

        // Show the timeline section
        document.getElementById('timeline-section').style.display = 'block';

        renderTimelineChart(data);
        renderTimelineSnapshots(data);

    } catch (error) {
        console.error('Failed to load timeline:', error);
    }
}

function renderTimelineChart(data) {
    const timeline = data.timeline;
    const ctx = document.getElementById('timeline-chart').getContext('2d');

    // Extract data for chart
    const labels = timeline.map(snapshot => {
        const date = new Date(snapshot.timestamp);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const kpData = timeline.map(snapshot => snapshot.stats.kill_points);
    const powerData = timeline.map(snapshot => snapshot.stats.power);
    const rankData = timeline.map(snapshot => snapshot.rank);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Kill Points',
                    data: kpData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    yAxisID: 'y',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Power',
                    data: powerData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    yAxisID: 'y',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Rank',
                    data: rankData,
                    borderColor: 'rgba(255, 206, 86, 1)',
                    backgroundColor: 'rgba(255, 206, 86, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#e8eaed',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.dataset.label === 'Rank') {
                                label += '#' + context.parsed.y;
                            } else {
                                label += formatShortNumber(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        color: '#e8eaed',
                        callback: function(value) {
                            return formatShortNumber(value);
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    reverse: true, // Lower rank number is better
                    ticks: {
                        color: '#e8eaed',
                        callback: function(value) {
                            return '#' + value;
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    ticks: {
                        color: '#e8eaed'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

function renderTimelineSnapshots(data) {
    const timeline = data.timeline;
    const snapshotsContainer = document.getElementById('timeline-snapshots');

    let html = '<div class="snapshots-grid">';

    timeline.forEach((snapshot, index) => {
        const date = new Date(snapshot.timestamp);
        const dateStr = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const kpDelta = snapshot.delta.kill_points;
        const deltaClass = getDeltaClass(kpDelta);
        const deltaPrefix = getDeltaPrefix(kpDelta);

        html += `
            <div class="snapshot-card">
                <div class="snapshot-header">
                    <span class="snapshot-number">#${index + 1}</span>
                    <span class="snapshot-rank">Rank #${snapshot.rank}</span>
                </div>
                <div class="snapshot-date">${dateStr}</div>
                <div class="snapshot-description">${snapshot.description || 'No description'}</div>
                <div class="snapshot-stats">
                    <div class="snapshot-stat">
                        <span class="stat-label">KP</span>
                        <span class="stat-value">${formatShortNumber(snapshot.stats.kill_points)}</span>
                        <span class="stat-delta ${deltaClass}">${deltaPrefix}${formatShortNumber(kpDelta)}</span>
                    </div>
                    <div class="snapshot-stat">
                        <span class="stat-label">Power</span>
                        <span class="stat-value">${formatShortNumber(snapshot.stats.power)}</span>
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    snapshotsContainer.innerHTML = html;
}

// ========================================
// Initialize
// ========================================
async function initializeApp() {
    try {
        // Fetch active season from public API endpoint
        const response = await fetch(`${API_URL}/api/seasons/active`);
        const data = await response.json();

        if (data.success && (data.season || data.season_id)) {
            // Handle both response formats
            KVK_SEASON_ID = data.season ? data.season.season_id : data.season_id;
            await loadPlayerData();
            await loadPlayerTimeline();
        } else {
            playerName.textContent = 'Error: No active season';
            statsCards.innerHTML = '<div class="error">No active season found. Please activate a season in the admin panel.</div>';
        }
    } catch (error) {
        console.error('Failed to fetch active season:', error);
        playerName.textContent = 'Error loading season';
        statsCards.innerHTML = '<div class="error">Failed to load active season.</div>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});