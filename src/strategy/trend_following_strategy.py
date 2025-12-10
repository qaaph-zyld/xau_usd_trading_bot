"""
Trend Following Strategy

A simple but robust trend-following strategy that:
1. Identifies the major trend using 200 SMA
2. Only trades in the direction of the trend
3. Enters on pullbacks to moving averages
4. Uses wide stops to avoid noise
5. Lets winners run with trailing stops

Philosophy: "The trend is your friend"
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import ta


class TrendFollowingStrategy:
    """
    A trend-following strategy designed for consistent profitability.
    
    Key principles:
    - Trade with the major trend (above 200 SMA = bullish)
    - Enter when price pulls back to 50 EMA
    - Exit on trend reversal or when stopped out
    """
    
    def __init__(self,
                 data: pd.DataFrame,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.02):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        
        self.positions = pd.Series(index=data.index, data=0.0)
        self.capital = pd.Series(index=data.index, data=0.0)
        self.trades = []
        
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate indicators."""
        # Moving averages
        self.data['sma_200'] = ta.trend.sma_indicator(self.data['close'], window=200)
        self.data['ema_50'] = ta.trend.ema_indicator(self.data['close'], window=50)
        self.data['ema_20'] = ta.trend.ema_indicator(self.data['close'], window=20)
        
        # ATR for stop loss sizing
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=20
        )
        
        # RSI
        self.data['rsi'] = ta.momentum.rsi(self.data['close'], window=14)
        
        # Trend filter: price relative to 200 SMA
        self.data['above_200'] = self.data['close'] > self.data['sma_200']
        self.data['below_200'] = self.data['close'] < self.data['sma_200']
        
        # Pullback detection: price touches 50 EMA
        self.data['near_ema50'] = abs(self.data['close'] - self.data['ema_50']) / self.data['close'] < 0.015
        
        # Swing low/high for stop placement
        self.data['swing_low'] = self.data['low'].rolling(10).min()
        self.data['swing_high'] = self.data['high'].rolling(10).max()
    
    def generate_signals(self) -> pd.Series:
        """Generate trading signals."""
        signals = pd.Series(index=self.data.index, data=0)
        
        for i in range(201, len(self.data)):
            close = self.data['close'].iloc[i]
            ema_50 = self.data['ema_50'].iloc[i]
            ema_20 = self.data['ema_20'].iloc[i]
            sma_200 = self.data['sma_200'].iloc[i]
            rsi = self.data['rsi'].iloc[i]
            
            # Check if EMA 20 is above EMA 50 (short-term trend confirmation)
            short_trend_up = ema_20 > ema_50
            short_trend_down = ema_20 < ema_50
            
            # LONG SIGNAL
            # Major trend up (close > 200 SMA)
            # Price pulled back to or below 50 EMA
            # Short-term trend starting to turn up
            # RSI not overbought
            if close > sma_200:  # Bullish bias
                if close <= ema_50 * 1.01:  # Near or below 50 EMA (pullback)
                    if rsi < 60:  # Not overbought
                        # Check if previous bar was lower (momentum turning)
                        if self.data['close'].iloc[i] > self.data['close'].iloc[i-1]:
                            signals.iloc[i] = 1
            
            # SHORT SIGNAL
            elif close < sma_200:  # Bearish bias
                if close >= ema_50 * 0.99:  # Near or above 50 EMA
                    if rsi > 40:  # Not oversold
                        if self.data['close'].iloc[i] < self.data['close'].iloc[i-1]:
                            signals.iloc[i] = -1
        
        return signals
    
    def backtest(self) -> Dict[str, Any]:
        """Run backtest with trend-following exits."""
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
            ema_50 = self.data['ema_50'].iloc[i]
            sma_200 = self.data['sma_200'].iloc[i]
            swing_low = self.data['swing_low'].iloc[i]
            swing_high = self.data['swing_high'].iloc[i]
            
            if pd.isna(atr) or atr <= 0:
                atr = close * 0.015
            
            # MANAGE EXISTING POSITION
            if position > 0:  # Long position
                highest_price = max(highest_price, high)
                
                # Trailing stop at 2 ATR below highest
                trail_stop = highest_price - atr * 2.5
                effective_stop = max(stop_loss, trail_stop)
                
                # Exit conditions:
                # 1. Stop loss hit
                # 2. Trend reversal (close below 200 SMA)
                exit_signal = False
                exit_reason = None
                
                if low <= effective_stop:
                    exit_signal = True
                    exit_price = effective_stop
                    exit_reason = 'trailing_stop' if trail_stop > stop_loss else 'stop_loss'
                elif close < sma_200:  # Trend reversal
                    exit_signal = True
                    exit_price = close
                    exit_reason = 'trend_reversal'
                
                if exit_signal:
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = exit_reason
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            elif position < 0:  # Short position
                lowest_price = min(lowest_price, low)
                
                # Trailing stop at 2.5 ATR above lowest
                trail_stop = lowest_price + atr * 2.5
                effective_stop = min(stop_loss, trail_stop)
                
                exit_signal = False
                exit_reason = None
                
                if high >= effective_stop:
                    exit_signal = True
                    exit_price = effective_stop
                    exit_reason = 'trailing_stop' if trail_stop < stop_loss else 'stop_loss'
                elif close > sma_200:  # Trend reversal
                    exit_signal = True
                    exit_price = close
                    exit_reason = 'trend_reversal'
                
                if exit_signal:
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    
                    if current_trade:
                        current_trade['exit_price'] = exit_price
                        current_trade['exit_reason'] = exit_reason
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    
                    position = 0
                    current_trade = None
            
            # NEW ENTRY
            if position == 0 and signal != 0:
                if signal == 1:  # Long
                    # Stop below recent swing low or 3 ATR below entry
                    stop_loss = min(swing_low - atr * 0.5, close - atr * 3)
                    risk_per_unit = close - stop_loss
                else:  # Short
                    stop_loss = max(swing_high + atr * 0.5, close + atr * 3)
                    risk_per_unit = stop_loss - close
                
                if risk_per_unit > 0:
                    risk_amount = capital * self.risk_per_trade
                    position_size = risk_amount / risk_per_unit
                    max_size = (capital * 0.15) / close  # Max 15% of capital
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
