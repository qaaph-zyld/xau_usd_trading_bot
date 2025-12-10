"""
OPTIMIZED PROP FIRM STRATEGY

Designed to maximize prop firm challenge pass rate.
Target: 30%+ pass rate for positive expected value.
"""

import pandas as pd
import numpy as np
import ta


class OptimizedPropStrategy:
    """
    Optimized strategy for prop firm challenges.
    
    Key optimizations:
    - Multiple signal types for more trades
    - Adaptive risk based on account equity
    - Trailing stops for larger winners
    - Quick exit on reversals
    """
    
    def __init__(self, data, base_risk=0.02, max_risk=0.04):
        self.data = data.copy()
        self.base_risk = base_risk
        self.max_risk = max_risk
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        # Multiple timeframe EMAs
        self.data['ema_3'] = ta.trend.ema_indicator(self.data['close'], window=3)
        self.data['ema_5'] = ta.trend.ema_indicator(self.data['close'], window=5)
        self.data['ema_8'] = ta.trend.ema_indicator(self.data['close'], window=8)
        self.data['ema_13'] = ta.trend.ema_indicator(self.data['close'], window=13)
        self.data['ema_21'] = ta.trend.ema_indicator(self.data['close'], window=21)
        
        # RSI with multiple periods
        self.data['rsi_7'] = ta.momentum.rsi(self.data['close'], window=7)
        self.data['rsi_14'] = ta.momentum.rsi(self.data['close'], window=14)
        
        # MACD
        macd = ta.trend.MACD(self.data['close'], window_slow=26, window_fast=12, window_sign=9)
        self.data['macd'] = macd.macd()
        self.data['macd_signal'] = macd.macd_signal()
        self.data['macd_hist'] = macd.macd_diff()
        
        # ATR
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=10
        )
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(self.data['close'], window=20, window_dev=2)
        self.data['bb_lower'] = bb.bollinger_lband()
        self.data['bb_upper'] = bb.bollinger_hband()
        self.data['bb_mid'] = bb.bollinger_mavg()
        
        # ADX for trend strength
        adx = ta.trend.ADXIndicator(self.data['high'], self.data['low'], self.data['close'], window=14)
        self.data['adx'] = adx.adx()
        self.data['di_plus'] = adx.adx_pos()
        self.data['di_minus'] = adx.adx_neg()
        
        # Momentum
        self.data['mom_3'] = self.data['close'].pct_change(3) * 100
        self.data['mom_5'] = self.data['close'].pct_change(5) * 100
        
        # Candlestick patterns
        self.data['body'] = self.data['close'] - self.data['open']
        self.data['range'] = self.data['high'] - self.data['low']
        self.data['body_pct'] = abs(self.data['body']) / self.data['range'].replace(0, 0.01)
    
    def get_signal_strength(self, i):
        """Calculate signal strength (0-100) for entry."""
        
        if i < 30:
            return 0, None
        
        close = self.data['close'].iloc[i]
        
        long_score = 0
        short_score = 0
        
        # EMA alignment (trend)
        ema_3 = self.data['ema_3'].iloc[i]
        ema_8 = self.data['ema_8'].iloc[i]
        ema_21 = self.data['ema_21'].iloc[i]
        
        if ema_3 > ema_8 > ema_21:
            long_score += 20
        elif ema_3 < ema_8 < ema_21:
            short_score += 20
        
        # EMA crossover
        prev_ema_3 = self.data['ema_3'].iloc[i-1]
        prev_ema_8 = self.data['ema_8'].iloc[i-1]
        
        if ema_3 > ema_8 and prev_ema_3 <= prev_ema_8:
            long_score += 25
        elif ema_3 < ema_8 and prev_ema_3 >= prev_ema_8:
            short_score += 25
        
        # RSI
        rsi = self.data['rsi_7'].iloc[i]
        if rsi < 30:
            long_score += 15
        elif rsi > 70:
            short_score += 15
        elif 40 < rsi < 60:
            # Neutral, slight trend continuation
            if long_score > short_score:
                long_score += 5
            else:
                short_score += 5
        
        # MACD
        macd = self.data['macd'].iloc[i]
        macd_sig = self.data['macd_signal'].iloc[i]
        prev_macd = self.data['macd'].iloc[i-1]
        prev_macd_sig = self.data['macd_signal'].iloc[i-1]
        
        if macd > macd_sig and prev_macd <= prev_macd_sig:
            long_score += 20
        elif macd < macd_sig and prev_macd >= prev_macd_sig:
            short_score += 20
        
        # MACD histogram direction
        macd_hist = self.data['macd_hist'].iloc[i]
        prev_hist = self.data['macd_hist'].iloc[i-1]
        
        if macd_hist > prev_hist:
            long_score += 10
        elif macd_hist < prev_hist:
            short_score += 10
        
        # ADX trend strength
        adx = self.data['adx'].iloc[i]
        di_plus = self.data['di_plus'].iloc[i]
        di_minus = self.data['di_minus'].iloc[i]
        
        if adx > 25:
            if di_plus > di_minus:
                long_score += 15
            else:
                short_score += 15
        
        # Momentum
        mom = self.data['mom_3'].iloc[i]
        if mom > 1:
            long_score += 10
        elif mom < -1:
            short_score += 10
        
        # Bollinger Band position
        bb_lower = self.data['bb_lower'].iloc[i]
        bb_upper = self.data['bb_upper'].iloc[i]
        
        if close < bb_lower:
            long_score += 10  # Oversold
        elif close > bb_upper:
            short_score += 10  # Overbought
        
        # Determine direction
        if long_score >= 50 and long_score > short_score:
            return long_score, 'LONG'
        elif short_score >= 50 and short_score > long_score:
            return short_score, 'SHORT'
        
        return 0, None
    
    def backtest_challenge(self, initial_capital=10000, 
                           profit_target=0.10, 
                           max_daily_loss=0.05,
                           max_drawdown=0.10,
                           time_limit=30):
        """Run prop firm challenge simulation."""
        
        capital = initial_capital
        start_capital = initial_capital
        highest_capital = capital
        
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        trailing_stop = 0
        position_high = 0
        
        trades = []
        daily_equity = []
        
        start_idx = 30
        end_idx = min(start_idx + time_limit, len(self.data))
        
        for i in range(start_idx, end_idx):
            day_start = capital
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            atr = self.data['atr'].iloc[i]
            
            if pd.isna(atr) or atr <= 0:
                atr = close * 0.01
            
            # Manage existing position
            if position > 0:
                position_high = max(position_high, high)
                
                # Trailing stop after 1 ATR profit
                if high > entry_price + atr:
                    new_trail = position_high - atr * 0.8
                    trailing_stop = max(trailing_stop, new_trail)
                
                effective_stop = max(stop_loss, trailing_stop)
                
                if low <= effective_stop:
                    exit_price = effective_stop
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'stop' if exit_price == stop_loss else 'trail'})
                    position = 0
                
                elif high >= take_profit:
                    exit_price = take_profit
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    position = 0
            
            elif position < 0:
                position_low = min(position_high, low) if position_high > 0 else low
                
                if low < entry_price - atr:
                    new_trail = position_low + atr * 0.8
                    trailing_stop = min(trailing_stop if trailing_stop > 0 else float('inf'), new_trail)
                
                effective_stop = min(stop_loss, trailing_stop) if trailing_stop > 0 else stop_loss
                
                if high >= effective_stop:
                    exit_price = effective_stop
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'stop' if exit_price == stop_loss else 'trail'})
                    position = 0
                
                elif low <= take_profit:
                    exit_price = take_profit
                    pnl = (entry_price - exit_price) * abs(position)
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    position = 0
            
            # Look for new entry
            if position == 0:
                strength, direction = self.get_signal_strength(i)
                
                if direction:
                    # Adaptive risk based on equity
                    equity_ratio = capital / start_capital
                    if equity_ratio > 1.05:
                        risk = self.max_risk  # Increase risk when ahead
                    elif equity_ratio < 0.95:
                        risk = self.base_risk * 0.5  # Reduce risk when behind
                    else:
                        risk = self.base_risk
                    
                    # Scale risk by signal strength
                    strength_factor = strength / 100
                    risk *= (0.5 + strength_factor * 0.5)
                    
                    if direction == 'LONG':
                        stop_loss = close - atr * 1.2
                        take_profit = close + atr * 2.5
                        risk_per_unit = close - stop_loss
                    else:
                        stop_loss = close + atr * 1.2
                        take_profit = close - atr * 2.5
                        risk_per_unit = stop_loss - close
                    
                    if risk_per_unit > 0:
                        size = (capital * risk) / risk_per_unit
                        position = size if direction == 'LONG' else -size
                        entry_price = close
                        trailing_stop = 0
                        position_high = close
            
            # Track daily equity
            unrealized = 0
            if position > 0:
                unrealized = (close - entry_price) * position
            elif position < 0:
                unrealized = (entry_price - close) * abs(position)
            
            daily_equity.append(capital + unrealized)
            
            # Update highest
            highest_capital = max(highest_capital, capital + unrealized)
            
            # Check prop firm rules
            daily_loss = (capital + unrealized) - day_start
            if daily_loss < -start_capital * max_daily_loss:
                return {
                    'passed': False,
                    'failed': True,
                    'reason': 'Daily loss',
                    'profit_pct': (capital - start_capital) / start_capital * 100,
                    'trades': len(trades),
                    'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
                    'max_dd': (highest_capital - min(daily_equity)) / start_capital * 100
                }
            
            current_dd = (highest_capital - (capital + unrealized)) / start_capital
            if current_dd > max_drawdown:
                return {
                    'passed': False,
                    'failed': True,
                    'reason': 'Max drawdown',
                    'profit_pct': (capital - start_capital) / start_capital * 100,
                    'trades': len(trades),
                    'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
                    'max_dd': current_dd * 100
                }
            
            # Check if passed
            current_profit = (capital + unrealized - start_capital) / start_capital
            if current_profit >= profit_target:
                # Close position and pass
                if position != 0:
                    if position > 0:
                        pnl = (close - entry_price) * position
                    else:
                        pnl = (entry_price - close) * abs(position)
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'pass_exit'})
                
                return {
                    'passed': True,
                    'failed': False,
                    'reason': None,
                    'profit_pct': (capital - start_capital) / start_capital * 100,
                    'trades': len(trades),
                    'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
                    'max_dd': (highest_capital - min(daily_equity)) / start_capital * 100 if daily_equity else 0,
                    'days_to_pass': i - start_idx + 1
                }
        
        # Time's up - close position
        if position != 0:
            close = self.data['close'].iloc[end_idx - 1]
            if position > 0:
                pnl = (close - entry_price) * position
            else:
                pnl = (entry_price - close) * abs(position)
            capital += pnl
            trades.append({'pnl': pnl, 'reason': 'end'})
        
        final_profit = (capital - start_capital) / start_capital
        
        return {
            'passed': final_profit >= profit_target,
            'failed': False,
            'reason': None if final_profit >= profit_target else 'Time limit',
            'profit_pct': final_profit * 100,
            'trades': len(trades),
            'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
            'max_dd': (highest_capital - min(daily_equity)) / start_capital * 100 if daily_equity else 0
        }
