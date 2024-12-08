import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .position_sizer import PositionSizer, PositionSize
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    daily_drawdown: float
    max_drawdown: float
    var_95: float
    expected_shortfall: float
    sharpe_ratio: float
    sortino_ratio: float

class RiskManager:
    def __init__(self,
                 initial_capital: float,
                 max_portfolio_risk: float = 0.05,
                 max_correlation: float = 0.7,
                 max_daily_trades: int = 3,
                 max_drawdown: float = 0.15):
        """
        Risk Manager for overall portfolio risk management
        
        Args:
            initial_capital: Initial trading capital
            max_portfolio_risk: Maximum portfolio risk as fraction of capital
            max_correlation: Maximum allowed correlation between positions
            max_daily_trades: Maximum number of trades per day
            max_drawdown: Maximum allowed drawdown
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlation = max_correlation
        self.max_daily_trades = max_daily_trades
        self.max_drawdown = max_drawdown
        
        self.position_sizer = PositionSizer()
        self.positions: Dict[str, PositionSize] = {}
        self.trade_history: List[Dict] = []
        self.daily_trades = 0
        self.last_trade_date = None
        
    def can_open_position(self, 
                         symbol: str,
                         correlation_matrix: pd.DataFrame) -> Tuple[bool, str]:
        """
        Check if a new position can be opened
        
        Returns:
            Tuple of (boolean, reason)
        """
        try:
            # Check daily trade limit
            current_date = datetime.now().date()
            if self.last_trade_date != current_date:
                self.daily_trades = 0
                self.last_trade_date = current_date
                
            if self.daily_trades >= self.max_daily_trades:
                return False, "Daily trade limit reached"
            
            # Check drawdown
            current_drawdown = (self.initial_capital - self.current_capital) / self.initial_capital
            if current_drawdown >= self.max_drawdown:
                return False, "Maximum drawdown reached"
            
            # Check correlation with existing positions
            if symbol in correlation_matrix.columns:
                for pos_symbol in self.positions:
                    if pos_symbol in correlation_matrix.columns:
                        correlation = abs(correlation_matrix.loc[symbol, pos_symbol])
                        if correlation > self.max_correlation:
                            return False, f"High correlation with existing position in {pos_symbol}"
            
            return True, "Position can be opened"
            
        except Exception as e:
            logger.error(f"Error checking position opening: {str(e)}")
            return False, str(e)
    
    def open_position(self,
                     symbol: str,
                     entry_price: float,
                     side: str,
                     atr: float,
                     correlation_matrix: pd.DataFrame) -> Optional[PositionSize]:
        """
        Open a new position with risk management
        """
        try:
            can_open, reason = self.can_open_position(symbol, correlation_matrix)
            if not can_open:
                logger.warning(f"Cannot open position: {reason}")
                return None
            
            # Calculate stop loss and take profit
            stop_loss = self.position_sizer.calculate_stop_loss(
                entry_price, atr, side
            )
            take_profit = self.position_sizer.calculate_take_profit(
                entry_price, stop_loss
            )
            
            # Calculate position size
            position = self.position_sizer.calculate_position_size(
                self.current_capital,
                entry_price,
                stop_loss,
                take_profit
            )
            
            # Adjust for correlation
            position.units = self.position_sizer.adjust_for_correlation(
                position.units,
                correlation_matrix,
                {k: v.units for k, v in self.positions.items()}
            )
            
            # Update positions and trade history
            self.positions[symbol] = position
            self.daily_trades += 1
            self.trade_history.append({
                'symbol': symbol,
                'entry_price': entry_price,
                'side': side,
                'position_size': position.units,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.now()
            })
            
            return position
            
        except Exception as e:
            logger.error(f"Error opening position: {str(e)}")
            return None
    
    def close_position(self,
                      symbol: str,
                      exit_price: float,
                      timestamp: datetime = None):
        """
        Close an existing position
        """
        try:
            if symbol not in self.positions:
                logger.warning(f"Position {symbol} not found")
                return
            
            position = self.positions[symbol]
            pnl = (exit_price - position.entry_price) * position.units
            
            # Update capital
            self.current_capital += pnl
            
            # Update trade history
            self.trade_history[-1].update({
                'exit_price': exit_price,
                'exit_time': timestamp or datetime.now(),
                'pnl': pnl
            })
            
            # Remove position
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
    
    def calculate_risk_metrics(self, returns: pd.Series) -> RiskMetrics:
        """
        Calculate various risk metrics
        """
        try:
            # Calculate drawdown
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns / rolling_max - 1
            
            # Calculate VaR and Expected Shortfall
            var_95 = returns.quantile(0.05)
            expected_shortfall = returns[returns <= var_95].mean()
            
            # Calculate Sharpe and Sortino ratios
            risk_free_rate = 0.02  # Assume 2% risk-free rate
            excess_returns = returns - risk_free_rate/252
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()
            
            downside_returns = returns[returns < 0]
            sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_returns.std()
            
            return RiskMetrics(
                daily_drawdown=drawdowns.iloc[-1],
                max_drawdown=drawdowns.min(),
                var_95=var_95,
                expected_shortfall=expected_shortfall,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            raise
    
    def update_stops(self, current_prices: Dict[str, float], atr_values: Dict[str, float]):
        """
        Update stop losses based on current prices and ATR
        """
        try:
            for symbol, position in self.positions.items():
                current_price = current_prices.get(symbol)
                atr = atr_values.get(symbol)
                
                if current_price is None or atr is None:
                    continue
                
                # Calculate trailing stop
                if position.units > 0:  # Long position
                    new_stop = current_price - (atr * self.position_sizer.atr_multiplier)
                    if new_stop > position.stop_loss_price:
                        position.stop_loss_price = new_stop
                else:  # Short position
                    new_stop = current_price + (atr * self.position_sizer.atr_multiplier)
                    if new_stop < position.stop_loss_price:
                        position.stop_loss_price = new_stop
                        
        except Exception as e:
            logger.error(f"Error updating stops: {str(e)}")
    
    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status
        """
        return {
            'current_capital': self.current_capital,
            'open_positions': len(self.positions),
            'daily_trades': self.daily_trades,
            'total_trades': len(self.trade_history),
            'current_drawdown': (self.initial_capital - self.current_capital) / self.initial_capital
        }
