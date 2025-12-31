"""
XRP Exchange Holdings Dashboard
Interactive Streamlit dashboard for tracking XRP holdings across exchanges
With historical comparison to February 24, 2025 benchmark
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

# ============================================================================
# VISITOR TRACKING
# ============================================================================

def get_visitor_count():
    """Get and increment visitor count using a simple file-based counter"""
    count_file = "visitor_count.txt"
    try:
        # Try to read existing count
        with open(count_file, "r") as f:
            count = int(f.read().strip())
    except:
        count = 0
    
    # Increment for new session
    if 'counted' not in st.session_state:
        st.session_state.counted = True
        count += 1
        try:
            with open(count_file, "w") as f:
                f.write(str(count))
        except:
            pass
    
    return count

# Suppress urllib3 warnings
urllib3.disable_warnings()

# ============================================================================
# CONFIGURATION
# ============================================================================

RIPPLED_URL = "https://s1.ripple.com:51234"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10

# ============================================================================
# HISTORICAL DATA - February 24, 2025 Benchmark
# ============================================================================

HISTORICAL_BALANCES_20250224 = {
    # Upbit
    "r38a3PtqW3M7LRESgaR4dyHjg3AxAmiZCt": 500000022.920354,  # Upbit15
    "r4G689g4KePYLKkyyumM1iUppTP4nhZwVC": 500000023.954709,  # Upbit21
    "rDxJNbV23mu9xsWoQHoBqZQvc77YcbJXwb": 980472688.335846,  # Upbit22
    "rHHQeqjz2QyNj1DVoAbcvfaKLv7RxpHMNE": 427.863089,  # Upbit23
    "rJWbw1u3oDDRcYLFqiWFjhGWRKVcBAWdgp": 500000022.940415,  # Upbit17
    "rJo4m69u9Wd1F8fN2RbgAsJEF6a4hW1nSi": 500000022.974330,  # Upbit19
    "rLgn612WAgRoZ285YmsQ4t7kb8Ui3csdoU": 500000022.970497,  # Upbit20
    "rMNUAfSz2spLEbaBwPnGtxTzZCajJifnzH": 500000022.930304,  # Upbit16
    "rNcAdhSLXBrJ3aZUq22HaNtNEPpB5fR8Ri": 500000070.927547,  # Upbit14
    "raQwCVAJVqjrVm1Nj5SFRcX8i22BhdC9WA": 5380330.943804,  # Upbit1
    "rfL1mn4VTCoHdhHhHMwqpShCFUaDBRk6Z5": 500000113.144652,  # Upbit12
    "rs48xReB6gjKtTnTfii93iwUhjhTJsW78B": 500000022.951598,  # Upbit18
    "rwa7YXssGVAL9yPKw6QJtCen2UqZbRQqpM": 500000111.032735,  # Upbit13
    # Binance
    "r3ZVNKgkkT3A7hbEZ8HxnNnLDCCmZiZECV": 4319156.176484,  # Binance US 3
    "rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh": 7375.223257,  # Binance 1
    "rEeEWeP88cpKUddKk37B2EZeiHBGiBXY3": 122.800031,  # Binance US 1
    "rMvYS27SYs5dXdFsUgpvv1CSrPsCz7ePF5": 219728.667554,  # Binance US 2
    "rNU4eAowPuixS5ZCWaRL72UUeKgxcKExpK": 6152514.319652,  # Binance 10
    "rNxp4h8apvRis6mJf9Sh8C6iRxfrDWN7AV": 268204.837425,  # Binance 11
    "rPCpZwPKogNodbjRxGDnefVXu9Q9R4PN4Q": 593.363378,  # Binance US 4
    "rPJ5GFpyDLv7gqeB1uZVUBwDwi41kaXN5A": 109917943.727643,  # Binance 12
    "rPz2qA93PeRCyHyFCqyNggnyycJR1N4iNf": 661827727.919798,  # Binance 13
    "rhWj9gaovwu2hZxYW7p388P8GRbuXFLQkK": 4831865.223177,  # Binance 14
    # Kraken
    "rGZjPjMkfhAqmc1ssEiT753uAgyftHRo2m": 20.251542,  # Kraken3
    "rLHzPsX6oXkzU2qL12kHCH8G8cnZv1rBJh": 25860812.904039,  # Kraken1
    "rUeDDFNp2q7Ymvyv75hFGC8DAcygVyJbNF": 265582363.149146,  # Kraken2
    "rp7TCczQuQo61dUo1oAgwdpRxLrA8vDaNV": 290523350.512168,  # Kraken4
    # Bybit
    "rJn2zAPdFA193sixJwuFixRkYDUtx3apQh": 4653377.535326,  # Bybit 3
    "rMrgNBrkE6FdCjWih5VAWkGMrmerrWpiZt": 9.757080,  # Bybit 1
    "rMvCasZ9cohYrSZRNYPTZfoaaSUQMfgQ8G": 116576792.538589,  # Bybit 4
    "rNFKfGBzMspdKfaZdpnEyhkFyw7C1mtQ8x": 20.965423,  # Bybit 2
    "raQxZLtqurEXvH5sgijrif7yXMNwvFRkJN": 147378587.843680,  # Bybit 6
    "rwBHqnCgNRnk3Kyoc6zon6Wt4Wujj3HNGe": 57941994.752545,  # Bybit 5
    # SBI VC Trade
    "r39uEuRjzLaSgvkjTfcejodbSrXLM3cYnX": 293.297424,  # SBI VC Trade 6
    "rDDyH5nfvozKZQCwiBrWfcE528sWsBPWET": 2639.366730,  # SBI VC Trade 1
    "rKcVYzVK1f4PhRFjLhWP7QmteG5FpPgRub": 36.929646,  # SBI VC Trade 2
    "rNRc2S2GSefSkTkAiyjE6LDzMonpeHp6jS": 318277941.998112,  # SBI VC TRADE 4
    "rUaESVd1yLMy5VyoJvwwuqE8ZiCb2PEqBR": 1123.897979,  # SBI VC Trade 3
    "raSZXZApFg7Nj1B5G6BnhoL6HcTqVMopJ3": 79576.400141,  # SBI VC Trade 5
}

HISTORICAL_DATE = "Feb 24, 2025"

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
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and "account_data" in result["result"]:
                        balance_drops = int(result["result"]["account_data"]["Balance"])
                        return balance_drops / 1_000_000
                break
            except requests.exceptions.Timeout:
                if i < MAX_RETRIES - 1:
                    time.sleep(1)
                continue
            except Exception:
                break
    except Exception:
        pass
    return 0.0


def get_historical_balance(address: str) -> Optional[float]:
    """Get historical balance from Feb 24, 2025 benchmark data"""
    return HISTORICAL_BALANCES_20250224.get(address)


def fetch_all_balances(progress_callback=None) -> Dict:
    """Fetch balances for all exchanges with historical comparison"""
    results = {}
    total_addresses = sum(len(wallets) for wallets in EXCHANGES.values())
    current = 0
    
    for exchange_name, wallets in EXCHANGES.items():
        exchange_total = 0
        exchange_historical = 0
        wallet_details = []
        has_historical = False
        
        for address, wallet_name in wallets.items():
            balance = get_xrp_balance(address)
            historical = get_historical_balance(address)
            
            exchange_total += balance
            
            wallet_info = {
                "address": address,
                "name": wallet_name,
                "balance": balance,
                "historical": historical
            }
            
            if historical is not None:
                exchange_historical += historical
                has_historical = True
                wallet_info["change"] = balance - historical
                wallet_info["change_pct"] = ((balance - historical) / historical * 100) if historical > 0 else 0
            
            wallet_details.append(wallet_info)
            
            current += 1
            if progress_callback:
                progress_callback(current / total_addresses)
        
        results[exchange_name] = {
            "total": exchange_total,
            "historical": exchange_historical if has_historical else None,
            "wallets": wallet_details,
            "wallet_count": len(wallets),
            "has_historical": has_historical
        }
        
        if has_historical:
            results[exchange_name]["change"] = exchange_total - exchange_historical
            results[exchange_name]["change_pct"] = ((exchange_total - exchange_historical) / exchange_historical * 100) if exchange_historical > 0 else 0
    
    return results


def create_summary_dataframe(data: Dict) -> pd.DataFrame:
    """Create summary DataFrame with historical comparison"""
    rows = []
    for exchange, info in data.items():
        row = {
            "Exchange": exchange,
            "Balance (XRP)": info["total"],
            "Wallet Count": info["wallet_count"]
        }
        
        if info.get("has_historical"):
            row[f"Balance ({HISTORICAL_DATE})"] = info["historical"]
            row["Change (XRP)"] = info["change"]
            row["Change (%)"] = info["change_pct"]
        else:
            row[f"Balance ({HISTORICAL_DATE})"] = None
            row["Change (XRP)"] = None
            row["Change (%)"] = None
            
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df = df.sort_values("Balance (XRP)", ascending=False).reset_index(drop=True)
    
    # Calculate market share
    total = df["Balance (XRP)"].sum()
    df["Market Share (%)"] = df["Balance (XRP)"] / total * 100
    
    # Reorder columns
    cols = ["Exchange", "Balance (XRP)", f"Balance ({HISTORICAL_DATE})", "Change (XRP)", "Change (%)", "Market Share (%)", "Wallet Count"]
    df = df[[c for c in cols if c in df.columns]]
    
    df.index = df.index + 1
    df.index.name = "Rank"
    return df


@st.cache_data(ttl=60)  # Cache price for 1 minute
def get_xrp_price():
    """Fetch current XRP price from CoinGecko API"""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "ripple", "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "price": data["ripple"]["usd"],
                "change_24h": data["ripple"]["usd_24h_change"]
            }
    except:
        pass
    return {"price": None, "change_24h": None}


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
    
    # Custom CSS + Twitter/X Follow Popup
    st.markdown("""
        <style>
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        [data-testid="stMetric"] label { color: #555 !important; }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #1f77b4 !important;
            font-size: 1.8rem !important;
        }
        @media (prefers-color-scheme: dark) {
            [data-testid="stMetric"] {
                background-color: #262730;
                border: 1px solid #3d3d3d;
            }
            [data-testid="stMetric"] label { color: #fafafa !important; }
            [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #00d4ff !important; }
        }
        
        /* Header widgets container */
        .header-widgets {
            display: flex;
            gap: 15px;
            margin: 10px 0 20px 0;
            flex-wrap: wrap;
        }
        
        /* XRP Price Widget */
        .xrp-price-widget {
            background: linear-gradient(135deg, #0a1628 0%, #1a2940 100%);
            border: 1px solid #00d4ff;
            border-radius: 12px;
            padding: 15px 25px;
            display: inline-flex;
            flex-direction: column;
            align-items: flex-start;
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
        }
        .price-label {
            color: #00d4ff;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .price-value {
            color: #ffffff;
            font-size: 28px;
            font-weight: bold;
        }
        .price-change {
            font-size: 13px;
            margin-top: 3px;
        }
        .price-change.positive { color: #00c853; }
        .price-change.negative { color: #ff5252; }
        
        /* X Army Follow Widget */
        .x-army-widget {
            background: linear-gradient(135deg, #1a1a2e 0%, #232333 100%);
            border: 1px solid #333;
            border-radius: 12px;
            padding: 12px 20px;
            display: inline-flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .x-army-widget:hover {
            border-color: #1da1f2;
            box-shadow: 0 0 15px rgba(29, 161, 242, 0.3);
            transform: translateY(-2px);
        }
        .x-logo {
            background: #ffffff;
            color: #000000;
            width: 32px;
            height: 32px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
        }
        .x-army-text {
            display: flex;
            flex-direction: column;
        }
        .x-army-title {
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
        }
        .x-army-title span { color: #00d4ff; }
        .x-army-handle {
            color: #888;
            font-size: 12px;
        }
        
        /* X Follow Popup Styles */
        .popup-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 999999;
        }
        .popup-overlay.show {
            display: flex !important;
        }
        .popup-content {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 400px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(29, 161, 242, 0.3);
            border: 2px solid rgba(29, 161, 242, 0.3);
            animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        @keyframes popIn {
            from { transform: scale(0.7); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        
        /* Bouncing X Icon */
        .x-icon {
            font-size: 60px;
            margin-bottom: 20px;
            display: inline-block;
            animation: bounce 1s ease infinite;
        }
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-20px); }
            60% { transform: translateY(-10px); }
        }
        
        .popup-headline {
            color: #ffffff;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 0 0 20px rgba(29, 161, 242, 0.5);
        }
        .popup-subtext {
            color: #a0a0a0;
            font-size: 14px;
            margin-bottom: 25px;
        }
        
        /* Glowing Follow Button */
        .follow-btn {
            background: linear-gradient(45deg, #1da1f2, #0d8ecf);
            color: white !important;
            border: none;
            padding: 15px 35px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            text-decoration: none !important;
            display: inline-block;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 0 20px rgba(29, 161, 242, 0.5), 0 0 40px rgba(29, 161, 242, 0.3);
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
            from { box-shadow: 0 0 20px rgba(29, 161, 242, 0.5), 0 0 40px rgba(29, 161, 242, 0.3); }
            to { box-shadow: 0 0 30px rgba(29, 161, 242, 0.8), 0 0 60px rgba(29, 161, 242, 0.5); }
        }
        .follow-btn:hover {
            transform: scale(1.05);
            background: linear-gradient(45deg, #0d8ecf, #1da1f2);
        }
        
        /* Dismiss Button */
        .dismiss-btn {
            background: transparent;
            color: #666;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            cursor: pointer;
            transition: color 0.3s ease;
        }
        .dismiss-btn:hover {
            color: #999;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("💎 XRP Exchange Holdings Tracker")
    
    # Get XRP price
    xrp_data = get_xrp_price()
    
    # Import components
    import streamlit.components.v1 as components
    
    # Header widgets using native Streamlit columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # XRP Price
        if xrp_data["price"]:
            change_sign = "+" if xrp_data["change_24h"] >= 0 else ""
            change_color = "#00c853" if xrp_data["change_24h"] >= 0 else "#ff5252"
            st.markdown(f'''
                <div style="background: linear-gradient(135deg, #0a1628, #1a2940); border: 2px solid #00d4ff; border-radius: 12px; padding: 15px 20px; box-shadow: 0 0 15px rgba(0,212,255,0.2);">
                    <div style="color: #00d4ff; font-size: 12px; font-weight: 600; letter-spacing: 1px;">XRP PRICE</div>
                    <div style="color: #fff; font-size: 28px; font-weight: bold;">${xrp_data["price"]:.4f}</div>
                    <div style="color: {change_color}; font-size: 14px;">{change_sign}{xrp_data["change_24h"]:.2f}% (24h)</div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
                <div style="background: linear-gradient(135deg, #0a1628, #1a2940); border: 2px solid #00d4ff; border-radius: 12px; padding: 15px 20px;">
                    <div style="color: #00d4ff; font-size: 12px; font-weight: 600;">XRP PRICE</div>
                    <div style="color: #fff; font-size: 28px; font-weight: bold;">Loading...</div>
                </div>
            ''', unsafe_allow_html=True)
    
    with col2:
        # X Army link
        st.markdown('''
            <a href="https://twitter.com/chachakobe4er" target="_blank" style="text-decoration: none; display: block;">
                <div style="background: linear-gradient(135deg, #1a1a2e, #232333); border: 2px solid #1da1f2; border-radius: 12px; padding: 15px 20px; display: flex; align-items: center; gap: 12px;">
                    <div style="background: #fff; color: #000; width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold;">𝕏</div>
                    <div>
                        <div style="color: #fff; font-size: 16px; font-weight: 600;">XRP <span style="color: #00d4ff;">𝕏</span> Army</div>
                        <div style="color: #888; font-size: 13px;">@chachakobe4er</div>
                    </div>
                </div>
            </a>
        ''', unsafe_allow_html=True)
    
    with col3:
        # ETF Tracker link
        st.markdown('''
            <a href="https://xrp-1-0jnc.onrender.com/" target="_blank" style="text-decoration: none; display: block;">
                <div style="background: linear-gradient(135deg, #0a2e1a, #1a4a2e); border: 2px solid #00c853; border-radius: 12px; padding: 15px 20px; display: flex; align-items: center; gap: 12px;">
                    <div style="background: #00c853; color: #000; width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">ETF</div>
                    <div>
                        <div style="color: #fff; font-size: 16px; font-weight: 600;">XRP <span style="color: #00c853;">ETF</span> Tracker</div>
                        <div style="color: #888; font-size: 13px;">Track XRP ETF Filings</div>
                    </div>
                </div>
            </a>
        ''', unsafe_allow_html=True)
    
    # Google Analytics tracking
    GA_TRACKING_ID = "G-3EVLLY6ND7"
    
    components.html(f'''
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA_TRACKING_ID}');
        </script>
    ''', height=0)
    
    st.markdown(f"Real-time tracking of XRP holdings | **Historical benchmark: {HISTORICAL_DATE}**")
    
    # Twitter Follow Popup
    if 'popup_closed' not in st.session_state:
        st.session_state.popup_closed = False
    
    if not st.session_state.popup_closed:
        st.markdown("---")
        popup_col1, popup_col2, popup_col3 = st.columns([1, 2, 1])
        with popup_col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); border-radius: 20px; padding: 30px; text-align: center; border: 2px solid rgba(29, 161, 242, 0.5); box-shadow: 0 0 40px rgba(29, 161, 242, 0.3);">
                <div style="font-size: 50px; background: #fff; color: #000; width: 70px; height: 70px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 15px;">𝕏</div>
                <div style="color: #fff; font-size: 24px; font-weight: bold; margin-bottom: 10px;">🚀 Join the XRP Army!</div>
                <div style="color: #aaa; font-size: 14px; margin-bottom: 20px;">Stay updated with the latest XRP insights & alpha</div>
                <a href="https://twitter.com/chachakobe4er" target="_blank" style="background: linear-gradient(45deg, #1da1f2, #0d8ecf); color: white; padding: 15px 35px; font-size: 16px; font-weight: bold; border-radius: 50px; text-decoration: none; display: inline-block; box-shadow: 0 0 20px rgba(29, 161, 242, 0.6);">
                    ✨ Follow @chachakobe4er ✨
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            if st.button("❌ Maybe later", use_container_width=True, key="dismiss_popup"):
                st.session_state.popup_closed = True
                st.rerun()
        st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Controls")
        
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        st.subheader("📊 Filter Exchanges")
        all_exchanges = list(EXCHANGES.keys())
        selected_exchanges = st.multiselect(
            "Select exchanges to display",
            options=all_exchanges,
            default=all_exchanges,
            help="Choose which exchanges to include"
        )
        
        st.markdown("---")
        
        st.subheader("⚙️ Display Options")
        show_historical = st.checkbox("Show historical comparison", value=True, help=f"Compare to {HISTORICAL_DATE}")
        show_wallet_details = st.checkbox("Show wallet-level details", value=False)
        chart_type = st.selectbox("Chart Type", ["Bar Chart", "Treemap", "Pie Chart"], index=0)
        top_n = st.slider("Top N exchanges to highlight", 5, 20, 10)
        
        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"Historical benchmark: {HISTORICAL_DATE}")
        
        # Visitor counter
        st.markdown("---")
        visitor_count = get_visitor_count()
        st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 10px; border: 1px solid #00d4ff;">
                <div style="color: #00d4ff; font-size: 11px; letter-spacing: 1px;">👥 VISITORS</div>
                <div style="color: #fff; font-size: 24px; font-weight: bold;">{visitor_count:,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Add analytics tracking (GoatCounter - free, privacy-friendly)
    components.html("""
        <script>
            // Simple page view tracking
            (function() {
                var sessionKey = 'xrp_dashboard_session';
                if (!sessionStorage.getItem(sessionKey)) {
                    sessionStorage.setItem(sessionKey, 'true');
                    // Log visit (you can replace with your own analytics endpoint)
                    console.log('New visitor session');
                }
            })();
        </script>
        
        <!-- Optional: Add GoatCounter for free analytics -->
        <!-- Uncomment and replace 'yoursite' with your GoatCounter site name -->
        <!-- <script data-goatcounter="https://yoursite.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script> -->
    """, height=0)
    
    if not selected_exchanges:
        st.warning("Please select at least one exchange from the sidebar.")
        return
    
    # Fetch data
    with st.spinner("Fetching live data from XRP Ledger..."):
        progress_bar = st.progress(0)
        data = fetch_all_balances(progress_callback=lambda p: progress_bar.progress(p))
        progress_bar.empty()
    
    filtered_data = {k: v for k, v in data.items() if k in selected_exchanges}
    df = create_summary_dataframe(filtered_data)
    
    # Key Metrics
    st.markdown("### 📈 Market Overview")
    
    total_xrp = df["Balance (XRP)"].sum()
    top3_share = df.head(3)["Market Share (%)"].sum()
    top10_share = df.head(10)["Market Share (%)"].sum()
    exchange_count = len(df)
    
    total_historical = df[f"Balance ({HISTORICAL_DATE})"].dropna().sum()
    total_change = total_xrp - total_historical if total_historical > 0 else None
    total_change_pct = (total_change / total_historical * 100) if total_historical > 0 else None
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(label="Total XRP Holdings", value=f"{total_xrp:,.0f}")
    with col2:
        st.metric(label="Exchanges Tracked", value=f"{exchange_count}")
    with col3:
        st.metric(label="Top 3 Concentration", value=f"{top3_share:.1f}%")
    with col4:
        st.metric(label="Top 10 Concentration", value=f"{top10_share:.1f}%")
    with col5:
        if show_historical and total_change is not None:
            st.metric(label=f"Change Since {HISTORICAL_DATE}", value=f"{total_change:+,.0f}", delta=f"{total_change_pct:+.1f}%")
        else:
            st.metric(label=f"Change Since {HISTORICAL_DATE}", value="N/A")
    
    st.markdown("---")
    
    # Charts Row
    col_chart, col_table = st.columns([1.2, 1])
    
    with col_chart:
        st.markdown(f"### 📊 Holdings Distribution (Top {top_n})")
        chart_df = df.head(top_n).copy()
        
        if chart_type == "Bar Chart":
            fig = px.bar(chart_df, x="Exchange", y="Balance (XRP)", color="Market Share (%)",
                        color_continuous_scale="Blues",
                        text=chart_df["Balance (XRP)"].apply(lambda x: f"{x/1e6:.1f}M"),
                        hover_data=["Market Share (%)", "Wallet Count"])
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_tickangle=-45, height=500, showlegend=False,
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        elif chart_type == "Treemap":
            fig = px.treemap(chart_df, path=["Exchange"], values="Balance (XRP)",
                           color="Balance (XRP)", color_continuous_scale="Blues",
                           hover_data=["Market Share (%)", "Wallet Count"])
            fig.update_layout(height=500)
        else:
            fig = px.pie(chart_df, names="Exchange", values="Balance (XRP)", hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col_table:
        st.markdown("### 🏆 Rankings")
        display_df = df.copy()
        display_df["Balance (XRP)"] = display_df["Balance (XRP)"].apply(lambda x: f"{x:,.0f}")
        display_df["Market Share (%)"] = display_df["Market Share (%)"].apply(lambda x: f"{x:.2f}%")
        
        if show_historical:
            display_df[f"Balance ({HISTORICAL_DATE})"] = display_df[f"Balance ({HISTORICAL_DATE})"].apply(
                lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
            display_df["Change (XRP)"] = display_df["Change (XRP)"].apply(
                lambda x: f"{x:+,.0f}" if pd.notna(x) else "N/A")
            display_df["Change (%)"] = display_df["Change (%)"].apply(
                lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")
            cols_to_show = ["Exchange", "Balance (XRP)", f"Balance ({HISTORICAL_DATE})", "Change (XRP)", "Change (%)", "Market Share (%)"]
        else:
            cols_to_show = ["Exchange", "Balance (XRP)", "Market Share (%)", "Wallet Count"]
        
        st.dataframe(display_df[cols_to_show], use_container_width=True, height=450)
    
    st.markdown("---")
    
    # Historical Change Analysis
    if show_historical:
        st.markdown(f"### 📊 Change Since {HISTORICAL_DATE}")
        hist_df = df[df["Change (XRP)"].notna()].copy()
        
        if len(hist_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                hist_df_sorted = hist_df.sort_values("Change (XRP)", ascending=True)
                colors = ['#ff5252' if x < 0 else '#00c853' for x in hist_df_sorted["Change (XRP)"]]
                
                fig_change = go.Figure(go.Bar(
                    x=hist_df_sorted["Change (XRP)"],
                    y=hist_df_sorted["Exchange"],
                    orientation='h',
                    marker_color=colors,
                    text=hist_df_sorted["Change (XRP)"].apply(lambda x: f"{x/1e6:+.1f}M"),
                    textposition='outside'
                ))
                fig_change.update_layout(title=f"XRP Balance Change Since {HISTORICAL_DATE}",
                                        xaxis_title="Change (XRP)", height=400, showlegend=False)
                st.plotly_chart(fig_change, use_container_width=True)
            
            with col2:
                hist_df_pct = hist_df.sort_values("Change (%)", ascending=True)
                colors_pct = ['#ff5252' if x < 0 else '#00c853' for x in hist_df_pct["Change (%)"]]
                
                fig_pct = go.Figure(go.Bar(
                    x=hist_df_pct["Change (%)"],
                    y=hist_df_pct["Exchange"],
                    orientation='h',
                    marker_color=colors_pct,
                    text=hist_df_pct["Change (%)"].apply(lambda x: f"{x:+.1f}%"),
                    textposition='outside'
                ))
                fig_pct.update_layout(title=f"Percentage Change Since {HISTORICAL_DATE}",
                                     xaxis_title="Change (%)", height=400, showlegend=False)
                st.plotly_chart(fig_pct, use_container_width=True)
            
            gainers = hist_df[hist_df["Change (XRP)"] > 0]
            losers = hist_df[hist_df["Change (XRP)"] < 0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Exchanges with Gains", len(gainers))
            with col2:
                st.metric("Exchanges with Losses", len(losers))
            with col3:
                net_change = hist_df["Change (XRP)"].sum()
                st.metric("Net Change (Tracked)", f"{net_change:+,.0f} XRP")
        else:
            st.info(f"No historical data available for the selected exchanges.")
    
    st.markdown("---")
    
    # Market Share Analysis
    st.markdown("### 🥧 Market Share Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_share = px.bar(df.head(15), y="Exchange", x="Market Share (%)", orientation="h",
                          color="Market Share (%)", color_continuous_scale="Viridis",
                          text=df.head(15)["Market Share (%)"].apply(lambda x: f"{x:.1f}%"))
        fig_share.update_traces(textposition="outside")
        fig_share.update_layout(height=500, yaxis={'categoryorder': 'total ascending'},
                               showlegend=False, title="Market Share by Exchange")
        st.plotly_chart(fig_share, use_container_width=True)
    
    with col2:
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
        fig_cumulative.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="50% threshold")
        fig_cumulative.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80% threshold")
        fig_cumulative.update_layout(title="Cumulative Market Concentration",
                                     xaxis_title="Number of Exchanges",
                                     yaxis_title="Cumulative Market Share (%)", height=500)
        st.plotly_chart(fig_cumulative, use_container_width=True)
    
    # Wallet-level details
    if show_wallet_details:
        st.markdown("---")
        st.markdown("### 🔍 Wallet-Level Details")
        
        selected_exchange = st.selectbox("Select an exchange to view wallet details", options=selected_exchanges)
        
        if selected_exchange and selected_exchange in filtered_data:
            wallet_data = filtered_data[selected_exchange]["wallets"]
            wallet_df = pd.DataFrame(wallet_data)
            wallet_df = wallet_df.sort_values("balance", ascending=False).reset_index(drop=True)
            wallet_df.index = wallet_df.index + 1
            
            display_wallet_df = wallet_df.copy()
            display_wallet_df = display_wallet_df.rename(columns={"address": "Address", "name": "Wallet Name", "balance": "Balance (XRP)"})
            
            if show_historical and "historical" in wallet_df.columns:
                display_wallet_df["Historical"] = wallet_df["historical"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
                display_wallet_df["Change"] = wallet_df.apply(lambda r: f"{r['change']:+,.0f}" if pd.notna(r.get('change')) else "N/A", axis=1)
                display_wallet_df["Change %"] = wallet_df.apply(lambda r: f"{r['change_pct']:+.2f}%" if pd.notna(r.get('change_pct')) else "N/A", axis=1)
            
            display_wallet_df["Balance (XRP)"] = display_wallet_df["Balance (XRP)"].apply(lambda x: f"{x:,.0f}")
            
            cols_to_display = ["Address", "Wallet Name", "Balance (XRP)"]
            if show_historical and "Historical" in display_wallet_df.columns:
                cols_to_display.extend(["Historical", "Change", "Change %"])
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(display_wallet_df[cols_to_display], use_container_width=True)
            
            with col2:
                raw_wallet_df = pd.DataFrame(wallet_data)
                if len(raw_wallet_df) > 1 and raw_wallet_df["balance"].sum() > 0:
                    fig_wallet = px.pie(raw_wallet_df, names="name", values="balance",
                                       title=f"{selected_exchange} Wallet Distribution")
                    fig_wallet.update_layout(height=300, showlegend=True)
                    st.plotly_chart(fig_wallet, use_container_width=True)
    
    # Export functionality
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv()
        st.download_button(label="📄 Download CSV", data=csv,
                          file_name=f"xrp_holdings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                          mime="text/csv", use_container_width=True)
    
    with col2:
        json_data = json.dumps(filtered_data, indent=2, default=str)
        st.download_button(label="📋 Download JSON", data=json_data,
                          file_name=f"xrp_holdings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                          mime="application/json", use_container_width=True)
    
    with col3:
        report = f"""XRP Exchange Holdings Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Historical Benchmark: {HISTORICAL_DATE}
{'='*60}

MARKET OVERVIEW
- Total XRP Holdings: {total_xrp:,.0f} XRP
- Exchanges Tracked: {exchange_count}
- Top 3 Concentration: {top3_share:.2f}%
- Top 10 Concentration: {top10_share:.2f}%
"""
        if total_change is not None:
            report += f"- Change Since {HISTORICAL_DATE}: {total_change:+,.0f} XRP ({total_change_pct:+.2f}%)\n"
        
        report += f"\nTOP 10 EXCHANGES\n{'='*60}\n"
        for idx, row in df.head(10).iterrows():
            balance = row['Balance (XRP)']
            share = row['Market Share (%)']
            change = row.get('Change (XRP)')
            change_str = f" | Change: {change:+,.0f}" if pd.notna(change) else ""
            report += f"{idx}. {row['Exchange']}: {balance:,.0f} XRP ({share:.2f}%){change_str}\n"
        
        st.download_button(label="📝 Download Report", data=report,
                          file_name=f"xrp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                          mime="text/plain", use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.caption("💡 Data is fetched live from the XRP Ledger. Balances are cached for 5 minutes.")
    st.caption(f"📅 Historical comparison data from {HISTORICAL_DATE} for: Upbit, Binance, Kraken, Bybit, SBI VC Trade")
    st.caption("⚠️ This dashboard is for informational purposes only.")


if __name__ == "__main__":
    main()
