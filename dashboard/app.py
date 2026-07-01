"""
Main Dash application initialization.
"""

import os
import dash
from dashboard.layout import create_layout
from dashboard.animation import register_clientside_callbacks, create_base_figure
from dashboard.callbacks import register_server_callbacks

def create_app(rrg_service) -> dash.Dash:
    """Initialize and configure the Dash application."""
    
    # Initialize Dash
    app = dash.Dash(
        __name__,
        title="RRG Dashboard",
        update_title=None, # Disable "Updating..." in title
        suppress_callback_exceptions=True,
        assets_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    )
    
    # Set layout
    app.layout = create_layout()
    
    # Find the Graph component and inject base figure
    def inject_figure(layout):
        children = getattr(layout, 'children', [])
        if children is None:
            children = []
        elif not isinstance(children, list):
            children = [children]
            
        for child in children:
            if hasattr(child, 'id') and child.id == "rrg-graph":
                child.figure = create_base_figure()
                return True
            if hasattr(child, 'children'):
                if inject_figure(child):
                    return True
        return False
        
    inject_figure(app.layout)
    
    # Register callbacks
    register_server_callbacks(rrg_service)
    register_clientside_callbacks()
    
    return app
