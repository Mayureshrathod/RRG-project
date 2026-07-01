"""
Animation and visualization logic for the dashboard.
Implements the base Plotly figure and client-side callbacks for smooth animation.
"""

from dash import ClientsideFunction, Input, Output, State
import plotly.graph_objects as go

from config.ui import QUADRANT_COLORS, QUADRANT_BG_OPACITY


def create_base_figure() -> go.Figure:
    """Create the base RRG Plotly figure with quadrants and layout."""
    fig = go.Figure()

    # Quadrant background shapes
    fig.add_shape(type="rect", x0=100, y0=100, x1=120, y1=120,
                  fillcolor=QUADRANT_COLORS["Leading"], opacity=QUADRANT_BG_OPACITY,
                  layer="below", line_width=0)
    fig.add_shape(type="rect", x0=100, y0=80, x1=120, y1=100,
                  fillcolor=QUADRANT_COLORS["Weakening"], opacity=QUADRANT_BG_OPACITY,
                  layer="below", line_width=0)
    fig.add_shape(type="rect", x0=80, y0=80, x1=100, y1=100,
                  fillcolor=QUADRANT_COLORS["Lagging"], opacity=QUADRANT_BG_OPACITY,
                  layer="below", line_width=0)
    fig.add_shape(type="rect", x0=80, y0=100, x1=100, y1=120,
                  fillcolor=QUADRANT_COLORS["Improving"], opacity=QUADRANT_BG_OPACITY,
                  layer="below", line_width=0)

    # Watermark annotations
    watermark_font = dict(color="rgba(255, 255, 255, 0.04)", size=42, family="Inter, -apple-system, sans-serif")
    fig.add_annotation(x=103, y=103, text="<b>LEADING</b>", showarrow=False, font=watermark_font, align="center")
    fig.add_annotation(x=103, y=97, text="<b>WEAKENING</b>", showarrow=False, font=watermark_font, align="center")
    fig.add_annotation(x=97, y=97, text="<b>LAGGING</b>", showarrow=False, font=watermark_font, align="center")
    fig.add_annotation(x=97, y=103, text="<b>IMPROVING</b>", showarrow=False, font=watermark_font, align="center")

    # Center axes (Quadrant lines)
    fig.add_hline(y=100, line_width=2, line_color="rgba(255, 255, 255, 0.3)", line_dash="dash")
    fig.add_vline(x=100, line_width=2, line_color="rgba(255, 255, 255, 0.3)", line_dash="dash")

    # Layout
    fig.update_layout(
        title="",
        xaxis=dict(
            title=dict(text="RS-Ratio", font=dict(size=13, color="#8b949e", family="Inter, sans-serif")),
            range=[94, 106],
            zeroline=False,
            gridcolor="#21262d",
            minor=dict(showgrid=True, gridcolor="rgba(33, 38, 45, 0.5)"),
            color="#e6edf3",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=True,
            spikecolor="#8b949e",
            spikethickness=1,
            spikedash="dot",
        ),
        yaxis=dict(
            title=dict(text="RS-Momentum", font=dict(size=13, color="#8b949e", family="Inter, sans-serif")),
            range=[94, 106],
            zeroline=False,
            gridcolor="#21262d",
            minor=dict(showgrid=True, gridcolor="rgba(33, 38, 45, 0.5)"),
            color="#e6edf3",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=True,
            spikecolor="#8b949e",
            spikethickness=1,
            spikedash="dot",
            scaleanchor="x",
            scaleratio=1,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6edf3", family="Inter, -apple-system, sans-serif"),
        margin=dict(l=60, r=40, t=50, b=60),
        showlegend=False,
        hovermode="closest",
        uirevision="constant",
    )

    return fig


def register_clientside_callbacks():
    """Register JavaScript callbacks for client-side animation."""
    from dash import clientside_callback

    # Main frame rendering: reads store data + slider position, updates graph + table + counts + date/frame
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="update_rrg_frame"
        ),
        [Output("rrg-graph", "figure"),
         Output("sector-table", "data"),
         Output("quadrant-counts", "children"),
         Output("date-display", "children"),
         Output("frame-display", "children")],
        [Input("timeline-slider", "value"),
         Input("trail-slider", "value"),
         Input("search-input", "value"),
         Input("store-sector-visibility", "data")],
        [State("store-rrg-data", "data"),
         State("rrg-graph", "figure")],
        prevent_initial_call=True
    )

    # Play/Pause toggle
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="toggle_animation"
        ),
        [Output("anim-interval", "disabled"),
         Output("btn-play", "style"),
         Output("btn-pause", "style")],
        [Input("btn-play", "n_clicks"),
         Input("btn-pause", "n_clicks")],
        [State("anim-interval", "disabled")],
        prevent_initial_call=True
    )

    # Auto-advance slider on interval tick
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="advance_frame"
        ),
        Output("timeline-slider", "value", allow_duplicate=True),
        Input("anim-interval", "n_intervals"),
        [State("timeline-slider", "value"),
         State("timeline-slider", "max")],
        prevent_initial_call=True
    )

    # Navigation controls (First, Prev, Next, Last)
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="navigate_timeline"
        ),
        Output("timeline-slider", "value", allow_duplicate=True),
        [Input("btn-first", "n_clicks"),
         Input("btn-prev", "n_clicks"),
         Input("btn-next", "n_clicks"),
         Input("btn-last", "n_clicks")],
        [State("timeline-slider", "value"),
         State("timeline-slider", "max")],
        prevent_initial_call=True
    )

    # Speed control
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="update_speed"
        ),
        Output("anim-interval", "interval"),
        Input("speed-dropdown", "value"),
        prevent_initial_call=True
    )

    # Render interactive legend
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="render_legend"
        ),
        Output("sector-legend", "children"),
        Input("store-rrg-data", "data"),
        prevent_initial_call=False
    )

    # Reset visibility (Show All / Hide All)
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="handle_show_hide_all"
        ),
        Output("store-sector-visibility", "data"),
        [Input("btn-show-all", "n_clicks"),
         Input("btn-hide-all", "n_clicks")],
        prevent_initial_call=True
    )

    # Keyboard shortcuts (space for play/pause)
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="setup_keyboard"
        ),
        Output("keyboard-listener", "tabIndex"),
        Input("keyboard-listener", "id")
    )
