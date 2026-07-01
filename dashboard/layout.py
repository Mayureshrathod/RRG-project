"""
Dashboard layout structure.
"""

from dash import dcc, html, dash_table
from dashboard.styles import STYLE_CONTAINER, STYLE_CARD, STYLE_CONTROLS_ROW, STYLE_DROPDOWN
from config.engine import Timeframe
from config.indices import BENCHMARKS

def create_layout() -> html.Div:
    """Create the main dashboard layout."""
    
    # Header
    header = html.Div([
        html.H1("Relative Rotation Graph (RRG)", style={"marginBottom": "5px"}),
        html.P("JdK-inspired sector rotation analysis", style={"color": "#aaaaaa", "marginTop": "0"}),
    ])
    
    # Controls
    controls = html.Div([
        html.Div([
            html.Label("Benchmark", style={"display": "block", "marginBottom": "5px"}),
            dcc.Dropdown(
                id="benchmark-dropdown",
                options=[{"label": v, "value": k} for k, v in BENCHMARKS.items()],
                value="NIFTY 50",
                clearable=False,
                style=STYLE_DROPDOWN,
                className="dark-dropdown"
            )
        ]),
        html.Div([
            html.Label("Timeframe", style={"display": "block", "marginBottom": "5px"}),
            dcc.Dropdown(
                id="timeframe-dropdown",
                options=[{"label": t.value.capitalize(), "value": t.value} for t in Timeframe],
                value=Timeframe.WEEKLY.value,
                clearable=False,
                style=STYLE_DROPDOWN,
                className="dark-dropdown"
            )
        ]),
        html.Div([
            html.Label("Trail Length", style={"display": "block", "marginBottom": "5px"}),
            dcc.Slider(
                id="trail-slider",
                min=1,
                max=20,
                step=1,
                value=10,
                marks={1: '1', 5: '5', 10: '10', 15: '15', 20: '20'},
                tooltip={"placement": "bottom", "always_visible": False}
            )
        ], style={"flexGrow": "1", "minWidth": "200px", "marginLeft": "20px"}),
        html.Div([
            html.Label("Search/Highlight", style={"display": "block", "marginBottom": "5px"}),
            dcc.Input(
                id="search-input",
                type="text",
                placeholder="Filter sectors...",
                style={"backgroundColor": "#1e1e1e", "color": "#e0e0e0", "border": "1px solid #333", "padding": "8px", "borderRadius": "4px", "width": "150px"}
            )
        ])
    ], style=STYLE_CONTROLS_ROW)
    
    # Graph Area with Interactive Legend
    graph_area = html.Div([
        html.Div(id="quadrant-counts", className="quad-stat-container"),
        # Interactive Sector Legend
        html.Div([
            html.Div(id="sector-legend", className="sector-legend"),
            html.Button(
                "Show All",
                id="btn-show-all",
                n_clicks=0,
                className="btn-show-all",
            ),
            html.Button(
                "Hide All",
                id="btn-hide-all",
                n_clicks=0,
                className="btn-hide-all",
            ),
        ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center", "alignItems": "center", "gap": "6px", "padding": "8px 0", "borderBottom": "1px solid #21262d", "marginBottom": "8px"}),
        dcc.Loading(
            id="loading-graph",
            type="circle",
            style={"display": "flex", "flexGrow": "1", "flexDirection": "column", "height": "100%"},
            children=[
                dcc.Graph(
                    id="rrg-graph",
                    config={
                        "displayModeBar": "hover", 
                        "scrollZoom": True, 
                        "displaylogo": False,
                        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                        "toImageButtonOptions": {"format": "svg", "filename": "RRG_Export"}
                    },
                    style={"height": "100%", "minHeight": "400px"}
                )
            ]
        )
    ], className="dashboard-card", style={"flexGrow": "1", "display": "flex", "flexDirection": "column", "marginBottom": "0"})
    
    # Animation Controls
    anim_controls = html.Div([
        html.Div([
            html.Div(id="date-display", style={"fontWeight": "bold", "marginBottom": "5px"}),
            html.Div(id="frame-display", style={"color": "#aaaaaa", "fontSize": "12px"})
        ], style={"width": "120px", "textAlign": "center", "marginRight": "15px"}),
        
        html.Div([
            html.Button("⏮", id="btn-first", n_clicks=0, className="anim-btn"),
            html.Button("◀", id="btn-prev", n_clicks=0, className="anim-btn"),
            html.Button("▶ Play", id="btn-play", n_clicks=0, className="anim-btn play-btn"),
            html.Button("⏸ Pause", id="btn-pause", n_clicks=0, className="anim-btn pause-btn"),
            html.Button("▶", id="btn-next", n_clicks=0, className="anim-btn"),
            html.Button("⏭", id="btn-last", n_clicks=0, className="anim-btn"),
        ], style={"display": "flex", "gap": "5px", "marginRight": "20px"}),
        
        html.Div([
            html.Label("Speed", style={"fontSize": "12px", "display": "block", "marginBottom": "2px"}),
            dcc.Dropdown(
                id="speed-dropdown",
                options=[
                    {"label": "0.5x", "value": 1000},
                    {"label": "1x", "value": 500},
                    {"label": "2x", "value": 250},
                    {"label": "4x", "value": 125}
                ],
                value=500,
                clearable=False,
                style={"width": "70px", "color": "black"}
            )
        ], style={"marginRight": "20px"}),
        
        html.Div([
            dcc.Slider(
                id="timeline-slider",
                min=0,
                max=100,
                step=1,
                value=100,
                marks=None,
                tooltip={"placement": "bottom", "always_visible": False}
            )
        ], style={"flexGrow": "1", "paddingTop": "15px"})
    ], className="dashboard-card", style={**STYLE_CONTROLS_ROW, "alignItems": "center"})
    
    # Sector Table
    table_card = html.Div([
        html.H3("Sector Data", style={"marginTop": "0", "marginBottom": "16px"}),
        dash_table.DataTable(
            id="sector-table",
            columns=[
                {"name": "Sector", "id": "Sector"},
                {"name": "Quadrant", "id": "Quadrant"},
                {"name": "RS-Ratio", "id": "RS Ratio"},
                {"name": "RS-Momentum", "id": "RS Momentum"},
                {"name": "Trend", "id": "Trend"},
                {"name": "Rank", "id": "Rank"},
            ],
            data=[],
            style_table={"overflowX": "auto", "border": "none", "borderRadius": "8px"},
            style_header={
                "backgroundColor": "#161b22",
                "color": "#e6edf3",
                "fontWeight": "600",
                "border": "none",
                "borderBottom": "2px solid #30363d",
                "textAlign": "left",
                "padding": "12px 15px"
            },
            style_data={
                "backgroundColor": "#0d1117",
                "color": "#e6edf3",
                "border": "none",
                "borderBottom": "1px solid #21262d",
                "textAlign": "left",
                "padding": "10px 15px"
            },
            style_data_conditional=[
                {"if": {"state": "active"}, "backgroundColor": "rgba(88, 166, 255, 0.1)", "border": "none"},
                {"if": {"row_index": "odd"}, "backgroundColor": "#12161d"},
                {"if": {"column_id": "Quadrant", "filter_query": "{Quadrant} = leading"}, "color": "#22c55e", "fontWeight": "500"},
                {"if": {"column_id": "Quadrant", "filter_query": "{Quadrant} = weakening"}, "color": "#f97316", "fontWeight": "500"},
                {"if": {"column_id": "Quadrant", "filter_query": "{Quadrant} = lagging"}, "color": "#ef4444", "fontWeight": "500"},
                {"if": {"column_id": "Quadrant", "filter_query": "{Quadrant} = improving"}, "color": "#3b82f6", "fontWeight": "500"},
            ],
            sort_action="native",
            page_size=15
        )
    ], className="dashboard-card")
    
    # Data Stores for Client-Side Callbacks
    stores = html.Div([
        dcc.Store(id="store-rrg-data"),           # Holds full precomputed RRG results
        dcc.Store(id="store-sector-visibility"),  # Tracks sector visibility for legend
        dcc.Interval(id="anim-interval", interval=500, n_intervals=0, disabled=True) # 2 fps data ticks, Plotly handles smooth 60fps interpolation
    ])
    
    # Hidden div for keyboard events
    keyboard_div = html.Div(id="keyboard-listener", tabIndex=0, style={"outline": "none"})
    
    return html.Div([
        keyboard_div,
        header,
        html.Div([controls], className="dashboard-card"),
        graph_area,
        anim_controls,
        table_card,
        stores
    ], style={**STYLE_CONTAINER, "display": "flex", "flexDirection": "column", "height": "100vh", "padding": "24px", "gap": "16px"})
