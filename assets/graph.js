/**
 * RRG Dashboard — Graph Rendering Module (Phase 2)
 *
 * Responsibilities:
 * - Create Plotly traces
 * - Draw trails, markers, and labels
 * - Update graph layout (zooming, auto-scaling)
 * - Handle relayout events (zoom/pan)
 *
 * This module relies strictly on `window.uiState` for configuration.
 */

window.rrgGraph = {
    /**
     * Compute maximum axis deviation from 100 over the ENTIRE dataset for visible sectors.
     */
    computeGlobalAxisBounds: function(store_data, visibleSectors) {
        var max_dev = 6;
        var sectors = Object.keys(store_data.sectors);
        for (var i = 0; i < sectors.length; i++) {
            var ticker = sectors[i];
            if (visibleSectors[ticker] === false) continue;
            var sd = store_data.sectors[ticker];
            
            // Protect against empty sectors
            if (!sd || !sd.rsr || !sd.rsm) continue;
            
            for (var k = 0; k < sd.rsr.length; k++) {
                // Ignore nulls/NaNs (serialized as null from Python)
                if (sd.rsr[k] === null || sd.rsm[k] === null) continue;
                
                var dx = Math.abs(sd.rsr[k] - 100);
                var dy = Math.abs(sd.rsm[k] - 100);
                if (dx > max_dev) max_dev = dx;
                if (dy > max_dev) max_dev = dy;
            }
        }
        return Math.ceil(max_dev * 1.05);
    },

    /**
     * Render the RRG Plotly graph based on current state and data.
     * @param {Object} store_data The data from the backend dcc.Store.
     * @param {Object} current_fig The existing Plotly figure state (if any).
     * @returns {Object} A new Plotly figure object ({ data, layout }).
     */
    render: function(store_data, current_fig) {
        var no_update = window.dash_clientside.no_update;

        if (!store_data || !store_data.sectors) {
            return no_update;
        }

        var sectors = Object.keys(store_data.sectors);
        var vis = window.uiState.visibleSectors;
        
        // Track whether we need to recompute global bounds
        var visJson = JSON.stringify(vis);
        var storeRef = store_data;
        if (this._lastStoreRef !== storeRef || this._lastVisJson !== visJson) {
            window.uiState.cachedAxisBounds = this.computeGlobalAxisBounds(store_data, vis);
            this._lastStoreRef = storeRef;
            this._lastVisJson = visJson;
        }
        
        // Cache existing traces for efficient updates (Bug 2 & 5)
        var existingTraces = {};
        if (current_fig && current_fig.data) {
            for (var j = 0; j < current_fig.data.length; j++) {
                var t = current_fig.data[j];
                if (t.name) existingTraces[t.name] = t;
            }
        }
        
        var trail_traces = [];
        var endpoint_traces = [];
        
        var colors = [
            '#58a6ff', '#f97316', '#22c55e', '#ef4444', '#a78bfa',
            '#f472b6', '#38bdf8', '#fbbf24', '#34d399', '#fb7185',
            '#818cf8', '#2dd4bf', '#e879f7'
        ];

        // We only want to animate if the timeline frame actually advanced.
        // If it's just a visibility toggle, we should snap instantly.
        var previousFrame = window.uiState.lastRenderedFrame;
        var currentFrame = window.uiState.currentFrame;
        window.uiState.lastRenderedFrame = currentFrame;

        for (var i = 0; i < sectors.length; i++) {
            var ticker = sectors[i];
            var sd = store_data.sectors[ticker];
            var is_visible = (vis[ticker] !== false);

            var end_idx = currentFrame + 1;
            var start_idx = Math.max(0, end_idx - window.uiState.trailLength);

            if (end_idx <= 0 || !sd.rsr || sd.rsr.length === 0) continue;

            var x_trail = sd.rsr.slice(start_idx, end_idx);
            var y_trail = sd.rsm.slice(start_idx, end_idx);

            if (x_trail.length === 0) continue;

            var is_highlighted = window.rrgSearch ? window.rrgSearch.isHighlighted(ticker) : true;
            var color = colors[i % colors.length];
            var last_x = x_trail[x_trail.length - 1];
            var last_y = y_trail[y_trail.length - 1];

            var sum_x = 0, sum_y = 0;
            for (var t_idx = 0; t_idx < x_trail.length; t_idx++) {
                sum_x += x_trail[t_idx];
                sum_y += y_trail[t_idx];
            }
            var cm_x = sum_x / x_trail.length;
            var cm_y = sum_y / x_trail.length;
            
            var textpos = 'top right';
            if (x_trail.length > 1) {
                var dx = last_x - cm_x;
                var dy = last_y - cm_y;
                if (dx >= 0 && dy >= 0) textpos = 'top right';
                else if (dx >= 0 && dy < 0) textpos = 'bottom right';
                else if (dx < 0 && dy >= 0) textpos = 'top left';
                else textpos = 'bottom left';
            } else {
                if (last_x >= 100 && last_y >= 100) textpos = 'top right';
                else if (last_x >= 100 && last_y < 100) textpos = 'bottom right';
                else if (last_x < 100 && last_y < 100) textpos = 'bottom left';
                else textpos = 'top left';
            }

            var len = x_trail.length;
            var max_idx = len - 1;
            
            var marker_sizes = new Array(len - 1);
            var marker_opacities = new Array(len - 1);
            var base_opacity = 0.15;
            var opacity_range = 0.85;
            
            for (var m = 0; m < len - 1; m++) {
                marker_sizes[m] = is_highlighted ? 4 : 2;
                var ratio = max_idx > 0 ? (m / max_idx) : 1;
                marker_opacities[m] = base_opacity + (opacity_range * ratio);
            }

            var trail_x = x_trail.slice(0, -1);
            var trail_y = y_trail.slice(0, -1);
            
            var trailName = ticker + ' Trail';
            if (trail_x.length > 0) {
                var trailTrace = existingTraces[trailName] || {};
                trailTrace.x = trail_x;
                trailTrace.y = trail_y;
                trailTrace.mode = 'lines+markers';
                trailTrace.name = trailName;
                trailTrace.visible = is_visible;
                trailTrace.line = { color: color, width: is_highlighted ? 2.5 : 0.8, shape: 'linear' };
                trailTrace.marker = {
                    size: marker_sizes,
                    color: color,
                    opacity: marker_opacities,
                    symbol: 'circle',
                    line: { width: 0 }
                };
                trailTrace.hoverinfo = 'skip';
                trailTrace.opacity = is_highlighted ? 1.0 : 0.15;
                trailTrace.showlegend = false;
                trail_traces.push(trailTrace);
            }

            var glowName = ticker + ' Glow';
            var glowTrace = existingTraces[glowName] || {};
            glowTrace.x = [last_x];
            glowTrace.y = [last_y];
            glowTrace.mode = 'markers';
            glowTrace.name = glowName;
            glowTrace.visible = is_visible;
            glowTrace.marker = {
                size: is_highlighted ? 20 : 10,
                color: color,
                opacity: 0.3,
                symbol: 'circle',
                line: { width: 0 }
            };
            glowTrace.hoverinfo = 'skip';
            glowTrace.opacity = is_highlighted ? 1.0 : 0.15;
            glowTrace.showlegend = false;
            endpoint_traces.push(glowTrace);

            var epName = ticker;
            var epTrace = existingTraces[epName] || {};
            epTrace.x = [last_x];
            epTrace.y = [last_y];
            epTrace.mode = 'markers+text';
            epTrace.name = epName;
            epTrace.visible = is_visible;
            epTrace.marker = {
                size: is_highlighted ? 12 : 6,
                color: color,
                opacity: 1.0,
                symbol: 'circle',
                line: { color: '#ffffff', width: 1.5 }
            };
            epTrace.text = [ticker.replace('NIFTY ', '')];
            epTrace.textposition = textpos;
            epTrace.textfont = { size: 11, color: is_highlighted ? '#ffffff' : 'rgba(255,255,255,0.3)', weight: 'bold' };
            epTrace.hovertemplate = 
                '<b>' + ticker + '</b><br>' +
                '──────────────<br>' +
                'RS-Ratio:    %{x:.2f}<br>' +
                'RS-Momentum: %{y:.2f}<extra></extra>';
            epTrace.opacity = is_highlighted ? 1.0 : 0.15;
            epTrace.showlegend = false;
            endpoint_traces.push(epTrace);
        }

        // Basic collision avoidance for text labels
        var boxes = [];
        var label_w = 2.0; 
        var label_h = 1.0; 
        
        for (var i = 0; i < endpoint_traces.length; i++) {
            var tr = endpoint_traces[i];
            if (tr.mode === 'markers+text' && tr.visible) {
                var lx = tr.x[0];
                var ly = tr.y[0];
                var pos = tr.textposition;
                
                var getBox = function(x, y, p) {
                    var bx = x, by = y;
                    if (p.includes('right')) bx += 0.5;
                    else if (p.includes('left')) bx -= (label_w + 0.5);
                    else bx -= label_w/2;
                    
                    if (p.includes('top')) by += 0.5;
                    else if (p.includes('bottom')) by -= (label_h + 0.5);
                    else by -= label_h/2;
                    return {x: bx, y: by, w: label_w, h: label_h};
                };
                
                var hasOverlap = function(box) {
                    for(var b of boxes) {
                        if (!(box.x > b.x + b.w || box.x + box.w < b.x || box.y > b.y + b.h || box.y + box.h < b.y)) return true;
                    }
                    return false;
                };

                var curBox = getBox(lx, ly, pos);
                if (hasOverlap(curBox)) {
                    var alts = ['top right', 'bottom right', 'top left', 'bottom left', 'top center', 'bottom center'];
                    for (var alt of alts) {
                        var altBox = getBox(lx, ly, alt);
                        if (!hasOverlap(altBox)) {
                            tr.textposition = alt;
                            curBox = altBox;
                            break;
                        }
                    }
                }
                boxes.push(curBox);
            }
        }

        var new_traces = trail_traces.concat(endpoint_traces);

        if (!current_fig) {
            return no_update;
        }

        // Shallow clone layout to prevent deep copy overhead (Bug 4)
        var new_layout = { ...current_fig.layout };

        if (!window.uiState.animationStatus.userHasZoomed) {
            var max_dev = window.uiState.cachedAxisBounds || 6;
            new_layout.xaxis = { ...new_layout.xaxis, range: [100 - max_dev, 100 + max_dev], autorange: false };
            new_layout.yaxis = { ...new_layout.yaxis, range: [100 - max_dev, 100 + max_dev], autorange: false };
        }

        // Handle animation transition cleanly (Bug 1 & Bug 3)
        if (window.uiState.animationStatus.isPlaying && previousFrame !== currentFrame) {
            var speed = window.uiState.playbackSpeed || 500;
            var duration = speed * 0.9;
            
            new_layout.transition = {
                duration: duration,
                easing: 'linear'
            };
        } else {
            // Force stop any ongoing transition when paused or scrubbing
            new_layout.transition = {
                duration: 0,
                easing: 'linear'
            };
        }

        var new_fig = { data: new_traces, layout: new_layout };

        if (!window.uiState.animationStatus.relayoutListenerAttached) {
            setTimeout(function() {
                var graphDiv = document.getElementById('rrg-graph');
                if (graphDiv) {
                    graphDiv.on('plotly_relayout', function(eventData) {
                        if (eventData && (eventData['xaxis.range[0]'] !== undefined || eventData['xaxis.range'] !== undefined)) {
                            window.uiState.updateNested('animationStatus', 'userHasZoomed', true);
                        }
                        if (eventData && (eventData['xaxis.autorange'] === true || eventData['yaxis.autorange'] === true)) {
                            window.uiState.updateNested('animationStatus', 'userHasZoomed', false);
                        }
                    });
                    window.uiState.updateNested('animationStatus', 'relayoutListenerAttached', true);
                }
            }, 100);
        }

        if (store_data.dates && store_data.dates.length > currentFrame && store_data.dates[currentFrame]) {
            new_layout.title = {
                text: store_data.dates[currentFrame],
                font: { size: 14, color: '#8b949e' },
                x: 0.5
            };
        }

        return new_fig;
    }
};
