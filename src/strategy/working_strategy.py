"""
Working Trend-Following Strategy

A practical strategy that actually generates trades with:
1. EMA crossover for entries
2. Trend filter for direction
3. ATR-based stops and targets
4. Trailing stop for profits
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import ta
import logging

logger = logging.getLogger(__name__)


class WorkingStrategy:
    """
    A trend-following strategy that actually works.
    
    Entry: EMA 8/21 crossover in direction of EMA 55 trend
    Exit: ATR-based stop loss and take profit with trailing stop
    """
    
    def __init__(self,
                 data: pd.DataFrame,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.02,
                 sl_atr_mult: float = 2.0,
                 tp_atr_mult: float = 4.0,
                 trail_atr_mult: float = 1.5):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.sl_atr_mult = sl_atr_mult
        self.tp_atr_mult = tp_atr_mult
        self.trail_atr_mult = trail_atr_mult
        
        self.positions = pd.Series(index=data.index, data=0.0)
        self.capital = pd.Series(index=data.index, data=0.0)
        self.trades = []
        
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate indicators."""
        self.data['ema_8'] = ta.trend.ema_indicator(self.data['close'], window=8)
        self.data['ema_21'] = ta.trend.ema_indicator(self.data['close'], window=21)
        self.data['ema_55'] = ta.trend.ema_indicator(self.data['close'], window=55)
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        self.data['rsi'] = ta.momentum.rsi(self.data['close'], window=14)
        
        # EMA crossovers
        self.data['ema_cross_up'] = (
            (self.data['ema_8'] > self.data['ema_21']) & 
            (self.data['ema_8'].shift(1) <= self.data['ema_21'].shift(1))
        )
        self.data['ema_cross_down'] = (
            (self.data['ema_8'] < self.data['ema_21']) &
            (self.data['ema_8'].shift(1) >= self.data['ema_21'].shift(1))
        )
    
    def generate_signals(self) -> pd.Series:
        """Generate trading signals."""
        signals = pd.Series(index=self.data.index, data=0)
        
        for i in range(60, len(self.data)):
            close = self.data['close'].iloc[i]
            ema_55 = self.data['ema_55'].iloc[i]
            rsi = self.data['rsi'].iloc[i]
            
            # Long: EMA cross up + price above EMA 55 + RSI not overbought
            if self.data['ema_cross_up'].iloc[i]:
                if close > ema_55 and rsi < 70:
                    signals.iloc[i] = 1
            
            # Short: EMA cross down + price below EMA 55 + RSI not oversold
            if self.data['ema_cross_down'].iloc[i]:
                if close < ema_55 and rsi > 30:
                    signals.iloc[i] = -1
        
        return signals
    
    def backtest(self) -> Dict[str, Any]:
        """Run backtest."""
        signals = self.generate_signals()
        
        capital = self.initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        highest_price = 0
        lowest_price = float('inf')
        
        self.trades = []
        current_trade = None
        
        for i in range(len(self.data)):
            if i < 60:
                self.capital.iloc[i] = capital
                self.positions.iloc[i] = 0
                continue
            
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            atr = self.data['atr'].iloc[i]
            signal = signals.iloc[i]
            
            if pd.isna(atr) or atr <= 0:
                atr = close * 0.01
            
            # Manage existing position
            if position > 0:  # Long
                highest_price = max(highest_price, high)
                
                # Calculate trailing stop
                trail_stop = highest_price - atr * self.trail_atr_mult
                effective_stop = max(stop_loss, trail_stop)
                
                # Check stop
                if low <= effective_stop:
                    exit_price = effective_stop
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'stop_loss'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
                
                # Check take profit
                elif high >= take_profit:
                    exit_price = take_profit
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'take_profit'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
                
                # Check signal reversal
                elif signal == -1:
                    exit_price = close
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'signal_reversal'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            elif position < 0:  # Short
                lowest_price = min(lowest_price, low)
                
                # Trailing stop
                trail_stop = lowest_price + atr * self.trail_atr_mult
                effective_stop = min(stop_loss, trail_stop)
                
                # Check stop
                if high >= effective_stop:
                    exit_price = effective_stop
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'stop_loss'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
                
                # Check take profit
                elif low <= take_profit:
                    exit_price = take_profit
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'take_profit'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
                
                # Signal reversal
                elif signal == 1:
                    exit_price = close
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = 'signal_reversal'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            # New entry
            if position == 0 and signal != 0:
                risk_amount = capital * self.risk_per_trade
                
                if signal == 1:  # Long
                    stop_loss = close - atr * self.sl_atr_mult
                    take_profit = close + atr * self.tp_atr_mult
                    risk_per_unit = close - stop_loss
                else:  # Short
                    stop_loss = close + atr * self.sl_atr_mult
                    take_profit = close - atr * self.tp_atr_mult
                    risk_per_unit = stop_loss - close
                
                if risk_per_unit > 0:
                    position_size = risk_amount / risk_per_unit
                    max_size = (capital * 0.1) / close
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
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
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
