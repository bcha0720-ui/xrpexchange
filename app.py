"""
XRP Exchange Holdings Dashboard
Interactive Streamlit dashboard for tracking XRP holdings across exchanges
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import urllib3
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import json

# Suppress urllib3 warnings
urllib3.disable_warnings()

# ============================================================================
# CONFIGURATION
# ============================================================================

RIPPLED_URL = "https://s1.ripple.com:51234"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10

# ============================================================================
# EXCHANGE DEFINITIONS
# ============================================================================

EXCHANGES = {
    "Robinhood": {
        "rEAKseZ7yNgaDuxH74PkqB12cVWohpi7R6": "Robinhood1",
        "r4ZuQtPNXGRMKfPjAsn2J7gRqoQuWnTPFP": "Robinhood2"
    },
    "Binance": {
        "rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh": "Binance 1",
        "rNU4eAowPuixS5ZCWaRL72UUeKgxcKExpK": "Binance 10",
        "rNxp4h8apvRis6mJf9Sh8C6iRxfrDWN7AV": "Binance 11",
        "rPJ5GFpyDLv7gqeB1uZVUBwDwi41kaXN5A": "Binance 12",
        "rPz2qA93PeRCyHyFCqyNggnyycJR1N4iNf": "Binance 13",
        "rhWj9gaovwu2hZxYW7p388P8GRbuXFLQkK": "Binance 14",
        "rarG6FaeYhnzSKSS5EEPofo4gFsPn2bZKk": "Binance 15",
        "rs8ZPbYqgecRcDzQpJYAMhSxSi5htsjnza": "Binance 5",
        "rDAE53VfMvftPB4ogpWGWvzkQxfht6JPxr": "Binance 6",
        "rfQ9EcLkU6WnNmkS3EwUkFeXeN47Rk8Cvi": "Binance 18",
        "rBtttd61FExHC68vsZ8dqmS3DfjFEceA1A": "Binance 9",
        "rLoqMgpjwGEQinYEM623za8c2nC2Uah8v7": "Binance 21",
        "rQUp2PKzH3vCtKs5H9tsPPE1rTsN6fhjqn": "Binance 22",
        "rEeEWeP88cpKUddKk37B2EZeiHBGiBXY3": "Binance US 1",
        "rMvYS27SYs5dXdFsUgpvv1CSrPsCz7ePF5": "Binance US 2",
        "r3ZVNKgkkT3A7hbEZ8HxnNnLDCCmZiZECV": "Binance US 3",
        "rPCpZwPKogNodbjRxGDnefVfatBiPwwQ": "Binance US 4",
        "rP3mUZyCDzZkTSd1VHoBbFt8HGm8fyq8qV": "Binance 17",
        "rDecw8UhrZZUiaWc91e571b3TL41MUioh7": "Binance 16",
        "rJpj1Mv21gJzsbsVnkp1U4nqchZbmZ9pM5": "Binance (XRP-BF2 Reserve)",
        "rfxbaKNt5SnMw5rPRRm4C53YK76MEnVXro": "Binance Charity2"
    },
    "Coinbase": {
        "rLNaPoKeeBjZe2qs6x52yVPZpZ8td4dc6w": "Coinbase1",
        "rw2ciyaNshpHe7bCHo4bRWq6pqqynnWKQg": "Coinbase2",
        "rUfghnh1VAWajpAmxgrzLPiCXJ7RwdJUgt": "Coinbase3",
        "rwpTh9DDa52XkM9nTKp2QrJuCGV5d1mQVP": "Coinbase4",
        "r3YsZdkznVzYBv141qhwXHDWoPUXLdksNw": "Coinbase5",
        "r4sRyacXpbh4HbagmgfoQq8Q3j8ZJzbZ1J": "Coinbase6",
        "rUjfTQpvBr6wsGGxMw6sRmRQGG76nvp8Ln": "Coinbase7",
        "rRmgo6NW1W7GHjC5qEpcpQnq8NE74ZS1P": "Coinbase10",
        "rHrHuQM3E114yMyPjeULWfQmbwVBrHsBEy": "Coinbase11",
        "rLBunuhuRY7aUCnDkSQhaf5ewCvdcWUYjR": "Coinbase12",
        "rDw1Z5BqJejpKCGfncHJ9rwRq2kYLo4sJG": "Coinbase13",
        "rwnYLUsoBQX3ECa1A5bSKLdbPoHKnqf63J": "Coinbase14",
        "rsTtGH7a9mom5X8Y9D3kxroXWvA912RgUZ": "Coinbase (Cold 176)",
    },
    "Upbit": {
        "raQwCVAJVqjrVm1Nj5SFRcX8i22BhdC9WA": "Upbit1",
        "rfL1mn4VTCoHdhHhHMwqpShCFUaDBRk6Z5": "Upbit12",
        "rwa7YXssGVAL9yPKw6QJtCen2UqZbRQqpM": "Upbit13",
        "rNcAdhSLXBrJ3aZUq22HaNtNEPpB5fR8Ri": "Upbit14",
        "r38a3PtqW3M7LRESgaR4dyHjg3AxAmiZCt": "Upbit15",
        "rMNUAfSz2spLEbaBwPnGtxTzZCajJifnzH": "Upbit16",
        "rJWbw1u3oDDRcYLFqiWFjhGWRKVcBAWdgp": "Upbit17",
        "rs48xReB6gjKtTnTfii93iwUhjhTJsW78B": "Upbit18",
        "rJo4m69u9Wd1F8fN2RbgAsJEF6a4hW1nSi": "Upbit19",
        "rLgn612WAgRoZ285YmsQ4t7kb8Ui3csdoU": "Upbit20",
        "r4G689g4KePYLKkyyumM1iUppTP4nhZwVC": "Upbit21",
        "rDxJNbV23mu9xsWoQHoBqZQvc77YcbJXwb": "Upbit22",
        "rHHQeqjz2QyNj1DVoAbcvfaKLv7RxpHMNE": "Upbit23"
    },
    "Kraken": {
        "rLHzPsX6oXkzU2qL12kHCH8G8cnZv1rBJh": "Kraken1",
        "rUeDDFNp2q7Ymvyv75hFGC8DAcygVyJbNF": "Kraken2",
        "rGZjPjMkfhAqmc1ssEiT753uAgyftHRo2m": "Kraken3",
        "rp7TCczQuQo61dUo1oAgwdpRxLrA8vDaNV": "Kraken4",
        "rEvuKRoEbZSbM5k5Qe5eTD9BixZXsfkxHf": "Kraken5",
        "rnJrjec2vrTJAAQUTMTjj7U6xdXrk9N4mT": "Kraken6",
        "rHapXGCL7KXTovvpEqLfDiZ6WV7vMhPWGJ": "Kraken7"
    },
    "Bitfinex": {
        "rLW9gnQo7BQhU6igk5keqYnH3TVrCxGRzm": "Bitfinex1",
        "rE3hWEGquaixF2XwirNbA1ds4m55LxNZPk": "Bitfinex2"
    },
    "Bitstamp": {
        "rDsbeomae4FXwgQTJp9Rs64Qg9vDiTCdBv": "Bitstamp1",
        "rUobSiUpYH2S97Mgb4E7b7HuzQj2uzZ3aD": "Bitstamp2",
        "rBMFF7vhe2pxYS5wo3dpXMDrbbRudB7hGf": "Bitstamp3",
        "rEXmdJZRfjXN3XGVdz99dGSZpQyJqUeirE": "Bitstamp"
    },
    "Bithumb": {
        "rPMM1dRp7taeRkbT74Smx2a25kTAHdr4N5": "Bithumb1",
        "rNTkgxs5WG5mU5Sz26YoDVrHim5Y5ohC7": "Bithumb2",
        "r9hUMZBc3MWRc4YdsdZgNCW5Qef8wNSXpb": "Bithumb3",
        "r9LHiNDZvpLoWPoKnbH2JWjFET8zoYT4Y5": "Bithumb4",
        "rD7XQw67JWBXuo2WPX2gZRsGKNsDUGTbx5": "Bithumb",
        "rZcBQae9iSJqFYBpNCfxGLXH7xuEzizxR": "Bithumb10",
        "rrsSUzrT2mYAMiL46pm7cwn6MmMmxVkEWM": "Bithumb11",
        "rPyCQm8E5j78PDbrfKF24fRC7qUAk1kDMZ": "Bithumb12",
        "rw3fRcmn5PJyPKuvtAwHDSpEqoW2JKmKbu": "Bithumb13"
    },
    "Crypto.com": {
        "r4DymtkgUAh2wqRxVfdd3Xtswzim6eC6c5": "Crypto.com 1",
        "rPHNKf25y3aqATYfrMv9LQnTRHQUYELXfn": "Crypto.com 2",
        "rJmXYcKCGJSayp4sAdp6Eo4CdSFtDVv7WG": "Crypto.com 3",
        "rKNwXQh9GMjaU8uTqKLECsqyib47g5dMvo": "Crypto.com 4",
        "rKV8HEL3vLc6q9waTiJcewdRdSFyx67QFb": "Crypto Exchange"
    },
    "Bybit": {
        "rMrgNBrkE6FdCjWih5VAWkGMrmerrWpiZt": "Bybit 1",
        "rNFKfGBzMspdKfaZdpnEyhkFyw7C1mtQ8x": "Bybit 2",
        "rJn2zAPdFA193sixJwuFixRkYDUtx3apQh": "Bybit 3",
        "rMvCasZ9cohYrSZRNYPTZfoaaSUQMfgQ8G": "Bybit 4",
        "rwBHqnCgNRnk3Kyoc6zon6Wt4Wujj3HNGe": "Bybit 5",
        "raQxZLtqurEXvH5sgijrif7yXMNwvFRkJN": "Bybit 6"
    },
    "Gate.io": {
        "rHcFoo6a9qT5NHiVn1THQRhsEGcxtYCV4d": "Gate.io 1",
        "rLzxZuZuAHM7k3FzfmhGkXVwScM4QSxoY7": "Gate.io 2",
        "rNnWmrc1EtNRe5SEQEs9pFibcjhpvAiVKF": "Gate.io 3",
        "rNu9U5sSouNoFunHp9e9trsLV6pvsSf54z": "Gate.io 4"
    },
    "Bitrue": {
        "rKq7xLeTaDFCg9cdy9MmgxpPWS8EZf2fNq": "Bitrue1",
        "raLPjTYeGezfdb6crXZzcC8RkLBEwbBHJ5": "Bitrue2",
        "rfKsmLP6sTfVGDvga6rW6XbmSFUzc3G9f3": "Bitrue3",
        "rNYW2bie6KwUSYhhtcnXWzRy5nLCa1UNCn": "Bitrue Insurance Fund",
        "r4DbbWjsZQ2hCcxmjncr7MRjpXTBPckGa9": "Bitrue Cold2"
    },
    "KuCoin": {
        "rLpvuHZFE46NUyZH5XaMvmYRJZF7aory7t": "Kucoin11",
        "rNFugeoj3ZN8Wv6xhuLegUBBPXKCyWLRkB": "Kucoin5",
        "rBxszqhQkhPALtkSpGuVeqR6hNtZ8xTH3T": "Kucoin7",
        "rp4gqz1XdqMsWRZbzPdPAQWw1tg5LuwUVP": "Kucoin8"
    },
    "OKX": {
        "rUzWJkXyEtT8ekSSxkBYPqCvHpngcy6Fks": "Okx"
    },
    "Gemini": {
        "raBQUYdAhnnojJQ6Xi3eXztZ74ot24RDq1": "Gemini1",
        "raq2gccLh11AwvBrpYcHntUTv4xQNRpyyG": "Gemini2",
        "rBYpyCjNwBDQFrgEdVfyosSgQS6iL6sTHe": "Gemini3"
    },
    "Uphold": {
        "rQrQMKhcw3WnptGeWiYSwX5Tz3otyJqPnq": "Uphold2",
        "rMdG3ju8pgyVh29ELPWaDuA74CpWW6Fxns": "Uphold3",
        "rBEc94rUFfLfTDwwGN7rQGBHc883c2QHhx": "Uphold4",
        "rsX8cp4aj9grKVD9V1K2ouUBXgYsjgUtBL": "Uphold8",
        "rErKXcbZj9BKEMih6eH6ExvBoHn9XLnTWe": "Uphold9",
        "rKe7pZPwdKEubmEDCAu9djJVsQfK4Atmzr": "Uphold11",
        "rsXT3AQqhHDusFs3nQQuwcA1yXRLZJAXKw": "uphold12"
    },
    "Bitget": {
        "rGDreBvnHrX1get7na3J4oowN19ny4GzFn": "Bitget Global"
    },
    "eToro": {
        "rsdvR9WZzKszBogBJrpLPE64WWyEW4ffzS": "eToro1",
        "raQ9yYPNDQwyeqAAX9xJgjjQ7wUtLxJ5JV": "eToro2",
        "rBMe3zVBLgeh2QN4CeX6B17zwbcN6JEmZB": "eToro3",
        "rEvwSpejhGTbdAXbxRTpGAzPBQkBRZxN5s": "eToro4",
        "rM9EyDmjxeukZGT6wfkxncqeM3ABJsro3a": "eToro5"
    },
    "MEXC": {
        "rs2dgzYeqYqsk8bvkQR5YPyqsXYcA24MP2": "Mexc"
    },
    "Bitbank": {
        "rLbKbPyuvs4wc1h13BEPHgbFGsRXMeFGL6": "Bitbank1",
        "rw7m3CtVHwGSdhFjV4MyJozmZJv3DYQnsA": "Bitbank2",
        "rwggnsfxvCmDb3YP9Hs1TaGvrPR7ngrn7Z": "Bitbank3",
        "r97KeayHuEsDwyU1yPBVtMLLoQr79QcRFe": "Bitbank4"
    },
    "Coinone": {
        "rp2diYfVtpbgEMyaoWnuaWgFCAkqCAEg28": "Coinone1",
        "rPsmHDMkheWZvbAkTA8A9bVnUdadPn7XBK": "Coinone2",
        "rhuCPEoLFYbpbwyhXioSumPKrnfCi3AXJZ": "Coinone3",
        "rMksM39efoP4XyAqEjzFUEowwnVbQTh6KW": "Coinone4",
        "rDKw32dPXHfoeGoD3kVtm76ia1WbxYtU7D": "Coinone5"
    },
    "Korbit": {
        "rBTjeJu1Rvnbq476Y7PDnvnXUeERV9CxEQ": "Korbit1",
        "rJRarS792K6LTqHsFkZGzM1Ue6G8jZ2AfK": "Korbit2",
        "rGU8q9qNCCQG2eMgJpLJJ1YFF5JAbntqau": "Korbit3",
        "r9WGxuEbUSh3ziYt34mBRViPbqVxZmwsu3": "Korbit4",
        "rNWWbLxbZRKd51NNZCEjoSNovrrx7yiPyt": "Korbit5",
        "rGq74nAmw1ARejUNLYEBGxiQBaoNtryEe9": "Korbit6",
        "rsYFhEk4uFvwvvKJomHL7KhdF29r2sw9KD": "Korbit7",
        "rwnXZEUe7o29SPcWZwnZukR8fdXmFMWHAN": "Korbit8"
    },
    "BitFlyer": {
        "rpY7bZBkA98P8zds5LdBktAKj9ifekPdkE": "BitFlyer 3",
        "rhWVCsCXrkwTeLBg6DyDr7abDaHz3zAKmn": "BitFlyer 4"
    },
    "Coincheck": {
        "rNQEMJA4PsoSrZRn9J6RajAYhcDzzhf8ok": "Coincheck 1",
        "rwgvfze315jjAAxT2TyyDqAPzL68HpAp6v": "Coincheck 2",
        "r99QSej32nAcjQAri65vE5ZXjw6xpUQ2Eh": "Coincheck 3"
    },
    "Bitpanda": {
        "rUEfYyerfok6Yo38tTTTZKeRefNh9iB1Bd": "Bitpanda1",
        "rhVWrjB9EGDeK4zuJ1x2KXSjjSpsDQSaU6": "Bitpanda2",
        "r3T75fuLjX51mmfb5Sk1kMNuhBgBPJsjza": "Bitpanda3",
        "rbrCJQZVk6jYra1MPuSvX3Vpe4to9fAvh": "Bitpanda4"
    },
    "SBI VC Trade": {
        "rNRc2S2GSefSkTkAiyjE6LDzMonpeHp6jS": "SBI VC TRADE 4",
        "raSZXZApFg7Nj1B5G6BnhoL6HcTqVMopJ3": "SBI VC Trade 5",
        "r39uEuRjzLaSgvkjTfcejodbSrXLM3cYnX": "SBI VC Trade 6",
        "rDDyH5nfvozKZQCwiBrWfcE528sWsBPWET": "SBI VC Trade 1",
        "rKcVYzVK1f4PhRFjLhWP7QmteG5FpPgRub": "SBI VC Trade 2",
        "rUaESVd1yLMy5VyoJvwwuqE8ZiCb2PEqBR": "SBI VC Trade 3"
    }
}

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_xrp_balance(address: str) -> float:
    """Fetch XRP balance from rippled server"""
    try:
        headers = {'Content-Type': 'application/json'}
        data = {
            "method": "account_info",
            "params": [{"account": address, "ledger_index": "validated", "strict": True}]
        }
        
        for i in range(MAX_RETRIES):
            try:
                response = requests.post(RIPPLED_URL, json=data, headers=headers, 
                                       timeout=REQUEST_TIMEOUT, verify=False)
                response.raise_for_status()
                result = response.json()
                
                if "result" in result and "account_data" in result["result"]:
                    return float(result["result"]["account_data"]["Balance"]) / 1e6
                
                if result.get("result", {}).get("error") == "actNotFound":
                    return 0.0
                break
                
            except requests.exceptions.RequestException as e:
                if i < MAX_RETRIES - 1:
                    time.sleep(2 ** i)
                else:
                    raise
        return 0.0
        
    except Exception as e:
        return 0.0


def fetch_all_balances(progress_callback=None) -> Dict[str, Dict]:
    """Fetch balances for all exchanges"""
    results = {}
    total_exchanges = len(EXCHANGES)
    
    for idx, (exchange, wallets) in enumerate(EXCHANGES.items()):
        exchange_total = 0.0
        wallet_details = []
        
        for address, name in wallets.items():
            balance = get_xrp_balance(address)
            exchange_total += balance
            wallet_details.append({
                "address": address,
                "name": name,
                "balance": balance
            })
        
        results[exchange] = {
            "total": exchange_total,
            "wallets": wallet_details,
            "wallet_count": len(wallets)
        }
        
        if progress_callback:
            progress_callback((idx + 1) / total_exchanges)
    
    return results


def create_summary_dataframe(data: Dict[str, Dict]) -> pd.DataFrame:
    """Create summary DataFrame from exchange data"""
    rows = []
    total_balance = sum(d["total"] for d in data.values())
    
    for exchange, details in data.items():
        market_share = (details["total"] / total_balance * 100) if total_balance > 0 else 0
        rows.append({
            "Exchange": exchange,
            "Balance (XRP)": details["total"],
            "Market Share (%)": market_share,
            "Wallet Count": details["wallet_count"]
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values("Balance (XRP)", ascending=False).reset_index(drop=True)
    df.index = df.index + 1  # Start ranking from 1
    df.index.name = "Rank"
    return df


# ============================================================================
# STREAMLIT APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="XRP Exchange Holdings Tracker",
        page_icon="💎",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS - works with both light and dark themes
    st.markdown("""
        <style>
        /* Metric cards styling */
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        [data-testid="stMetric"] label {
            color: #555 !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #1f77b4 !important;
            font-size: 1.8rem !important;
        }
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            [data-testid="stMetric"] {
                background-color: #262730;
                border: 1px solid #3d3d3d;
            }
            [data-testid="stMetric"] label {
                color: #fafafa !important;
            }
            [data-testid="stMetric"] [data-testid="stMetricValue"] {
                color: #00d4ff !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("💎 XRP Exchange Holdings Tracker")
    st.markdown("Real-time tracking of XRP holdings across major cryptocurrency exchanges")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Controls")
        
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Exchange filter
        st.subheader("📊 Filter Exchanges")
        all_exchanges = list(EXCHANGES.keys())
        selected_exchanges = st.multiselect(
            "Select exchanges to display",
            options=all_exchanges,
            default=all_exchanges,
            help="Choose which exchanges to include in the analysis"
        )
        
        st.markdown("---")
        
        # Display options
        st.subheader("⚙️ Display Options")
        show_wallet_details = st.checkbox("Show wallet-level details", value=False)
        chart_type = st.selectbox(
            "Chart Type",
            ["Bar Chart", "Treemap", "Pie Chart"],
            index=0
        )
        
        top_n = st.slider("Top N exchanges to highlight", 5, 20, 10)
        
        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"Data source: {RIPPLED_URL}")
    
    # Main content
    if not selected_exchanges:
        st.warning("Please select at least one exchange from the sidebar.")
        return
    
    # Fetch data with progress bar
    with st.spinner("Fetching live data from XRP Ledger..."):
        progress_bar = st.progress(0)
        data = fetch_all_balances(progress_callback=lambda p: progress_bar.progress(p))
        progress_bar.empty()
    
    # Filter data based on selection
    filtered_data = {k: v for k, v in data.items() if k in selected_exchanges}
    
    # Create summary DataFrame
    df = create_summary_dataframe(filtered_data)
    
    # Key Metrics Row
    st.markdown("### 📈 Market Overview")
    
    total_xrp = df["Balance (XRP)"].sum()
    top3_share = df.head(3)["Market Share (%)"].sum()
    top10_share = df.head(10)["Market Share (%)"].sum()
    exchange_count = len(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total XRP Holdings",
            value=f"{total_xrp:,.0f}",
            help="Total XRP held across all selected exchanges"
        )
    
    with col2:
        st.metric(
            label="Exchanges Tracked",
            value=f"{exchange_count}",
            help="Number of exchanges being monitored"
        )
    
    with col3:
        st.metric(
            label="Top 3 Concentration",
            value=f"{top3_share:.1f}%",
            help="Percentage of total holdings by top 3 exchanges"
        )
    
    with col4:
        st.metric(
            label="Top 10 Concentration",
            value=f"{top10_share:.1f}%",
            help="Percentage of total holdings by top 10 exchanges"
        )
    
    st.markdown("---")
    
    # Charts Row
    col_chart, col_table = st.columns([1.2, 1])
    
    with col_chart:
        st.markdown(f"### 📊 Holdings Distribution (Top {top_n})")
        
        chart_df = df.head(top_n).copy()
        
        if chart_type == "Bar Chart":
            fig = px.bar(
                chart_df,
                x="Exchange",
                y="Balance (XRP)",
                color="Market Share (%)",
                color_continuous_scale="Blues",
                text=chart_df["Balance (XRP)"].apply(lambda x: f"{x/1e6:.1f}M"),
                hover_data=["Market Share (%)", "Wallet Count"]
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                xaxis_tickangle=-45,
                height=500,
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            
        elif chart_type == "Treemap":
            fig = px.treemap(
                chart_df,
                path=["Exchange"],
                values="Balance (XRP)",
                color="Balance (XRP)",
                color_continuous_scale="Blues",
                hover_data=["Market Share (%)", "Wallet Count"]
            )
            fig.update_layout(height=500)
            
        else:  # Pie Chart
            fig = px.pie(
                chart_df,
                names="Exchange",
                values="Balance (XRP)",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col_table:
        st.markdown("### 🏆 Rankings")
        
        # Format the display DataFrame
        display_df = df.copy()
        display_df["Balance (XRP)"] = display_df["Balance (XRP)"].apply(lambda x: f"{x:,.0f}")
        display_df["Market Share (%)"] = display_df["Market Share (%)"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=450
        )
    
    st.markdown("---")
    
    # Market Share Visualization
    st.markdown("### 🥧 Market Share Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Horizontal bar for market share
        fig_share = px.bar(
            df.head(15),
            y="Exchange",
            x="Market Share (%)",
            orientation="h",
            color="Market Share (%)",
            color_continuous_scale="Viridis",
            text=df.head(15)["Market Share (%)"].apply(lambda x: f"{x:.1f}%")
        )
        fig_share.update_traces(textposition="outside")
        fig_share.update_layout(
            height=500,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            title="Market Share by Exchange"
        )
        st.plotly_chart(fig_share, use_container_width=True)
    
    with col2:
        # Cumulative distribution
        cumulative_df = df.copy()
        cumulative_df["Cumulative Share (%)"] = cumulative_df["Market Share (%)"].cumsum()
        
        fig_cumulative = go.Figure()
        fig_cumulative.add_trace(go.Scatter(
            x=list(range(1, len(cumulative_df) + 1)),
            y=cumulative_df["Cumulative Share (%)"],
            mode='lines+markers',
            name='Cumulative Share',
            line=dict(color='#00d4ff', width=3),
            marker=dict(size=8)
        ))
        fig_cumulative.add_hline(y=50, line_dash="dash", line_color="orange", 
                                  annotation_text="50% threshold")
        fig_cumulative.add_hline(y=80, line_dash="dash", line_color="red",
                                  annotation_text="80% threshold")
        fig_cumulative.update_layout(
            title="Cumulative Market Concentration",
            xaxis_title="Number of Exchanges",
            yaxis_title="Cumulative Market Share (%)",
            height=500
        )
        st.plotly_chart(fig_cumulative, use_container_width=True)
    
    # Wallet-level details (expandable)
    if show_wallet_details:
        st.markdown("---")
        st.markdown("### 🔍 Wallet-Level Details")
        
        selected_exchange = st.selectbox(
            "Select an exchange to view wallet details",
            options=selected_exchanges
        )
        
        if selected_exchange and selected_exchange in filtered_data:
            wallet_data = filtered_data[selected_exchange]["wallets"]
            wallet_df = pd.DataFrame(wallet_data)
            wallet_df = wallet_df.sort_values("balance", ascending=False).reset_index(drop=True)
            wallet_df.index = wallet_df.index + 1
            wallet_df.columns = ["Address", "Wallet Name", "Balance (XRP)"]
            wallet_df["Balance (XRP)"] = wallet_df["Balance (XRP)"].apply(lambda x: f"{x:,.0f}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(wallet_df, use_container_width=True)
            
            with col2:
                # Mini pie chart for wallet distribution
                raw_wallet_df = pd.DataFrame(wallet_data)
                if len(raw_wallet_df) > 1 and raw_wallet_df["balance"].sum() > 0:
                    fig_wallet = px.pie(
                        raw_wallet_df,
                        names="name",
                        values="balance",
                        title=f"{selected_exchange} Wallet Distribution"
                    )
                    fig_wallet.update_layout(height=300, showlegend=True)
                    st.plotly_chart(fig_wallet, use_container_width=True)
    
    # Export functionality
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv()
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name=f"xrp_holdings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        json_data = json.dumps(filtered_data, indent=2, default=str)
        st.download_button(
            label="📋 Download JSON",
            data=json_data,
            file_name=f"xrp_holdings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        # Summary report
        report = f"""XRP Exchange Holdings Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

MARKET OVERVIEW
- Total XRP Holdings: {total_xrp:,.0f} XRP
- Exchanges Tracked: {exchange_count}
- Top 3 Concentration: {top3_share:.2f}%
- Top 10 Concentration: {top10_share:.2f}%

TOP 10 EXCHANGES
{'='*50}
"""
        for idx, row in df.head(10).iterrows():
            report += f"{idx}. {row['Exchange']}: {float(row['Balance (XRP)'].replace(',', '') if isinstance(row['Balance (XRP)'], str) else row['Balance (XRP)']):,.0f} XRP ({row['Market Share (%)']})\n"
        
        st.download_button(
            label="📝 Download Report",
            data=report,
            file_name=f"xrp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Footer
    st.markdown("---")
    st.caption("💡 Data is fetched live from the XRP Ledger. Balances are cached for 5 minutes to improve performance.")
    st.caption("⚠️ This dashboard is for informational purposes only. Always verify data from official sources.")


if __name__ == "__main__":
    main()
