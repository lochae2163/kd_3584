// ========================================
// Configuration
// ========================================
const API_URL = 'http://localhost:8001';
const KVK_SEASON_ID = 'season_1';

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
// Initialize
// ========================================
document.addEventListener('DOMContentLoaded', loadPlayerData);