/**
 * RRG Dashboard — Interactive Legend Module (Phase 3)
 *
 * Responsibilities:
 * - Render HTML for the legend items.
 * - Handle click, ctrl-click, and keyboard toggles for sectors.
 * - Manage visibility state in `window.uiState.visibleSectors`.
 * - Sync CSS classes to reflect visibility visually.
 * - Communicate state changes to Dash via dcc.Store.
 */

window.rrgLegend = {
    /**
     * Render the initial legend HTML and attach event listeners.
     */
    render: function(store_data) {
        var no_update = window.dash_clientside.no_update;

        if (!store_data || !store_data.sectors) return no_update;

        var sectors = Object.keys(store_data.sectors);
        var colors = [
            '#58a6ff', '#f97316', '#22c55e', '#ef4444', '#a78bfa',
            '#f472b6', '#38bdf8', '#fbbf24', '#34d399', '#fb7185',
            '#818cf8', '#2dd4bf', '#e879f7'
        ];

        // Initialize visibility if empty
        if (Object.keys(window.uiState.visibleSectors).length === 0) {
            var initialVis = {};
            for (var i = 0; i < sectors.length; i++) {
                initialVis[sectors[i]] = true;
            }
            window.uiState.update('visibleSectors', initialVis);
        }

        var htmlStr = '';
        for (var i = 0; i < sectors.length; i++) {
            var ticker = sectors[i];
            var color = colors[i % colors.length];
            var isHidden = (window.uiState.visibleSectors[ticker] === false);
            var isHighlighted = window.rrgSearch ? window.rrgSearch.isHighlighted(ticker) : true;
            var cssClass = 'legend-item' + (isHidden ? ' legend-hidden' : '') + (!isHighlighted ? ' legend-dimmed' : '');
            var safeTickerId = ticker.replace(/\s+/g, '_');

            htmlStr += '<span class="' + cssClass + '" id="legenditem___' + safeTickerId + '" tabindex="0" role="button">' +
                       '<span class="legend-dot" style="background-color: ' + color + '"></span>' +
                       ' ' + ticker.replace('NIFTY ', '') +
                       '</span>';
        }

        setTimeout(function() {
            var legendDiv = document.getElementById('sector-legend');
            if (legendDiv) {
                legendDiv.innerHTML = htmlStr;

                if (!window.uiState.animationStatus.legendHandlersAttached) {
                    legendDiv.addEventListener('click', function(e) {
                        var item = e.target.closest('.legend-item');
                        if (!item) return;
                        
                        var itemId = item.getAttribute('id');
                        if (!itemId || !itemId.includes('legenditem___')) return;
                        
                        var sector = itemId.split('legenditem___')[1].replace(/_/g, ' ');
                        if (!sector) return;
                        
                        var vis = Object.assign({}, window.uiState.visibleSectors);
                        var activeSectors = Object.keys(vis);

                        if (e.ctrlKey || e.metaKey) {
                            vis[sector] = !vis[sector];
                        } else {
                            var visibleCount = activeSectors.filter(function(s) { return vis[s] !== false; });
                            var isOnlyVisible = (visibleCount.length === 1 && visibleCount[0] === sector);
                            
                            if (isOnlyVisible) {
                                for (var s = 0; s < activeSectors.length; s++) {
                                    vis[activeSectors[s]] = true;
                                }
                            } else {
                                for (var s = 0; s < activeSectors.length; s++) {
                                    vis[activeSectors[s]] = (activeSectors[s] === sector);
                                }
                            }
                        }
                        
                        window.uiState.update('visibleSectors', vis);
                        window.rrgLegend.syncDOMAndStore();
                    });

                    legendDiv.addEventListener('keydown', function(e) {
                        if (e.code === 'Enter' || e.code === 'Space') {
                            var item = e.target.closest('.legend-item');
                            if (item) {
                                e.preventDefault();
                                item.click();
                            }
                        }
                    });

                    window.uiState.updateNested('animationStatus', 'legendHandlersAttached', true);
                }
            }
        }, 50);

        return no_update;
    },

    /**
     * Handle "Show All" action to reset visibility.
     */
    showAll: function() {
        var vis = Object.assign({}, window.uiState.visibleSectors);
        var sectors = Object.keys(vis);
        for (var i = 0; i < sectors.length; i++) {
            vis[sectors[i]] = true;
        }
        window.uiState.update('visibleSectors', vis);
        
        this.syncDOMAndStore();
        return window.dash_clientside.no_update;
    },

    /**
     * Handle "Hide All" action.
     */
    hideAll: function() {
        var vis = Object.assign({}, window.uiState.visibleSectors);
        var sectors = Object.keys(vis);
        for (var i = 0; i < sectors.length; i++) {
            vis[sectors[i]] = false;
        }
        window.uiState.update('visibleSectors', vis);
        
        this.syncDOMAndStore();
        return window.dash_clientside.no_update;
    },

    /**
     * Sync CSS classes with state and push to Dash store.
     */
    syncDOMAndStore: function() {
        var legendDiv = document.getElementById('sector-legend');
        if (legendDiv) {
            var items = legendDiv.querySelectorAll('.legend-item');
            for (var i = 0; i < items.length; i++) {
                var itemId = items[i].getAttribute('id');
                if (itemId && itemId.includes('legenditem___')) {
                    var sector = itemId.split('legenditem___')[1].replace(/_/g, ' ');
                    var isHidden = (window.uiState.visibleSectors[sector] === false);
                    var isHighlighted = window.rrgSearch ? window.rrgSearch.isHighlighted(sector) : true;
                    
                    if (isHidden) {
                        items[i].classList.add('legend-hidden');
                    } else {
                        items[i].classList.remove('legend-hidden');
                    }

                    if (!isHighlighted) {
                        items[i].classList.add('legend-dimmed');
                    } else {
                        items[i].classList.remove('legend-dimmed');
                    }
                }
            }
        }

        var visibilityData = JSON.parse(JSON.stringify(window.uiState.visibleSectors));
        
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props('store-sector-visibility', { data: visibilityData });
        } else {
            var storeEl = document.getElementById('store-sector-visibility');
            if (storeEl && storeEl._dashprivate_setProps) {
                storeEl._dashprivate_setProps({ data: visibilityData });
            }
        }
    }
};
