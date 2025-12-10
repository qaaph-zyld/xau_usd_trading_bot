"""
Momentum Strategy

Based on market analysis findings:
- After 3+ consecutive up days: 54.6% win rate, +0.14% avg return
- Above 200 SMA filter adds +2.22% return

Strategy:
- Buy after 3+ consecutive up days
- Only when above 200 SMA
- Trail stop at recent swing low
- Exit when momentum fades or stopped out
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import ta


class MomentumStrategy:
    """
    A momentum strategy that buys after consecutive up days.
    """
    
    def __init__(self,
                 data: pd.DataFrame,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.02,
                 consecutive_days: int = 3,
                 hold_days: int = 5):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.consecutive_days = consecutive_days
        self.hold_days = hold_days
        
        self.positions = pd.Series(index=data.index, data=0.0)
        self.capital = pd.Series(index=data.index, data=0.0)
        self.trades = []
        
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate indicators."""
        # Returns
        self.data['returns'] = self.data['close'].pct_change()
        
        # Trend filter
        self.data['sma_200'] = ta.trend.sma_indicator(self.data['close'], window=200)
        self.data['above_200'] = self.data['close'] > self.data['sma_200']
        
        # ATR for stops
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        
        # Count consecutive up/down days
        self.data['up_day'] = self.data['returns'] > 0
        
        # Calculate up streak
        up_streak = []
        streak = 0
        for i in range(len(self.data)):
            if pd.isna(self.data['up_day'].iloc[i]):
                streak = 0
            elif self.data['up_day'].iloc[i]:
                streak += 1
            else:
                streak = 0
            up_streak.append(streak)
        self.data['up_streak'] = up_streak
        
        # Also track down streaks for short signals
        down_streak = []
        streak = 0
        for i in range(len(self.data)):
            if pd.isna(self.data['up_day'].iloc[i]):
                streak = 0
            elif not self.data['up_day'].iloc[i]:
                streak += 1
            else:
                streak = 0
            down_streak.append(streak)
        self.data['down_streak'] = down_streak
        
        # Swing low/high for stops
        self.data['swing_low'] = self.data['low'].rolling(10).min()
        self.data['swing_high'] = self.data['high'].rolling(10).max()
    
    def generate_signals(self) -> pd.Series:
        """Generate signals."""
        signals = pd.Series(index=self.data.index, data=0)
        
        for i in range(201, len(self.data)):
            up_streak = self.data['up_streak'].iloc[i-1]  # Previous day's streak
            down_streak = self.data['down_streak'].iloc[i-1]
            above_200 = self.data['above_200'].iloc[i]
            below_200 = not above_200
            
            # Long signal: 3+ up days AND above 200 SMA
            if up_streak >= self.consecutive_days and above_200:
                signals.iloc[i] = 1
            
            # Short signal: 3+ down days AND below 200 SMA
            elif down_streak >= self.consecutive_days and below_200:
                signals.iloc[i] = -1
        
        return signals
    
    def backtest(self) -> Dict[str, Any]:
        """Run backtest."""
        signals = self.generate_signals()
        
        capital = self.initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
        bars_held = 0
        highest_price = 0
        lowest_price = float('inf')
        
        self.trades = []
        current_trade = None
        
        for i in range(len(self.data)):
            if i < 201:
                self.capital.iloc[i] = capital
                self.positions.iloc[i] = 0
                continue
            
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            atr = self.data['atr'].iloc[i]
            signal = signals.iloc[i]
            swing_low = self.data['swing_low'].iloc[i]
            swing_high = self.data['swing_high'].iloc[i]
            
            if pd.isna(atr) or atr <= 0:
                atr = close * 0.02
            
            # Manage existing position
            if position > 0:
                bars_held += 1
                highest_price = max(highest_price, high)
                
                # Trailing stop
                trail_stop = highest_price - atr * 2
                effective_stop = max(stop_loss, trail_stop)
                
                # Exit conditions
                exit_signal = False
                exit_reason = None
                
                if low <= effective_stop:
                    exit_signal = True
                    exit_price = effective_stop
                    exit_reason = 'trailing_stop'
                elif bars_held >= self.hold_days * 2:  # Max hold 10 days
                    exit_signal = True
                    exit_price = close
                    exit_reason = 'time_exit'
                elif self.data['returns'].iloc[i] < -0.02:  # Big down day
                    exit_signal = True
                    exit_price = close
                    exit_reason = 'momentum_exit'
                
                if exit_signal:
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = exit_reason
                        current_trade['pnl'] = pnl
                        current_trade['bars_held'] = bars_held
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            elif position < 0:
                bars_held += 1
                lowest_price = min(lowest_price, low)
                
                trail_stop = lowest_price + atr * 2
                effective_stop = min(stop_loss, trail_stop)
                
                exit_signal = False
                exit_reason = None
                
                if high >= effective_stop:
                    exit_signal = True
                    exit_price = effective_stop
                    exit_reason = 'trailing_stop'
                elif bars_held >= self.hold_days * 2:
                    exit_signal = True
                    exit_price = close
                    exit_reason = 'time_exit'
                elif self.data['returns'].iloc[i] > 0.02:
                    exit_signal = True
                    exit_price = close
                    exit_reason = 'momentum_exit'
                
                if exit_signal:
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = exit_reason
                        current_trade['pnl'] = pnl
                        current_trade['bars_held'] = bars_held
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            # New entry
            if position == 0 and signal != 0:
                if signal == 1:
                    stop_loss = swing_low - atr * 0.5
                    risk_per_unit = close - stop_loss
                else:
                    stop_loss = swing_high + atr * 0.5
                    risk_per_unit = stop_loss - close
                
                if risk_per_unit > 0:
                    risk_amount = capital * self.risk_per_trade
                    position_size = risk_amount / risk_per_unit
                    max_size = (capital * 0.15) / close
                    position_size = min(position_size, max_size)
                    
                    position = position_size if signal > 0 else -position_size
                    entry_price = close
                    bars_held = 0
                    highest_price = close
                    lowest_price = close
                    
                    current_trade = {
                        'entry_date': self.data.index[i],
                        'entry_price': entry_price,
                        'side': 'long' if signal > 0 else 'short',
                        'size': abs(position),
                        'stop_loss': stop_loss
                    }
            
            self.positions.iloc[i] = position
            unrealized = (close - entry_price) * position if position != 0 else 0
            self.capital.iloc[i] = capital + unrealized
        
        # Close remaining
        if position != 0:
            close = self.data['close'].iloc[-1]
            if position > 0:
                pnl = (close - entry_price) * position
            else:
                pnl = (entry_price - close) * abs(position)
            capital += pnl
            
            if current_trade:
                current_trade['exit_price'] = close
                current_trade['exit_reason'] = 'end_of_data'
                current_trade['pnl'] = pnl
                current_trade['bars_held'] = bars_held
                self.trades.append(current_trade)
        
        return self._calculate_metrics(capital)
    
    def _calculate_metrics(self, final_capital: float) -> Dict[str, Any]:
        """Calculate metrics."""
        metrics = {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'net_profit': final_capital - self.initial_capital,
            'total_return': (final_capital - self.initial_capital) / self.initial_capital,
            'total_return_pct': ((final_capital - self.initial_capital) / self.initial_capital) * 100,
            'total_trades': len(self.trades),
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'win_rate_pct': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'risk_reward_ratio': 0,
            'profit_factor': 0,
            'max_drawdown_pct': 0,
            'sharpe_ratio': 0,
            'gross_profit': 0,
            'gross_loss': 0
        }
        
        if not self.trades:
            return metrics
        
        trades_df = pd.DataFrame(self.trades)
        
        winners = trades_df[trades_df['pnl'] > 0]
        losers = trades_df[trades_df['pnl'] < 0]
        
        metrics['winning_trades'] = len(winners)
        metrics['losing_trades'] = len(losers)
        metrics['win_rate'] = len(winners) / len(trades_df)
        metrics['win_rate_pct'] = metrics['win_rate'] * 100
        
        metrics['avg_win'] = winners['pnl'].mean() if len(winners) > 0 else 0
        metrics['avg_loss'] = abs(losers['pnl'].mean()) if len(losers) > 0 else 0
        
        if metrics['avg_loss'] > 0:
            metrics['risk_reward_ratio'] = metrics['avg_win'] / metrics['avg_loss']
        
        metrics['gross_profit'] = winners['pnl'].sum() if len(winners) > 0 else 0
        metrics['gross_loss'] = abs(losers['pnl'].sum()) if len(losers) > 0 else 0
        
        if metrics['gross_loss'] > 0:
            metrics['profit_factor'] = metrics['gross_profit'] / metrics['gross_loss']
        else:
            metrics['profit_factor'] = float('inf') if metrics['gross_profit'] > 0 else 0
        
        # Drawdown
        equity = self.capital.dropna()
        if len(equity) > 0:
            rolling_max = equity.expanding().max()
            drawdown = (equity - rolling_max) / rolling_max
            metrics['max_drawdown_pct'] = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
        
        # Sharpe
        returns = equity.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            metrics['sharpe_ratio'] = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        
        return metrics
