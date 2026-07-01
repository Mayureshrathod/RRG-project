/**
 * RRG Dashboard — Centralized UI State Management
 * 
 * This file is prefixed with '00_' to ensure Dash loads it before other scripts.
 * It serves as the single source of truth for the frontend rendering engine.
 */

window.uiState = {
    // Core Data
    currentFrame: 0,
    benchmark: 'NIFTY 50',
    timeframe: 'weekly',
    
    // UI Settings
    trailLength: 10,
    playbackSpeed: 500,
    theme: 'dark',
    searchFilter: '',
    
    // Complex State
    visibleSectors: {}, // Example: { 'NIFTY BANK': true, 'NIFTY IT': false }
    animationStatus: {
        isPlaying: false,
        userHasZoomed: false,
        relayoutListenerAttached: false
    },
    
    // Reactive Listeners
    _listeners: [],
    
    /**
     * Subscribe to state changes.
     * @param {function} callback - Function called with the updated state when changes occur.
     */
    subscribe: function(callback) {
        this._listeners.push(callback);
    },
    
    /**
     * Notify all listeners of a state change.
     */
    notify: function() {
        var stateContext = this;
        this._listeners.forEach(function(cb) {
            cb(stateContext);
        });
    },
    
    /**
     * Update state dynamically.
     * @param {string|object} key - Property name, or an object containing multiple properties.
     * @param {*} value - Property value (if key is a string).
     */
    update: function(key, value) {
        var changed = false;
        if (typeof key === 'object') {
            for (var prop in key) {
                if (Object.prototype.hasOwnProperty.call(key, prop)) {
                    if (this[prop] !== key[prop]) {
                        this[prop] = key[prop];
                        changed = true;
                    }
                }
            }
        } else {
            if (this[key] !== value) {
                this[key] = value;
                changed = true;
            }
        }
        
        if (changed) {
            this.notify();
        }
    },

    /**
     * Update a deeply nested property (e.g. animationStatus.userHasZoomed).
     * @param {string} parentKey - The parent object key (e.g. 'animationStatus')
     * @param {string} childKey - The child property key (e.g. 'userHasZoomed')
     * @param {*} value - The new value
     */
    updateNested: function(parentKey, childKey, value) {
        if (this[parentKey] && this[parentKey][childKey] !== value) {
            this[parentKey][childKey] = value;
            this.notify();
        }
    }
};
