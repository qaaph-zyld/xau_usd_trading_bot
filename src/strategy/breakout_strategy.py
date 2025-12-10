"""
Breakout Strategy

Simple breakout strategy with high R:R trades:
- Buy on breakout above 20-day high
- Only when above 200 SMA
- Wide stops below 20-day low
- Let winners run with loose trailing stop
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import ta


class BreakoutStrategy:
    """
    High R:R breakout strategy.
    """
    
    def __init__(self,
                 data: pd.DataFrame,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.02,
                 breakout_period: int = 20):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.breakout_period = breakout_period
        
        self.positions = pd.Series(index=data.index, data=0.0)
        self.capital = pd.Series(index=data.index, data=0.0)
        self.trades = []
        
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate indicators."""
        # Breakout levels
        self.data['high_20'] = self.data['high'].rolling(self.breakout_period).max()
        self.data['low_20'] = self.data['low'].rolling(self.breakout_period).min()
        
        # Trend filter
        self.data['sma_200'] = ta.trend.sma_indicator(self.data['close'], window=200)
        self.data['sma_50'] = ta.trend.sma_indicator(self.data['close'], window=50)
        
        # ATR
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        
        # Volume confirmation (if available)
        if 'volume' in self.data.columns:
            self.data['vol_sma'] = self.data['volume'].rolling(20).mean()
            self.data['vol_breakout'] = self.data['volume'] > self.data['vol_sma'] * 1.5
        else:
            self.data['vol_breakout'] = True
    
    def generate_signals(self) -> pd.Series:
        """Generate breakout signals."""
        signals = pd.Series(index=self.data.index, data=0)
        
        for i in range(201, len(self.data)):
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            prev_high_20 = self.data['high_20'].iloc[i-1]
            prev_low_20 = self.data['low_20'].iloc[i-1]
            sma_200 = self.data['sma_200'].iloc[i]
            sma_50 = self.data['sma_50'].iloc[i]
            
            # Long breakout: close breaks above 20-day high
            # Only when above 200 SMA and 50 SMA > 200 SMA (strong uptrend)
            if close > prev_high_20:
                if close > sma_200 and sma_50 > sma_200:
                    signals.iloc[i] = 1
            
            # Short breakout: close breaks below 20-day low
            # Only when below 200 SMA and 50 SMA < 200 SMA
            elif close < prev_low_20:
                if close < sma_200 and sma_50 < sma_200:
                    signals.iloc[i] = -1
        
        return signals
    
    def backtest(self) -> Dict[str, Any]:
        """Run backtest."""
        signals = self.generate_signals()
        
        capital = self.initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
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
            low_20 = self.data['low_20'].iloc[i]
            high_20 = self.data['high_20'].iloc[i]
            sma_200 = self.data['sma_200'].iloc[i]
            
            if pd.isna(atr) or atr <= 0:
                atr = close * 0.02
            
            # Manage long position
            if position > 0:
                highest_price = max(highest_price, high)
                
                # Very loose trailing stop: 3 ATR below highest
                trail_stop = highest_price - atr * 3
                effective_stop = max(stop_loss, trail_stop)
                
                # Exit on stop or trend reversal
                if low <= effective_stop:
                    exit_price = effective_stop
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'trailing_stop'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
                
                elif close < sma_200:  # Trend reversal
                    exit_price = close
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'trend_reversal'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            # Manage short position
            elif position < 0:
                lowest_price = min(lowest_price, low)
                
                trail_stop = lowest_price + atr * 3
                effective_stop = min(stop_loss, trail_stop)
                
                if high >= effective_stop:
                    exit_price = effective_stop
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'trailing_stop'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
                
                elif close > sma_200:
                    exit_price = close
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'trend_reversal'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            # New entry
            if position == 0 and signal != 0:
                if signal == 1:
                    # Stop below 20-day low
                    stop_loss = low_20 - atr * 0.5
                    risk_per_unit = close - stop_loss
                else:
                    stop_loss = high_20 + atr * 0.5
                    risk_per_unit = stop_loss - close
                
                if risk_per_unit > 0:
                    risk_amount = capital * self.risk_per_trade
                    position_size = risk_amount / risk_per_unit
                    max_size = (capital * 0.15) / close
                    position_size = min(position_size, max_size)
                    
                    position = position_size if signal > 0 else -position_size
                    entry_price = close
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
        
        equity = self.capital.dropna()
        if len(equity) > 0:
            rolling_max = equity.expanding().max()
            drawdown = (equity - rolling_max) / rolling_max
            metrics['max_drawdown_pct'] = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
        
        returns = equity.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            metrics['sharpe_ratio'] = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        
        return metrics
