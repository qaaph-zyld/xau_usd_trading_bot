import pandas as pd
import numpy as np
from typing import Tuple, Optional
from .base_strategy import BaseStrategy
import logging
import ta

logger = logging.getLogger(__name__)

class RSIMeanReversionStrategy(BaseStrategy):
    def __init__(self, data: pd.DataFrame,
                 rsi_period: int = 14,
                 oversold_threshold: int = 30,
                 overbought_threshold: int = 70,
                 initial_capital: float = 100000):
        """
        RSI Mean Reversion Strategy
        
        Args:
            data: DataFrame with OHLCV data
            rsi_period: Period for RSI calculation
            oversold_threshold: RSI threshold for oversold condition
            overbought_threshold: RSI threshold for overbought condition
            initial_capital: Starting capital for backtesting
        """
        super().__init__(data, initial_capital)
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self._calculate_indicators()
        
    def _calculate_indicators(self):
        """
        Calculate RSI indicator
        """
        try:
            self.data['rsi'] = ta.momentum.rsi(self.data['close'], 
                                             window=self.rsi_period)
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            raise
            
    def generate_signals(self) -> pd.Series:
        """
        Generate trading signals based on RSI mean reversion
        
        Returns:
            Series with trading signals (1: Buy, -1: Sell, 0: Hold)
        """
        signals = pd.Series(index=self.data.index, data=0)
        
        # Generate buy signals when RSI crosses above oversold threshold
        buy_signals = (self.data['rsi'] > self.oversold_threshold) & \
                     (self.data['rsi'].shift(1) <= self.oversold_threshold)
        
        # Generate sell signals when RSI crosses below overbought threshold
        sell_signals = (self.data['rsi'] < self.overbought_threshold) & \
                      (self.data['rsi'].shift(1) >= self.overbought_threshold)
        
        signals[buy_signals] = 1
        signals[sell_signals] = -1
        
        return signals
    
    def optimize_parameters(self, 
                          rsi_range: Tuple[int, int],
                          oversold_range: Tuple[int, int],
                          overbought_range: Tuple[int, int],
                          metric: str = 'sharpe_ratio') -> dict:
        """
        Optimize strategy parameters
        
        Args:
            rsi_range: (min, max) for RSI period
            oversold_range: (min, max) for oversold threshold
            overbought_range: (min, max) for overbought threshold
            metric: Performance metric to optimize for
            
        Returns:
            Dict with optimal parameters and performance
        """
        best_metric = float('-inf')
        best_params = {}
        
        for rsi_period in range(rsi_range[0], rsi_range[1]):
            for oversold in range(oversold_range[0], oversold_range[1]):
                for overbought in range(overbought_range[0], overbought_range[1]):
                    if oversold >= overbought:
                        continue
                        
                    # Test parameters
                    self.rsi_period = rsi_period
                    self.oversold_threshold = oversold
                    self.overbought_threshold = overbought
                    self._calculate_indicators()
                    
                    results = self.backtest()
                    current_metric = results[metric]
                    
                    if current_metric > best_metric:
                        best_metric = current_metric
                        best_params = {
                            'rsi_period': rsi_period,
                            'oversold_threshold': oversold,
                            'overbought_threshold': overbought,
                            'performance': results
                        }
        
        # Reset to best parameters
        self.rsi_period = best_params['rsi_period']
        self.oversold_threshold = best_params['oversold_threshold']
        self.overbought_threshold = best_params['overbought_threshold']
        self._calculate_indicators()
        
        return best_params
    
    def add_filters(self, trend_filter: bool = True, volatility_filter: bool = True):
        """
        Add additional filters to improve strategy performance
        
        Args:
            trend_filter: Use SMA trend filter
            volatility_filter: Use ATR volatility filter
        """
        if trend_filter:
            # Add 200-day SMA trend filter
            self.data['sma_200'] = self.data['close'].rolling(window=200).mean()
            
        if volatility_filter:
            # Add ATR volatility filter
            self.data['atr'] = ta.volatility.average_true_range(
                high=self.data['high'],
                low=self.data['low'],
                close=self.data['close'],
                window=14
            )
