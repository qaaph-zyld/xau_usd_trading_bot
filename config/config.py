from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data settings
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Trading pair settings
TRADING_PAIR = {
    "from_symbol": "XAU",
    "to_symbol": "USD",
    "interval": "60min"
}

# Technical analysis settings
TECHNICAL_PARAMS = {
    "sma_periods": [20, 50, 200],
    "rsi_period": 14,
    "bollinger_period": 20,
    "bollinger_std": 2,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "atr_period": 14
}

# API Configuration
API_CONFIG = {
    "alpha_vantage_key": os.getenv("ALPHA_VANTAGE_API_KEY"),
    "request_timeout": 30,
    "max_retries": 3
}
