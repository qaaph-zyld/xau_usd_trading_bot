from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000):
        """
        Initialize base strategy
        
        Args:
            data: DataFrame with OHLCV data and indicators
            initial_capital: Starting capital for backtesting
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.positions = pd.Series(index=data.index, dtype=float)
        self.capital = pd.Series(index=data.index, dtype=float)
        self.capital.iloc[0] = initial_capital
        
    @abstractmethod
    def generate_signals(self) -> pd.Series:
        """
        Generate trading signals
        Returns:
            Series with trading signals (1: Buy, -1: Sell, 0: Hold)
        """
        pass
    
    def calculate_position_size(self, signal: float, current_price: float) -> float:
        """
        Calculate position size based on available capital
        """
        if signal == 0:
            return 0
        
        # Use 2% risk per trade
        risk_amount = self.capital.iloc[-1] * 0.02
        position_size = risk_amount / current_price
        return position_size if signal > 0 else -position_size
    
    def backtest(self) -> Dict[str, Any]:
        """
        Run backtest and calculate performance metrics
        """
        try:
            # Generate signals
            signals = self.generate_signals()
            
            # Calculate positions and PnL
            for i in range(len(self.data)):
                if i == 0:
                    self.positions.iloc[i] = 0
                    continue
                
                current_signal = signals.iloc[i]
                current_price = self.data['close'].iloc[i]
                
                # Calculate new position size
                new_position = self.calculate_position_size(current_signal, current_price)
                self.positions.iloc[i] = new_position
                
                # Calculate PnL
                price_change = self.data['close'].iloc[i] - self.data['close'].iloc[i-1]
                pnl = self.positions.iloc[i-1] * price_change
                self.capital.iloc[i] = self.capital.iloc[i-1] + pnl
            
            # Calculate performance metrics
            return self._calculate_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error during backtesting: {str(e)}")
            raise
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate strategy performance metrics
        """
        returns = self.capital.pct_change().dropna()
        
        metrics = {
            'total_return': (self.capital.iloc[-1] - self.initial_capital) / self.initial_capital,
            'annual_return': returns.mean() * 252,  # Assuming daily data
            'volatility': returns.std() * np.sqrt(252),
            'sharpe_ratio': (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() != 0 else 0,
            'max_drawdown': (self.capital / self.capital.cummax() - 1).min(),
            'final_capital': self.capital.iloc[-1],
            'win_rate': len(returns[returns > 0]) / len(returns) if len(returns) > 0 else 0
        }
        
        return metrics
    
    def plot_performance(self, save_path: Optional[str] = None):
        """
        Plot strategy performance
        """
        try:
            import matplotlib.pyplot as plt
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Plot price and positions
            ax1.plot(self.data.index, self.data['close'], label='Price')
            ax1.scatter(self.data.index[self.positions > 0], 
                       self.data['close'][self.positions > 0],
                       marker='^', color='g', label='Buy')
            ax1.scatter(self.data.index[self.positions < 0],
                       self.data['close'][self.positions < 0],
                       marker='v', color='r', label='Sell')
            ax1.set_title('Trading Signals')
            ax1.legend()
            
            # Plot capital
            ax2.plot(self.data.index, self.capital, label='Portfolio Value')
            ax2.set_title('Portfolio Value')
            ax2.legend()
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
                
        except ImportError:
            logger.warning("Matplotlib not installed. Cannot plot performance.")
