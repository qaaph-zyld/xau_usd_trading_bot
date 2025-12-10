"""Optimize EMA Crossover Strategy for maximum profitability."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import product
import ta


class OptimizedEMAStrategy:
    """EMA Crossover with optimizable parameters."""
    
    def __init__(self, data, initial_capital=10000, 
                 fast_ema=8, slow_ema=21, trend_ema=55,
                 risk_per_trade=0.02, sl_mult=2.0, tp_mult=4.0, trail_mult=1.5):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.trend_ema = trend_ema
        self.risk_per_trade = risk_per_trade
        self.sl_mult = sl_mult
        self.tp_mult = tp_mult
        self.trail_mult = trail_mult
        
        self.positions = pd.Series(index=data.index, data=0.0)
        self.capital = pd.Series(index=data.index, data=0.0)
        self.trades = []
        
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        self.data['ema_fast'] = ta.trend.ema_indicator(self.data['close'], window=self.fast_ema)
        self.data['ema_slow'] = ta.trend.ema_indicator(self.data['close'], window=self.slow_ema)
        self.data['ema_trend'] = ta.trend.ema_indicator(self.data['close'], window=self.trend_ema)
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        self.data['rsi'] = ta.momentum.rsi(self.data['close'], window=14)
        
        self.data['cross_up'] = (
            (self.data['ema_fast'] > self.data['ema_slow']) & 
            (self.data['ema_fast'].shift(1) <= self.data['ema_slow'].shift(1))
        )
        self.data['cross_down'] = (
            (self.data['ema_fast'] < self.data['ema_slow']) &
            (self.data['ema_fast'].shift(1) >= self.data['ema_slow'].shift(1))
        )
    
    def backtest(self):
        capital = self.initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        highest = 0
        lowest = float('inf')
        
        self.trades = []
        current_trade = None
        
        min_idx = max(60, self.trend_ema + 10)
        
        for i in range(len(self.data)):
            if i < min_idx:
                self.capital.iloc[i] = capital
                self.positions.iloc[i] = 0
                continue
            
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            atr = self.data['atr'].iloc[i]
            ema_trend = self.data['ema_trend'].iloc[i]
            rsi = self.data['rsi'].iloc[i]
            
            if pd.isna(atr) or atr <= 0:
                atr = close * 0.01
            
            # Long position management
            if position > 0:
                highest = max(highest, high)
                trail = highest - atr * self.trail_mult
                eff_stop = max(stop_loss, trail)
                
                if low <= eff_stop:
                    pnl = (eff_stop - entry_price) * position
                    capital += pnl
                    if current_trade:
                        current_trade['exit_price'] = eff_stop
                        current_trade['exit_reason'] = 'stop'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    position = 0
                    current_trade = None
                elif high >= take_profit:
                    pnl = (take_profit - entry_price) * position
                    capital += pnl
                    if current_trade:
                        current_trade['exit_price'] = take_profit
                        current_trade['exit_reason'] = 'take_profit'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    position = 0
                    current_trade = None
                elif self.data['cross_down'].iloc[i]:
                    pnl = (close - entry_price) * position
                    capital += pnl
                    if current_trade:
                        current_trade['exit_price'] = close
                        current_trade['exit_reason'] = 'signal'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    position = 0
                    current_trade = None
            
            # Short position management
            elif position < 0:
                lowest = min(lowest, low)
                trail = lowest + atr * self.trail_mult
                eff_stop = min(stop_loss, trail)
                
                if high >= eff_stop:
                    pnl = (entry_price - eff_stop) * abs(position)
                    capital += pnl
                    if current_trade:
                        current_trade['exit_price'] = eff_stop
                        current_trade['exit_reason'] = 'stop'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    position = 0
                    current_trade = None
                elif low <= take_profit:
                    pnl = (entry_price - take_profit) * abs(position)
                    capital += pnl
                    if current_trade:
                        current_trade['exit_price'] = take_profit
                        current_trade['exit_reason'] = 'take_profit'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    position = 0
                    current_trade = None
                elif self.data['cross_up'].iloc[i]:
                    pnl = (entry_price - close) * abs(position)
                    capital += pnl
                    if current_trade:
                        current_trade['exit_price'] = close
                        current_trade['exit_reason'] = 'signal'
                        current_trade['pnl'] = pnl
                        self.trades.append(current_trade)
                    position = 0
                    current_trade = None
            
            # Entry
            if position == 0:
                signal = 0
                if self.data['cross_up'].iloc[i] and close > ema_trend and rsi < 70:
                    signal = 1
                elif self.data['cross_down'].iloc[i] and close < ema_trend and rsi > 30:
                    signal = -1
                
                if signal != 0:
                    if signal == 1:
                        stop_loss = close - atr * self.sl_mult
                        take_profit = close + atr * self.tp_mult
                        risk = close - stop_loss
                    else:
                        stop_loss = close + atr * self.sl_mult
                        take_profit = close - atr * self.tp_mult
                        risk = stop_loss - close
                    
                    if risk > 0:
                        size = (capital * self.risk_per_trade) / risk
                        max_size = (capital * 0.1) / close
                        size = min(size, max_size)
                        
                        position = size if signal > 0 else -size
                        entry_price = close
                        highest = close
                        lowest = close
                        
                        current_trade = {
                            'entry_date': self.data.index[i],
                            'entry_price': entry_price,
                            'side': 'long' if signal > 0 else 'short',
                            'size': abs(position)
                        }
            
            self.positions.iloc[i] = position
            unrealized = (close - entry_price) * position if position != 0 else 0
            self.capital.iloc[i] = capital + unrealized
        
        # Close remaining
        if position != 0:
            close = self.data['close'].iloc[-1]
            pnl = (close - entry_price) * position if position > 0 else (entry_price - close) * abs(position)
            capital += pnl
            if current_trade:
                current_trade['exit_price'] = close
                current_trade['exit_reason'] = 'end'
                current_trade['pnl'] = pnl
                self.trades.append(current_trade)
        
        return self._metrics(capital)
    
    def _metrics(self, final):
        m = {
            'return_pct': ((final - self.initial_capital) / self.initial_capital) * 100,
            'trades': len(self.trades),
            'win_rate': 0,
            'profit_factor': 0,
            'rr_ratio': 0,
            'max_dd': 0
        }
        
        if self.trades:
            df = pd.DataFrame(self.trades)
            winners = df[df['pnl'] > 0]
            losers = df[df['pnl'] < 0]
            m['win_rate'] = len(winners) / len(df) * 100
            m['avg_win'] = winners['pnl'].mean() if len(winners) > 0 else 0
            m['avg_loss'] = abs(losers['pnl'].mean()) if len(losers) > 0 else 0
            if m['avg_loss'] > 0:
                m['rr_ratio'] = m['avg_win'] / m['avg_loss']
            gp = winners['pnl'].sum() if len(winners) > 0 else 0
            gl = abs(losers['pnl'].sum()) if len(losers) > 0 else 0
            if gl > 0:
                m['profit_factor'] = gp / gl
            
            equity = self.capital.dropna()
            if len(equity) > 0:
                rm = equity.expanding().max()
                dd = (equity - rm) / rm
                m['max_dd'] = abs(dd.min()) * 100
        
        return m


def main():
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("EMA CROSSOVER OPTIMIZATION")
    print("=" * 70)
    
    # Parameter grid
    fast_emas = [5, 8, 10, 12]
    slow_emas = [15, 21, 26, 30]
    trend_emas = [50, 55, 100]
    sl_mults = [1.5, 2.0, 2.5]
    tp_mults = [3.0, 4.0, 5.0]
    trail_mults = [1.0, 1.5, 2.0]
    
    results = []
    total = len(fast_emas) * len(slow_emas) * len(trend_emas) * len(sl_mults) * len(tp_mults) * len(trail_mults)
    print(f"Testing {total} combinations...")
    
    for fast, slow, trend, sl, tp, trail in product(fast_emas, slow_emas, trend_emas, sl_mults, tp_mults, trail_mults):
        if fast >= slow:
            continue
        
        try:
            s = OptimizedEMAStrategy(data, fast_ema=fast, slow_ema=slow, trend_ema=trend,
                                     sl_mult=sl, tp_mult=tp, trail_mult=trail)
            m = s.backtest()
            
            if m['trades'] >= 10:  # Minimum trades
                results.append({
                    'fast': fast, 'slow': slow, 'trend': trend,
                    'sl': sl, 'tp': tp, 'trail': trail,
                    **m
                })
        except:
            pass
    
    if not results:
        print("No valid results!")
        return
    
    df = pd.DataFrame(results)
    df = df.sort_values('return_pct', ascending=False)
    
    print(f"\n{'TOP 10 PARAMETER COMBINATIONS':=^70}")
    print("-" * 70)
    print(f"{'Fast':>5} {'Slow':>5} {'Trend':>6} {'SL':>4} {'TP':>4} {'Trail':>6} {'Ret%':>8} {'Win%':>6} {'PF':>6} {'Trades':>7}")
    print("-" * 70)
    
    for _, r in df.head(10).iterrows():
        print(f"{r['fast']:>5} {r['slow']:>5} {r['trend']:>6} {r['sl']:>4.1f} {r['tp']:>4.1f} "
              f"{r['trail']:>6.1f} {r['return_pct']:>+8.2f} {r['win_rate']:>6.1f} {r['profit_factor']:>6.2f} {r['trades']:>7}")
    
    # Best
    best = df.iloc[0]
    print(f"\n{'BEST PARAMETERS':=^70}")
    print(f"  Fast EMA: {best['fast']}")
    print(f"  Slow EMA: {best['slow']}")
    print(f"  Trend EMA: {best['trend']}")
    print(f"  Stop Loss: {best['sl']}x ATR")
    print(f"  Take Profit: {best['tp']}x ATR")
    print(f"  Trailing Stop: {best['trail']}x ATR")
    print(f"\n  Return: {best['return_pct']:+.2f}%")
    print(f"  Win Rate: {best['win_rate']:.1f}%")
    print(f"  Profit Factor: {best['profit_factor']:.2f}")
    print(f"  R:R Ratio: {best['rr_ratio']:.2f}")
    print(f"  Max Drawdown: {best['max_dd']:.2f}%")
    
    # Verdict
    print("\n" + "=" * 70)
    if best['return_pct'] > 10 and best['win_rate'] > 50:
        print("🏆 PROFITABLE STRATEGY FOUND!")
    elif best['return_pct'] > 5:
        print("✅ MODERATELY PROFITABLE")
    elif best['return_pct'] > 0:
        print("⚠️  MARGINALLY PROFITABLE")
    else:
        print("❌ NOT PROFITABLE")
    
    return best


if __name__ == "__main__":
    best = main()
