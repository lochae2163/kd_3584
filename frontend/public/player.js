// ========================================
// Configuration
// ========================================
// API_URL and utility functions are now in utilities.js
let KVK_SEASON_ID = null;
let cachedPlayerData = null;
let killsChart = null;
let deltaChart = null;
let timelineChart = null;
let cachedTimelineData = null;

// ========================================
// Get Player ID from URL
// ========================================
const urlParams = new URLSearchParams(window.location.search);
const governorId = urlParams.get('id');

if (!governorId) {
    window.location.href = 'dashboard.html';
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

        cachedPlayerData = player;
        renderPlayerData(player);
        renderCharts(player);

    } catch (error) {
        console.error('Failed to load player:', error);
        statsCards.innerHTML = `
            <div class="error-message">
                <h3>${t('player.notFound')}</h3>
                <p>${t('player.couldNotFind', { id: governorId })}</p>
                <a href="dashboard.html" class="back-btn">${t('common.backToLeaderboard')}</a>
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
    playerId.textContent = `${t('common.governorId')}: ${player.governor_id}`;

    // Rank Badge
    let rankBadge = '';
    if (player.rank === 1) {
        rankBadge = '<div class="rank-badge-large gold">🥇 #1</div>';
    } else if (player.rank === 2) {
        rankBadge = '<div class="rank-badge-large silver">🥈 #2</div>';
    } else if (player.rank === 3) {
        rankBadge = '<div class="rank-badge-large bronze">🥉 #3</div>';
    } else if (player.rank) {
        rankBadge = `<div class="rank-badge-large">${t('player.rankLabel')} #${player.rank}</div>`;
    }
    rankSection.innerHTML = rankBadge;

    // Stats Cards
    const statsData = [
        { label: t('common.power'), icon: '💪', value: stats.power, delta: delta.power, color: 'blue' },
        { label: t('common.killPoints'), icon: '⚔️', value: stats.kill_points, delta: delta.kill_points, color: 'green' },
        { label: t('common.t5Kills'), icon: '🎯', value: stats.t5_kills, delta: delta.t5_kills, color: 'purple' },
        { label: t('common.t4Kills'), icon: '🏹', value: stats.t4_kills, delta: delta.t4_kills, color: 'orange' },
        { label: t('common.deaths'), icon: '💀', value: stats.deads, delta: delta.deads, color: 'red' }
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
                ` : `<div class="stat-delta neutral">${t('common.noChange')}</div>`}
            </div>
        </div>
    `).join('');

    // Delta Summary
    const deltaData = [
        { label: t('common.t5Kills'), icon: '🎯', value: delta.t5_kills },
        { label: t('common.t4Kills'), icon: '🏹', value: delta.t4_kills },
        { label: t('common.deaths'), icon: '💀', value: delta.deads },
        { label: t('common.killPoints'), icon: '⚔️', value: delta.kill_points },
        { label: t('common.power'), icon: '💪', value: delta.power }
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

    renderKillsDonutChart(stats);
    renderDeltaBarChart(delta);
}

// ========================================
// Chart 1: T5 vs T4 Kills Distribution
// ========================================
function renderKillsDonutChart(stats) {
    const canvas = document.getElementById('kills-chart');
    if (killsChart) { killsChart.destroy(); killsChart = null; }

    const ctx = canvas.getContext('2d');
    const t5Kills = stats.t5_kills || 0;
    const t4Kills = stats.t4_kills || 0;
    const total = t5Kills + t4Kills;

    const t5Percent = total > 0 ? ((t5Kills / total) * 100).toFixed(1) : 0;
    const t4Percent = total > 0 ? ((t4Kills / total) * 100).toFixed(1) : 0;

    killsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [`${t('common.t5Kills')} (${t5Percent}%)`, `${t('common.t4Kills')} (${t4Percent}%)`],
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
                    text: t('player.t5vsT4'),
                    color: '#ffffff',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 15 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${formatFullNumber(context.raw)} ${t('player.kills')}`;
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
    const canvas = document.getElementById('delta-chart');
    if (deltaChart) { deltaChart.destroy(); deltaChart = null; }

    const ctx = canvas.getContext('2d');
    const data = [
        { label: t('common.t5Kills'), value: delta.t5_kills || 0 },
        { label: t('common.t4Kills'), value: delta.t4_kills || 0 },
        { label: t('common.deaths'), value: delta.deads || 0 }
    ];

    const colors = data.map((d, i) => {
        if (i === 2) { // Deaths
            if (d.value > 0) return 'rgba(239, 68, 68, 0.85)';
            if (d.value < 0) return 'rgba(34, 197, 94, 0.85)';
        } else {
            if (d.value > 0) return 'rgba(34, 197, 94, 0.85)';
            if (d.value < 0) return 'rgba(239, 68, 68, 0.85)';
        }
        return 'rgba(100, 116, 139, 0.85)';
    });

    const borderColors = data.map((d, i) => {
        if (i === 2) {
            if (d.value > 0) return 'rgba(239, 68, 68, 1)';
            if (d.value < 0) return 'rgba(34, 197, 94, 1)';
        } else {
            if (d.value > 0) return 'rgba(34, 197, 94, 1)';
            if (d.value < 0) return 'rgba(239, 68, 68, 1)';
        }
        return 'rgba(100, 116, 139, 1)';
    });

    deltaChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                label: t('player.changeFromBaseline'),
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
                    text: t('player.kvkContribution'),
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
            return;
        }

        const data = await response.json();

        if (!data.success || !data.timeline || data.timeline.length < 2) {
            return;
        }

        cachedTimelineData = data;
        document.getElementById('timeline-section').style.display = 'block';
        renderTimelineChart(data);
        renderTimelineSnapshots(data);

    } catch (error) {
        console.error('Failed to load timeline:', error);
    }
}

function renderTimelineChart(data) {
    const timeline = data.timeline;
    const canvas = document.getElementById('timeline-chart');
    if (timelineChart) { timelineChart.destroy(); timelineChart = null; }

    const ctx = canvas.getContext('2d');
    const locale = I18n.getLang() === 'ja' ? 'ja-JP' : 'en-US';

    const labels = timeline.map(snapshot => {
        const date = new Date(snapshot.timestamp);
        return date.toLocaleDateString(locale, { month: 'short', day: 'numeric' });
    });

    const kpData = timeline.map(snapshot => snapshot.stats.kill_points);
    const powerData = timeline.map(snapshot => snapshot.stats.power);
    const rankData = timeline.map(snapshot => snapshot.rank);

    timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: t('common.killPoints'),
                    data: kpData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    yAxisID: 'y',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: t('common.power'),
                    data: powerData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    yAxisID: 'y',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: t('player.rankLabel'),
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
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.dataset.label === t('player.rankLabel')) {
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
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    reverse: true,
                    ticks: {
                        color: '#e8eaed',
                        callback: function(value) {
                            return '#' + value;
                        }
                    },
                    grid: { drawOnChartArea: false }
                },
                x: {
                    ticks: { color: '#e8eaed' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

function renderTimelineSnapshots(data) {
    const timeline = data.timeline;
    const snapshotsContainer = document.getElementById('timeline-snapshots');
    const locale = I18n.getLang() === 'ja' ? 'ja-JP' : 'en-US';

    let html = '<div class="snapshots-grid">';

    timeline.forEach((snapshot, index) => {
        const date = new Date(snapshot.timestamp);
        const dateStr = date.toLocaleDateString(locale, {
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
                    <span class="snapshot-rank">${t('player.rankLabel')} #${snapshot.rank}</span>
                </div>
                <div class="snapshot-date">${dateStr}</div>
                <div class="snapshot-description">${snapshot.description || t('player.noDescription')}</div>
                <div class="snapshot-stats">
                    <div class="snapshot-stat">
                        <span class="stat-label">${t('player.kp')}</span>
                        <span class="stat-value">${formatShortNumber(snapshot.stats.kill_points)}</span>
                        <span class="stat-delta ${deltaClass}">${deltaPrefix}${formatShortNumber(kpDelta)}</span>
                    </div>
                    <div class="snapshot-stat">
                        <span class="stat-label">${t('common.power')}</span>
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
// Language change handler
// ========================================
window.addEventListener('languageChanged', () => {
    if (cachedPlayerData) {
        renderPlayerData(cachedPlayerData);
        renderCharts(cachedPlayerData);
    }
    if (cachedTimelineData) {
        renderTimelineChart(cachedTimelineData);
        renderTimelineSnapshots(cachedTimelineData);
    }
});

// ========================================
// Initialize
// ========================================
async function initializeApp() {
    try {
        const response = await fetch(`${API_URL}/api/seasons/active`);
        const data = await response.json();

        if (data.success && (data.season || data.season_id)) {
            KVK_SEASON_ID = data.season ? data.season.season_id : data.season_id;
            await loadPlayerData();
            await loadPlayerTimeline();
        } else {
            playerName.textContent = t('player.noActiveSeason');
            statsCards.innerHTML = `<div class="error">${t('player.noActiveSeasonDesc')}</div>`;
        }
    } catch (error) {
        console.error('Failed to fetch active season:', error);
        playerName.textContent = t('player.errorLoadingSeason');
        statsCards.innerHTML = `<div class="error">${t('player.failedLoadSeason')}</div>`;
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await I18n.init();
    initializeApp();
});
