import os
from datetime import datetime
import pandas as pd
from alpha_vantage.foreignexchange import ForeignExchange
from dotenv import load_dotenv
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ForexDataCollector:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not found in environment variables")
        self.fx = ForeignExchange(key=self.api_key)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def fetch_intraday_data(self, from_symbol="XAU", to_symbol="USD", interval="60min"):
        """
        Fetch intraday forex data from Alpha Vantage
        """
        try:
            logger.info(f"Fetching {from_symbol}/{to_symbol} data at {interval} interval")
            data, meta_data = self.fx.get_currency_exchange_intraday(
                from_symbol=from_symbol,
                to_symbol=to_symbol,
                interval=interval,
                outputsize='full'
            )
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data, orient='index')
            df.index = pd.to_datetime(df.index)
            df.columns = ['open', 'high', 'low', 'close']
            
            # Save data
            filename = f"{from_symbol}_{to_symbol}_{interval}_{datetime.now().strftime('%Y%m%d')}.csv"
            filepath = self.data_dir / filename
            df.to_csv(filepath)
            logger.info(f"Data saved to {filepath}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            raise

    def load_latest_data(self, from_symbol="XAU", to_symbol="USD", interval="60min"):
        """
        Load the most recent data file for the specified pair
        """
        pattern = f"{from_symbol}_{to_symbol}_{interval}_*.csv"
        files = list(self.data_dir.glob(pattern))
        if not files:
            return None
        
        latest_file = max(files, key=os.path.getctime)
        return pd.read_csv(latest_file, index_col=0, parse_dates=True)

if __name__ == "__main__":
    collector = ForexDataCollector()
    try:
        data = collector.fetch_intraday_data()
        print(f"Successfully collected {len(data)} data points")
    except Exception as e:
        print(f"Error: {str(e)}")
