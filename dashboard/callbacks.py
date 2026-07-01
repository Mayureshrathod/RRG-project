"""
Server-side callbacks for the dashboard.
Delegates all data and computational logic to the RRGService.
"""

from dash import Input, Output, callback, dcc
import dash
from services.rrg_service import RRGService
from utils.logger import get_logger

logger = get_logger(__name__)


def register_server_callbacks(rrg_service: RRGService):
    """Register Python callbacks for data updates."""

    @callback(
        [Output("store-rrg-data", "data"),
         Output("timeline-slider", "max"),
         Output("timeline-slider", "value")],
        [Input("benchmark-dropdown", "value"),
         Input("timeframe-dropdown", "value")],
        prevent_initial_call=False
    )
    def update_rrg_data(benchmark_ticker: str, timeframe_val: str):
        """Fetch data from service layer and populate the client-side store."""
        logger.info(
            f"Dashboard callback: benchmark={benchmark_ticker}, timeframe={timeframe_val}"
        )

        data_dict, max_idx = rrg_service.get_frame_store(
            benchmark_ticker, timeframe_val
        )

        if not data_dict:
            logger.error("No data returned from RRG Service")
            return dash.no_update, dash.no_update, dash.no_update

        return data_dict, max_idx, max_idx
