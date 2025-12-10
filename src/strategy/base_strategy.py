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
    
    def calculate_position_size(self, signal: float, current_price: float, current_capital: float = None) -> float:
        """
        Calculate position size based on available capital
        """
        if signal == 0:
            return 0
        
        # Use current capital if provided, otherwise use initial
        capital = current_capital if current_capital is not None else self.initial_capital
        
        # Use 5% risk per trade for more significant position sizes
        risk_amount = capital * 0.05
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
            current_position = 0
            
            for i in range(len(self.data)):
                if i == 0:
                    self.positions.iloc[i] = 0
                    self.capital.iloc[i] = self.initial_capital
                    continue
                
                current_signal = signals.iloc[i]
                current_price = self.data['close'].iloc[i]
                prev_capital = self.capital.iloc[i-1]
                
                # Skip if we don't have valid previous capital
                if pd.isna(prev_capital):
                    prev_capital = self.initial_capital
                
                # Position management: hold position until opposite signal
                if current_signal == 1:  # Buy signal
                    if current_position <= 0:  # Only enter if not already long
                        current_position = self.calculate_position_size(1, current_price, prev_capital)
                elif current_signal == -1:  # Sell signal
                    if current_position >= 0:  # Only enter if not already short
                        current_position = self.calculate_position_size(-1, current_price, prev_capital)
                # If signal is 0, maintain current position (no change)
                
                self.positions.iloc[i] = current_position
                
                # Calculate PnL based on held position
                price_change = self.data['close'].iloc[i] - self.data['close'].iloc[i-1]
                prev_position = self.positions.iloc[i-1] if not pd.isna(self.positions.iloc[i-1]) else 0
                pnl = prev_position * price_change
                self.capital.iloc[i] = prev_capital + pnl
            
            # Calculate performance metrics
            return self._calculate_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error during backtesting: {str(e)}")
            raise
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate strategy performance metrics
        """
        # Drop NaN values from capital series
        valid_capital = self.capital.dropna()
        valid_positions = self.positions.dropna()
        
        if len(valid_capital) < 2:
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'final_capital': self.initial_capital,
                'win_rate': 0.0,
                'total_trades': 0,
                'profit_factor': 0.0
            }
        
        returns = valid_capital.pct_change(fill_method=None).dropna()
        
        final_capital = valid_capital.iloc[-1]
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Handle edge cases
        annual_return = returns.mean() * 252 if len(returns) > 0 else 0
        volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0
        sharpe_ratio = annual_return / volatility if volatility != 0 else 0
        
        # Calculate max drawdown
        rolling_max = valid_capital.expanding().max()
        drawdowns = valid_capital / rolling_max - 1
        max_drawdown = drawdowns.min() if len(drawdowns) > 0 else 0
        
        # Calculate trade-based metrics
        position_changes = valid_positions.diff().fillna(0)
        trade_entries = position_changes[position_changes != 0]
        total_trades = len(trade_entries)
        
        # Calculate per-period PnL for win rate
        period_returns = valid_capital.diff().dropna()
        winning_periods = len(period_returns[period_returns > 0])
        total_periods = len(period_returns)
        win_rate = winning_periods / total_periods if total_periods > 0 else 0
        
        # Profit factor (gross profit / gross loss)
        gross_profit = period_returns[period_returns > 0].sum()
        gross_loss = abs(period_returns[period_returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'final_capital': final_capital,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'profit_factor': profit_factor
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
