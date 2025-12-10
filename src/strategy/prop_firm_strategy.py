"""
PROP FIRM AGGRESSIVE STRATEGY

Designed specifically for prop firm challenges:
- Higher win rate targeting
- More aggressive entries
- Faster signals
- Higher risk per trade (within prop firm limits)
"""

import pandas as pd
import numpy as np
import ta


class PropFirmStrategy:
    """
    Aggressive strategy for prop firm challenges.
    
    Key differences from conservative strategy:
    - Faster EMAs for quicker signals
    - RSI extremes for additional entries
    - MACD crossovers
    - Higher risk per trade (3-5%)
    """
    
    def __init__(self, data, risk_per_trade=0.03):
        self.data = data.copy()
        self.risk_per_trade = risk_per_trade
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        # Fast EMAs for quick signals
        self.data['ema_3'] = ta.trend.ema_indicator(self.data['close'], window=3)
        self.data['ema_8'] = ta.trend.ema_indicator(self.data['close'], window=8)
        self.data['ema_21'] = ta.trend.ema_indicator(self.data['close'], window=21)
        
        # RSI for oversold/overbought
        self.data['rsi'] = ta.momentum.rsi(self.data['close'], window=7)  # Faster RSI
        
        # MACD
        macd = ta.trend.MACD(self.data['close'], window_slow=26, window_fast=12, window_sign=9)
        self.data['macd'] = macd.macd()
        self.data['macd_signal'] = macd.macd_signal()
        
        # ATR for stops
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=10
        )
        
        # Bollinger Bands for mean reversion
        bb = ta.volatility.BollingerBands(self.data['close'], window=20, window_dev=2)
        self.data['bb_lower'] = bb.bollinger_lband()
        self.data['bb_upper'] = bb.bollinger_hband()
        
        # Signal conditions
        # EMA crossovers
        self.data['ema_cross_up'] = (
            (self.data['ema_3'] > self.data['ema_8']) & 
            (self.data['ema_3'].shift(1) <= self.data['ema_8'].shift(1))
        )
        self.data['ema_cross_down'] = (
            (self.data['ema_3'] < self.data['ema_8']) &
            (self.data['ema_3'].shift(1) >= self.data['ema_8'].shift(1))
        )
        
        # MACD crossovers
        self.data['macd_cross_up'] = (
            (self.data['macd'] > self.data['macd_signal']) &
            (self.data['macd'].shift(1) <= self.data['macd_signal'].shift(1))
        )
        self.data['macd_cross_down'] = (
            (self.data['macd'] < self.data['macd_signal']) &
            (self.data['macd'].shift(1) >= self.data['macd_signal'].shift(1))
        )
        
        # RSI extremes
        self.data['rsi_oversold'] = self.data['rsi'] < 25
        self.data['rsi_overbought'] = self.data['rsi'] > 75
        
        # BB touches
        self.data['bb_lower_touch'] = self.data['low'] <= self.data['bb_lower']
        self.data['bb_upper_touch'] = self.data['high'] >= self.data['bb_upper']
    
    def get_signals(self, start_idx=30):
        """Generate trading signals."""
        signals = []
        
        for i in range(start_idx, len(self.data)):
            close = self.data['close'].iloc[i]
            atr = self.data['atr'].iloc[i]
            ema_21 = self.data['ema_21'].iloc[i]
            
            if pd.isna(atr):
                continue
            
            # LONG signals
            long_signal = False
            
            # Signal 1: EMA crossover + price above EMA 21
            if self.data['ema_cross_up'].iloc[i] and close > ema_21:
                long_signal = True
            
            # Signal 2: RSI oversold bounce
            if self.data['rsi_oversold'].iloc[i-1] and self.data['rsi'].iloc[i] > 30:
                if close > ema_21:
                    long_signal = True
            
            # Signal 3: MACD crossover + trend
            if self.data['macd_cross_up'].iloc[i] and close > ema_21:
                long_signal = True
            
            # Signal 4: BB lower touch reversal
            if self.data['bb_lower_touch'].iloc[i] and close > ema_21:
                if self.data['close'].iloc[i] > self.data['open'].iloc[i]:  # Bullish candle
                    long_signal = True
            
            # SHORT signals
            short_signal = False
            
            if self.data['ema_cross_down'].iloc[i] and close < ema_21:
                short_signal = True
            
            if self.data['rsi_overbought'].iloc[i-1] and self.data['rsi'].iloc[i] < 70:
                if close < ema_21:
                    short_signal = True
            
            if self.data['macd_cross_down'].iloc[i] and close < ema_21:
                short_signal = True
            
            if self.data['bb_upper_touch'].iloc[i] and close < ema_21:
                if self.data['close'].iloc[i] < self.data['open'].iloc[i]:  # Bearish candle
                    short_signal = True
            
            if long_signal:
                signals.append({
                    'idx': i,
                    'date': self.data.index[i],
                    'direction': 'LONG',
                    'entry': close,
                    'stop_loss': close - atr * 1.0,  # Tighter stop for aggressive
                    'take_profit': close + atr * 2.0,  # 2:1 R:R
                    'atr': atr
                })
            elif short_signal:
                signals.append({
                    'idx': i,
                    'date': self.data.index[i],
                    'direction': 'SHORT',
                    'entry': close,
                    'stop_loss': close + atr * 1.0,
                    'take_profit': close - atr * 2.0,
                    'atr': atr
                })
        
        return signals
    
    def backtest(self, initial_capital=10000, max_daily_loss=0.05, max_drawdown=0.10):
        """Backtest with prop firm rules."""
        
        signals = self.get_signals()
        
        capital = initial_capital
        highest_capital = capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        
        trades = []
        daily_pnl = {}
        
        signal_idx = 0
        
        for i in range(30, len(self.data)):
            date = self.data.index[i].strftime('%Y-%m-%d')
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            
            day_start = capital
            
            # Manage position
            if position > 0:
                if low <= stop_loss:
                    pnl = (stop_loss - entry_price) * position
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'stop'})
                    position = 0
                elif high >= take_profit:
                    pnl = (take_profit - entry_price) * position
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    position = 0
            
            elif position < 0:
                if high >= stop_loss:
                    pnl = (entry_price - stop_loss) * abs(position)
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'stop'})
                    position = 0
                elif low <= take_profit:
                    pnl = (entry_price - take_profit) * abs(position)
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    position = 0
            
            # Check for new signal
            if position == 0 and signal_idx < len(signals):
                sig = signals[signal_idx]
                if sig['idx'] == i:
                    risk = abs(sig['entry'] - sig['stop_loss'])
                    if risk > 0:
                        size = (capital * self.risk_per_trade) / risk
                        position = size if sig['direction'] == 'LONG' else -size
                        entry_price = sig['entry']
                        stop_loss = sig['stop_loss']
                        take_profit = sig['take_profit']
                    signal_idx += 1
            
            # Skip used signals
            while signal_idx < len(signals) and signals[signal_idx]['idx'] <= i:
                signal_idx += 1
            
            # Daily P/L tracking
            daily_pnl[date] = capital - day_start
            
            # Update highest
            highest_capital = max(highest_capital, capital)
            
            # Check prop firm rules
            if capital - day_start < -initial_capital * max_daily_loss:
                return {
                    'passed': False,
                    'failed': True,
                    'reason': 'Daily loss limit',
                    'trades': len(trades),
                    'profit_pct': (capital - initial_capital) / initial_capital * 100,
                    'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
                    'max_dd': (highest_capital - capital) / initial_capital * 100
                }
            
            if highest_capital - capital > initial_capital * max_drawdown:
                return {
                    'passed': False,
                    'failed': True,
                    'reason': 'Max drawdown',
                    'trades': len(trades),
                    'profit_pct': (capital - initial_capital) / initial_capital * 100,
                    'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
                    'max_dd': (highest_capital - capital) / initial_capital * 100
                }
        
        # Close remaining
        if position != 0:
            close = self.data['close'].iloc[-1]
            if position > 0:
                pnl = (close - entry_price) * position
            else:
                pnl = (entry_price - close) * abs(position)
            capital += pnl
            trades.append({'pnl': pnl, 'reason': 'end'})
        
        profit_pct = (capital - initial_capital) / initial_capital * 100
        
        return {
            'passed': profit_pct >= 10,
            'failed': False,
            'reason': None,
            'final_capital': capital,
            'profit_pct': profit_pct,
            'trades': len(trades),
            'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
            'max_dd': (highest_capital - min(capital, *[initial_capital + sum(t['pnl'] for t in trades[:j+1]) 
                                                        for j in range(len(trades))])) / initial_capital * 100 if trades else 0
        }
