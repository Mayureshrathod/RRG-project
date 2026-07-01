# RRG Dashboard

A professional Relative Rotation Graph (RRG) Dashboard for Indian stock market sector analysis. 

This application visualizes sector rotation against selected benchmarks (like NIFTY 50) using the Julius de Kempenaer methodology (RS-Ratio and RS-Momentum). It features local caching, multiple timeframes (Daily, Weekly, Monthly), and animated playback.

## Features
- **Accurate RRG Calculations**: Authentic RS-Ratio and RS-Momentum calculations.
- **Multiple Timeframes**: Analyze on Daily, Weekly, and Monthly charts.
- **Fast Local Caching**: Uses Parquet files to cache fetched market data and avoid rate limits.
- **Yahoo Finance Provider**: Automatically maps and fetches index data from Yahoo Finance.

## Installation

1. Clone or download this project.
2. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Start the dashboard server by running:
```bash
python main.py
```

The application will validate the index symbols on startup (this may take ~15 seconds on the very first run). Once the terminal says `Server started at http://127.0.0.1:8050`, open that URL in your web browser.

## Running Tests

To verify the mathematical engine and project setup, run the test suite:
```bash
pytest tests/
```
