/**
 * RRG Dashboard — Table Renderer Module (Phase 5)
 *
 * Responsibilities:
 * - Calculate current sector values (RS Ratio, RS Momentum) for the current frame.
 * - Determine the current trend direction.
 * - Calculate Quadrant counts (Leading, Weakening, Lagging, Improving).
 * - Rank and sort the table data.
 * - Return the structured data to Dash to render the DataTable and quadrant summary.
 */

window.rrgTable = {
    /**
     * Renders the table data and quadrant counts based on the current UI state.
     * @param {Object} store_data - The data from the dcc.Store.
     * @returns {Object} An object containing table_data (array) and counts_div (Dash HTML components).
     */
    render: function(store_data) {
        var sectors = Object.keys(store_data.sectors);
        var table_data = [];
        var quadrant_counts = { leading: 0, weakening: 0, lagging: 0, improving: 0 };
        var vis = window.uiState.visibleSectors;

        for (var i = 0; i < sectors.length; i++) {
            var ticker = sectors[i];
            var sd = store_data.sectors[ticker];
            var is_visible = (vis[ticker] !== false);
            
            var end_idx = window.uiState.currentFrame + 1;
            var start_idx = Math.max(0, end_idx - window.uiState.trailLength);
            if (end_idx <= 0 || !sd.rsr || sd.rsr.length === 0) continue;
            
            var x_trail = sd.rsr.slice(start_idx, end_idx);
            var y_trail = sd.rsm.slice(start_idx, end_idx);
            if (x_trail.length === 0) continue;
            
            var last_x = x_trail[x_trail.length - 1];
            var last_y = y_trail[y_trail.length - 1];

            var current_quadrant = sd.quadrant[end_idx - 1] || 'unknown';
            var current_direction = sd.direction ? sd.direction[end_idx - 1] : 0;
            var current_rank = sd.rank ? sd.rank[end_idx - 1] : 0;

            var trend = '-';
            if (current_direction !== null && current_direction !== undefined && !isNaN(current_direction)) {
                var d = current_direction;
                if (d >= -22.5 && d < 22.5) trend = 'Right';
                else if (d >= 22.5 && d < 67.5) trend = 'Up-Right';
                else if (d >= 67.5 && d < 112.5) trend = 'Up';
                else if (d >= 112.5 && d < 157.5) trend = 'Up-Left';
                else if (d >= 157.5 || d < -157.5) trend = 'Left';
                else if (d >= -157.5 && d < -112.5) trend = 'Down-Left';
                else if (d >= -112.5 && d < -67.5) trend = 'Down';
                else if (d >= -67.5 && d < -22.5) trend = 'Down-Right';
            }

            var is_highlighted = window.rrgSearch ? window.rrgSearch.isHighlighted(ticker) : true;
            if (is_visible && is_highlighted) {
                table_data.push({
                    'Sector': ticker.replace('NIFTY ', ''),
                    'Quadrant': current_quadrant,
                    'RS Ratio': last_x !== null ? last_x.toFixed(2) : '-',
                    'RS Momentum': last_y !== null ? last_y.toFixed(2) : '-',
                    'Trend': trend,
                    'Rank': current_rank !== null ? current_rank.toFixed(3) : '-'
                });

                var lower_quadrant = current_quadrant.toLowerCase();
                if (quadrant_counts[lower_quadrant] !== undefined) {
                    quadrant_counts[lower_quadrant]++;
                }
            }
        }

        // Sort table data by Rank (descending)
        table_data.sort(function(a, b) { return parseFloat(b.Rank) - parseFloat(a.Rank); });

        var createCard = function(label, count, className) {
            return {
                type: 'Div',
                namespace: 'dash_html_components',
                props: {
                    className: 'quad-stat-card ' + className,
                    children: [
                        { type: 'Div', namespace: 'dash_html_components', props: { children: label, className: 'quad-stat-label' } },
                        { type: 'Div', namespace: 'dash_html_components', props: { children: String(count), className: 'quad-stat-value' } }
                    ]
                }
            };
        };

        var counts_div = [
            createCard('Leading', quadrant_counts.leading, 'quad-leading'),
            createCard('Weakening', quadrant_counts.weakening, 'quad-weakening'),
            createCard('Lagging', quadrant_counts.lagging, 'quad-lagging'),
            createCard('Improving', quadrant_counts.improving, 'quad-improving')
        ];
        
        return { table_data: table_data, counts_div: counts_div };
    }
};
