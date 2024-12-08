import pandas as pd
import numpy as np
import ta
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with a DataFrame containing OHLC data
        """
        self.data = data.copy()
        self._validate_data()

    def _validate_data(self):
        """
        Validate that the DataFrame has the required columns
        """
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in self.data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")

    def add_moving_averages(self, periods=[20, 50, 200]):
        """
        Add Simple Moving Averages for specified periods
        """
        for period in periods:
            self.data[f'sma_{period}'] = ta.trend.sma_indicator(
                self.data['close'], 
                window=period
            )
        return self.data

    def add_rsi(self, period=14):
        """
        Add Relative Strength Index
        """
        self.data['rsi'] = ta.momentum.rsi(
            self.data['close'], 
            window=period
        )
        return self.data

    def add_bollinger_bands(self, period=20, std_dev=2):
        """
        Add Bollinger Bands
        """
        indicator_bb = ta.volatility.BollingerBands(
            close=self.data["close"], 
            window=period, 
            window_dev=std_dev
        )
        self.data['bb_upper'] = indicator_bb.bollinger_hband()
        self.data['bb_middle'] = indicator_bb.bollinger_mavg()
        self.data['bb_lower'] = indicator_bb.bollinger_lband()
        return self.data

    def add_macd(self, fast_period=12, slow_period=26, signal_period=9):
        """
        Add MACD indicators
        """
        self.data['macd'] = ta.trend.macd(
            self.data['close'],
            window_slow=slow_period,
            window_fast=fast_period
        )
        self.data['macd_signal'] = ta.trend.macd_signal(
            self.data['close'],
            window_slow=slow_period,
            window_fast=fast_period,
            window_sign=signal_period
        )
        self.data['macd_diff'] = ta.trend.macd_diff(
            self.data['close'],
            window_slow=slow_period,
            window_fast=fast_period,
            window_sign=signal_period
        )
        return self.data

    def add_atr(self, period=14):
        """
        Add Average True Range for volatility analysis
        """
        self.data['atr'] = ta.volatility.average_true_range(
            high=self.data['high'],
            low=self.data['low'],
            close=self.data['close'],
            window=period
        )
        return self.data

    def analyze_all(self):
        """
        Add all technical indicators
        """
        try:
            self.add_moving_averages()
            self.add_rsi()
            self.add_bollinger_bands()
            self.add_macd()
            self.add_atr()
            logger.info("Successfully added all technical indicators")
            return self.data
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            raise
