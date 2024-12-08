import pandas as pd
import numpy as np
from typing import Tuple, Optional
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, data: pd.DataFrame, 
                 short_window: int = 50,
                 long_window: int = 200,
                 initial_capital: float = 100000):
        """
        SMA Crossover Strategy
        
        Args:
            data: DataFrame with OHLCV data
            short_window: Short-term SMA period
            long_window: Long-term SMA period
            initial_capital: Starting capital for backtesting
        """
        super().__init__(data, initial_capital)
        self.short_window = short_window
        self.long_window = long_window
        self._calculate_indicators()
        
    def _calculate_indicators(self):
        """
        Calculate required technical indicators
        """
        try:
            self.data[f'sma_{self.short_window}'] = self.data['close'].rolling(window=self.short_window).mean()
            self.data[f'sma_{self.long_window}'] = self.data['close'].rolling(window=self.long_window).mean()
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise
            
    def generate_signals(self) -> pd.Series:
        """
        Generate trading signals based on SMA crossover
        
        Returns:
            Series with trading signals (1: Buy, -1: Sell, 0: Hold)
        """
        signals = pd.Series(index=self.data.index, data=0)
        
        # Calculate crossover
        golden_cross = (self.data[f'sma_{self.short_window}'] > self.data[f'sma_{self.long_window}']) & \
                      (self.data[f'sma_{self.short_window}'].shift(1) <= self.data[f'sma_{self.long_window}'].shift(1))
        death_cross = (self.data[f'sma_{self.short_window}'] < self.data[f'sma_{self.long_window}']) & \
                     (self.data[f'sma_{self.short_window}'].shift(1) >= self.data[f'sma_{self.long_window}'].shift(1))
        
        # Generate signals
        signals[golden_cross] = 1
        signals[death_cross] = -1
        
        return signals
    
    def optimize_parameters(self, short_range: Tuple[int, int], 
                          long_range: Tuple[int, int],
                          metric: str = 'sharpe_ratio') -> dict:
        """
        Optimize strategy parameters
        
        Args:
            short_range: (min, max) for short SMA window
            long_range: (min, max) for long SMA window
            metric: Performance metric to optimize for
            
        Returns:
            Dict with optimal parameters and performance
        """
        best_metric = float('-inf')
        best_params = {}
        
        for short in range(short_range[0], short_range[1]):
            for long in range(long_range[0], long_range[1]):
                if short >= long:
                    continue
                    
                # Test parameters
                self.short_window = short
                self.long_window = long
                self._calculate_indicators()
                
                results = self.backtest()
                current_metric = results[metric]
                
                if current_metric > best_metric:
                    best_metric = current_metric
                    best_params = {
                        'short_window': short,
                        'long_window': long,
                        'performance': results
                    }
        
        # Reset to best parameters
        self.short_window = best_params['short_window']
        self.long_window = best_params['long_window']
        self._calculate_indicators()
        
        return best_params
