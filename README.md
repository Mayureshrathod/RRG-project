# RRG Dashboard

A professional Relative Rotation Graph (RRG) Dashboard for Indian stock market sector analysis. 

This application visualizes sector rotation against selected benchmarks (like NIFTY 50) using the Julius de Kempenaer methodology (RS-Ratio and RS-Momentum). It features local caching, multiple timeframes (Daily, Weekly, Monthly), and animated playback.

## Features
- **Accurate RRG Calculations**: Authentic RS-Ratio and RS-Momentum calculations.
- **Multiple Timeframes**: Analyze on Daily, Weekly, and Monthly charts.
- **Fast Local Caching**: Uses Parquet files to cache fetched market data and avoid rate limits.
- **Yahoo Finance Provider**: Automatically maps and fetches index data from Yahoo Finance.

---

## 🚀 How to Run (For Team Members)

If a team member has shared this repository with you, follow these steps to run the dashboard on your own computer:

### Prerequisites
- Python 3.9 or higher installed.

### 1. Download the Project
Clone this repository using Git, or download the ZIP file and extract it.
```bash
git clone <URL_TO_YOUR_GITHUB_REPO>
cd "RRG project"
```

### 2. Set up a Virtual Environment (Recommended)
This keeps the project's dependencies separate from your main Python installation.
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries, including Pandas, Dash, and PyArrow.
```bash
pip install -r requirements.txt
```

### 4. Run the Dashboard
Start the local server:
```bash
python run_dashboard.py
```

The application will validate the index symbols on startup (this may take ~15 seconds on the very first run as it fetches data). 

Once it's ready, open your web browser and go to:
**http://127.0.0.1:8050**

---

## 🌐 Sharing on the Local Network (Wi-Fi)

The server is configured to run on `0.0.0.0`, which means it listens on all network interfaces. 
If you run `python run_dashboard.py` on your computer, anyone connected to the same Wi-Fi network can view the dashboard by entering your computer's local IP address into their browser.

For example, if your IP address is `192.168.1.5`, your team can open:
`http://192.168.1.5:8050`

---

## Running Tests

To verify the mathematical engine and project setup, run the test suite:
```bash
pytest tests/
```
