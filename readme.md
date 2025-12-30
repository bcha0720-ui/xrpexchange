# XRP Exchange Holdings Dashboard

An interactive Streamlit dashboard for tracking XRP holdings across major cryptocurrency exchanges in real-time.

![Dashboard Preview](preview.png)

## Features

- **Real-time Data**: Fetches live balances directly from the XRP Ledger
- **Interactive Charts**: Bar charts, treemaps, and pie charts with Plotly
- **Market Analysis**: 
  - Total holdings overview
  - Market share distribution
  - Concentration analysis (Top 3, Top 10)
  - Cumulative market share visualization
- **Filtering**: Select specific exchanges to analyze
- **Wallet Details**: Drill down to individual wallet balances
- **Export Options**: Download data as CSV, JSON, or text report

## Installation

1. **Clone or download this directory**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard**:
   ```bash
   streamlit run app.py
   ```

4. **Open in browser**: Navigate to `http://localhost:8501`

## Usage

### Sidebar Controls

- **🔄 Refresh Data**: Clear cache and fetch fresh data from XRP Ledger
- **Filter Exchanges**: Select which exchanges to include in the analysis
- **Display Options**: 
  - Toggle wallet-level details
  - Choose chart type (Bar, Treemap, Pie)
  - Adjust number of top exchanges to highlight

### Main Dashboard

1. **Market Overview**: Key metrics showing total holdings and concentration
2. **Holdings Distribution**: Visual breakdown of XRP across exchanges
3. **Rankings Table**: Sortable table with all exchange data
4. **Market Share Analysis**: Detailed concentration analysis with cumulative view
5. **Wallet Details**: (Optional) Drill down into individual wallets per exchange
6. **Export**: Download data in various formats

## Configuration

To modify tracked exchanges, edit the `EXCHANGES` dictionary in `app.py`:

```python
EXCHANGES = {
    "Exchange Name": {
        "rWalletAddress1...": "Wallet Label 1",
        "rWalletAddress2...": "Wallet Label 2",
    },
    ...
}
```

## Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud (Free)
1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Deploy directly from your repository

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

### Heroku / Railway / Render
Add a `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

## Data Caching

- Balances are cached for 5 minutes (`@st.cache_data(ttl=300)`)
- Click "Refresh Data" to clear cache and fetch fresh data
- Caching helps reduce API load on the XRP Ledger

## Notes

- Data is fetched from Ripple's public server (`s1.ripple.com:51234`)
- SSL verification is disabled for compatibility
- This is for informational purposes only - always verify with official sources

## License

MIT License - Feel free to modify and use as needed.
