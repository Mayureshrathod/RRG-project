/**
 * RRG Dashboard — Client-side animation and rendering.
 *
 * All rendering runs in the browser. No Python callback fires during playback.
 * Now relies on window.uiState (00_state.js) for centralized state management.
 */

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {

        /**
         * Main frame renderer.
         * Reads the timeline slider position, slices trail data, builds traces.
         */
        update_rrg_frame: function(timeline_idx, trail_length, search_term, visibility_data, store_data, current_fig) {
            var no_update = window.dash_clientside.no_update;
            
            // 1. Sync state (Animation Engine simply updates uiState)
            var updates = {
                currentFrame: timeline_idx,
                trailLength: trail_length,
                searchFilter: search_term || ''
            };
            
            if (visibility_data) {
                updates.visibleSectors = visibility_data;
            }
            
            window.uiState.update(updates);

            if (!store_data || !store_data.sectors) {
                return [no_update, no_update, no_update, no_update, no_update];
            }

            // 2. Delegate Graph Rendering
            var new_fig = window.rrgGraph ? window.rrgGraph.render(store_data, current_fig) : no_update;

            // 3. Delegate Table and Quadrant Rendering (Phase 5)
            var table_result = window.rrgTable ? window.rrgTable.render(store_data) : { table_data: [], counts_div: [] };
            var table_data = table_result.table_data;
            var counts_div = table_result.counts_div;

            // 4. Return Frame and Date
            var date_str = (store_data.dates && store_data.dates[timeline_idx]) ? store_data.dates[timeline_idx] : "";
            var total_frames = store_data.dates ? store_data.dates.length - 1 : 100;
            var frame_str = timeline_idx + " / " + total_frames;

            return [new_fig, table_data, counts_div, date_str, frame_str];
        },

        toggle_animation: function(play_clicks, pause_clicks, is_disabled) {
            var base_style = { padding: '8px 16px', cursor: 'pointer', border: '1px solid #30363d', borderRadius: '6px', fontSize: '14px' };

            var play_default = Object.assign({}, base_style, { marginRight: '10px', backgroundColor: '#161b22', color: '#e6edf3' });
            var pause_default = Object.assign({}, base_style, { marginRight: '20px', backgroundColor: '#161b22', color: '#e6edf3' });
            var active_style = { backgroundColor: '#0ea882', color: '#ffffff', border: '1px solid #0ea882' };

            var prev_play = window.uiState.animationStatus.playClicks || 0;
            var prev_pause = window.uiState.animationStatus.pauseClicks || 0;
            var curr_play = play_clicks || 0;
            var curr_pause = pause_clicks || 0;

            var play_clicked = curr_play > prev_play;
            var pause_clicked = curr_pause > prev_pause;

            window.uiState.updateNested('animationStatus', 'playClicks', curr_play);
            window.uiState.updateNested('animationStatus', 'pauseClicks', curr_pause);

            if (play_clicked) {
                window.uiState.updateNested('animationStatus', 'userHasZoomed', false);
                window.uiState.updateNested('animationStatus', 'isPlaying', true);
                document.body.classList.add('is-playing');
                var play_style = Object.assign({}, play_default, active_style);
                return [false, play_style, pause_default];
            } else if (pause_clicked) {
                window.uiState.updateNested('animationStatus', 'isPlaying', false);
                document.body.classList.remove('is-playing');
                var pause_style = Object.assign({}, pause_default, active_style);
                return [true, play_default, pause_style];
            }

            if (is_disabled) {
                return [true, play_default, pause_default];
            } else {
                var play_active = Object.assign({}, play_default, active_style);
                return [false, play_active, pause_default];
            }
        },

        advance_frame: function(n_intervals, current_val, max_val) {
            if (!window.uiState.animationStatus.isPlaying) {
                return window.dash_clientside.no_update;
            }
            if (current_val === undefined || current_val === null || max_val === undefined || max_val === null) {
                return window.dash_clientside.no_update;
            }
            if (current_val >= max_val) {
                // Auto-pause at end
                var pause_btn = document.getElementById('btn-pause');
                if (pause_btn) pause_btn.click();
                return current_val;
            }
            return current_val + 1;
        },

        setup_keyboard: function(dummy_id) {
            if (window.uiState.animationStatus.keyboardSetup) return 0;

            document.addEventListener('keydown', function(e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

                if (e.code === 'Space') {
                    e.preventDefault();
                    var play_btn = document.getElementById('btn-play');
                    var pause_btn = document.getElementById('btn-pause');

                    if (play_btn && pause_btn) {
                        if (window.uiState.animationStatus.isPlaying) {
                            pause_btn.click();
                        } else {
                            play_btn.click();
                        }
                    }
                } else if (e.code === 'ArrowLeft') {
                    e.preventDefault();
                    var prev_btn = document.getElementById('btn-prev');
                    if (prev_btn) prev_btn.click();
                } else if (e.code === 'ArrowRight') {
                    e.preventDefault();
                    var next_btn = document.getElementById('btn-next');
                    if (next_btn) next_btn.click();
                }
            });

            window.uiState.updateNested('animationStatus', 'keyboardSetup', true);
            return 0;
        },

        render_legend: function(store_data) {
            if (window.rrgLegend) {
                return window.rrgLegend.render(store_data);
            }
            return window.dash_clientside.no_update;
        },

        navigate_timeline: function(first_clicks, prev_clicks, next_clicks, last_clicks, current_val, max_val) {
            var ctx = window.dash_clientside.callback_context;
            if (!ctx.triggered || ctx.triggered.length === 0) {
                return window.dash_clientside.no_update;
            }
            
            var triggered_id = ctx.triggered[0].prop_id.split('.')[0];
            var new_val = current_val;
            
            if (triggered_id === "btn-first") {
                new_val = 0;
            } else if (triggered_id === "btn-prev") {
                new_val = Math.max(0, current_val - 1);
            } else if (triggered_id === "btn-next") {
                new_val = Math.min(max_val, current_val + 1);
            } else if (triggered_id === "btn-last") {
                new_val = max_val;
            }
            
            return new_val;
        },

        update_speed: function(speed_val) {
            if (!speed_val) return window.dash_clientside.no_update;
            window.uiState.update('playbackSpeed', speed_val);
            return speed_val;
        },

        handle_show_hide_all: function(show_clicks, hide_clicks) {
            var ctx = window.dash_clientside.callback_context;
            if (!ctx.triggered || ctx.triggered.length === 0) {
                return window.dash_clientside.no_update;
            }
            var triggered_id = ctx.triggered[0].prop_id.split('.')[0];
            
            if (window.rrgLegend) {
                if (triggered_id === 'btn-show-all') return window.rrgLegend.showAll();
                if (triggered_id === 'btn-hide-all') return window.rrgLegend.hideAll();
            }
            return window.dash_clientside.no_update;
        }
    }
});
