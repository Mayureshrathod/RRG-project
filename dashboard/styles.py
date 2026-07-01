"""
Dashboard UI styles and constants.
GitHub-inspired dark theme.
"""

from config.ui import QUADRANT_COLORS

# GitHub Dark theme colors
COLORS = {
    "background": "#0d1117",
    "paper": "#161b22",
    "text": "#e6edf3",
    "text_muted": "#8b949e",
    "grid": "#21262d",
    "border": "#30363d",
    "accent": "#58a6ff",
    "quadrants": QUADRANT_COLORS,
}

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

STYLE_CONTAINER = {
    "backgroundColor": COLORS["background"],
    "color": COLORS["text"],
    "fontFamily": FONT_FAMILY,
    "minHeight": "100vh",
    "margin": "0",
    "padding": "20px",
    "boxSizing": "border-box",
}

STYLE_CARD = {
    "backgroundColor": COLORS["paper"],
    "borderRadius": "8px",
    "padding": "20px",
    "border": f"1px solid {COLORS['border']}",
    "marginBottom": "20px",
}

STYLE_CONTROLS_ROW = {
    "display": "flex",
    "flexWrap": "wrap",
    "gap": "15px",
    "alignItems": "flex-end",
    "marginBottom": "10px",
}

STYLE_DROPDOWN = {
    "backgroundColor": COLORS["paper"],
    "color": COLORS["text"],
    "minWidth": "200px",
}
