// ========================================
// KvK Tracker - Shared Utilities
// ========================================
// This file contains shared utility functions used across all frontend pages
// to eliminate code duplication and maintain consistency.

// ========================================
// Configuration
// ========================================

/**
 * API base URL configuration
 * Automatically selects localhost for development or production URL for deployed site
 */
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://kd3584-production.up.railway.app';

// ========================================
// Number Formatting Functions
// ========================================

/**
 * Format number with space as thousand separator (full number)
 * Example: 6526578201 -> "6 526 578 201"
 * Used in: script.js, player.js
 */
function formatFullNumber(num) {
    if (!num && num !== 0) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/**
 * Format number for summary cards (shortened with units)
 * Example: 6526578201 -> "6.53B"
 * Used in: script.js, player.js
 */
function formatShortNumber(num) {
    if (!num && num !== 0) return '0';
    if (num >= 1000000000) return (num / 1000000000).toFixed(2) + 'B';
    if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

/**
 * Format number with space as thousand separator (for regular display)
 * Example: 1234567 -> "1 234 567"
 * Used in: admin.js, contribution.js
 */
function formatNumber(num) {
    if (!num) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/**
 * Format delta number with space separators (full number, used for gained stats)
 * Example: 125000000 -> "125 000 000"
 * Used in: script.js
 */
function formatDeltaNumber(num) {
    if (!num || num === 0) return '0';
    const absNum = Math.abs(num);
    return absNum.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

// ========================================
// Date Formatting Functions
// ========================================

/**
 * Format date string to UTC format
 * Example: "2024-01-15T10:30:00" -> "01/15/2024, 10:30:00 UTC"
 * Used in: admin.js, script.js
 *
 * Note: Database stores timestamps as naive datetimes in UTC.
 * We must append 'Z' to tell JavaScript to parse as UTC, not local time.
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    // Ensure the date is parsed as UTC by appending 'Z' if not present
    let utcString = dateString;
    if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
        utcString = dateString + 'Z';
    }
    const date = new Date(utcString);
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

// ========================================
// Delta Display Functions
// ========================================

/**
 * Get CSS class for delta value (positive/negative/neutral)
 * Used in: player.js
 */
function getDeltaClass(value) {
    if (value > 0) return 'positive';
    if (value < 0) return 'negative';
    return 'neutral';
}

/**
 * Get arrow indicator for delta value
 * Used in: player.js
 */
function getDeltaArrow(value) {
    if (value > 0) return '↑';
    if (value < 0) return '↓';
    return '→';
}

/**
 * Get prefix for delta value (+/-)
 * Used in: player.js
 */
function getDeltaPrefix(value) {
    if (value > 0) return '+';
    return '';
}

// ========================================
// UI Helper Functions
// ========================================

/**
 * Show loading state in an element
 * Used in: contribution.js
 */
function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="loading">${message}</div>`;
    }
}

/**
 * Show error message in an element
 * Used in: contribution.js
 */
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="error-message">❌ ${message}</div>`;
    }
}

/**
 * Show message with type (success/error/warning)
 * Used in: admin.js
 */
function showMessage(element, type, message) {
    element.innerHTML = `<div class="message ${type}">${message}</div>`;
}

// ========================================
// Export Note
// ========================================
// All functions are globally available since they're defined in the global scope.
// To use these utilities, include this script BEFORE your page-specific JavaScript:
// <script src="utilities.js"></script>
// <script src="your-page-script.js"></script>
