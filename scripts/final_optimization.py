"""Final optimization - push for maximum profitability."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


class FinalStrategy:
    """Optimized strategy with best parameters."""
    
    def __init__(self, data, initial_capital=10000, risk_per_trade=0.02):
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        
        # Best parameters from optimization
        self.fast_ema = 5
        self.slow_ema = 21
        self.trend_ema = 55
        self.sl_mult = 1.5
        self.tp_mult = 3.0
        self.trail_mult = 1.5
        
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
        
        for i in range(66, len(self.data)):
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            atr = self.data['atr'].iloc[i]
            ema_trend = self.data['ema_trend'].iloc[i]
            rsi = self.data['rsi'].iloc[i]
            
            if pd.isna(atr) or atr <= 0:
                atr = close * 0.01
            
            # Position management
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
                        max_size = (capital * 0.15) / close
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
        
        if position != 0:
            close = self.data['close'].iloc[-1]
            pnl = (close - entry_price) * position if position > 0 else (entry_price - close) * abs(position)
            capital += pnl
            if current_trade:
                current_trade['exit_price'] = close
                current_trade['exit_reason'] = 'end'
                current_trade['pnl'] = pnl
                self.trades.append(current_trade)
        
        return capital


def main():
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("FINAL PROFITABILITY TEST")
    print("=" * 70)
    print(f"Data: {len(data)} bars")
    print(f"Period: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    
    buy_hold = ((data['close'].iloc[-1] / data['close'].iloc[66]) - 1) * 100
    print(f"Buy & Hold: {buy_hold:+.2f}%")
    
    # Test with different risk levels
    print("\n" + "=" * 70)
    print("RISK LEVEL COMPARISON")
    print("=" * 70)
    print(f"{'Risk%':>8} {'Return%':>10} {'Final$':>12} {'Trades':>8} {'Win%':>8} {'PF':>8} {'MaxDD%':>8}")
    print("-" * 70)
    
    best_risk = None
    best_return = -100
    
    for risk in [0.01, 0.02, 0.03, 0.04, 0.05]:
        s = FinalStrategy(data.copy(), initial_capital=10000, risk_per_trade=risk)
        final = s.backtest()
        
        ret = ((final - 10000) / 10000) * 100
        
        if s.trades:
            df = pd.DataFrame(s.trades)
            winners = df[df['pnl'] > 0]
            losers = df[df['pnl'] < 0]
            wr = len(winners) / len(df) * 100
            gp = winners['pnl'].sum() if len(winners) > 0 else 0
            gl = abs(losers['pnl'].sum()) if len(losers) > 0 else 0
            pf = gp / gl if gl > 0 else 999
            
            equity = s.capital.dropna()
            rm = equity.expanding().max()
            dd = ((equity - rm) / rm).min() * -100
        else:
            wr = 0
            pf = 0
            dd = 0
        
        print(f"{risk*100:>8.0f} {ret:>+10.2f} {final:>12,.2f} {len(s.trades):>8} {wr:>8.1f} {pf:>8.2f} {dd:>8.2f}")
        
        if ret > best_return:
            best_return = ret
            best_risk = risk
            best_strategy = s
    
    print("-" * 70)
    
    # Show best result details
    print(f"\n{'BEST RESULT':=^70}")
    print(f"  Risk per trade: {best_risk*100:.0f}%")
    print(f"  Return: {best_return:+.2f}%")
    
    if best_strategy.trades:
        df = pd.DataFrame(best_strategy.trades)
        winners = df[df['pnl'] > 0]
        losers = df[df['pnl'] < 0]
        
        print(f"  Total trades: {len(df)}")
        print(f"  Winning: {len(winners)}")
        print(f"  Losing: {len(losers)}")
        print(f"  Win rate: {len(winners)/len(df)*100:.1f}%")
        print(f"  Avg win: ${winners['pnl'].mean():.2f}")
        print(f"  Avg loss: ${abs(losers['pnl'].mean()):.2f}")
        print(f"  Largest win: ${winners['pnl'].max():.2f}")
        print(f"  Largest loss: ${abs(losers['pnl'].min()):.2f}")
        
        gp = winners['pnl'].sum()
        gl = abs(losers['pnl'].sum())
        print(f"  Gross profit: ${gp:.2f}")
        print(f"  Gross loss: ${gl:.2f}")
        print(f"  Profit factor: {gp/gl:.2f}")
        
        # Trade breakdown
        exits = df['exit_reason'].value_counts()
        print(f"\n  Exit breakdown:")
        for reason, count in exits.items():
            pnl = df[df['exit_reason'] == reason]['pnl'].sum()
            print(f"    {reason}: {count} trades, ${pnl:+,.2f}")
        
        print(f"\n  Sample trades:")
        for i, t in enumerate(best_strategy.trades[:8]):
            print(f"    {t['side']:5} ${t['entry_price']:.2f} -> ${t['exit_price']:.2f} = ${t['pnl']:+,.2f} ({t['exit_reason']})")
    
    # Final verdict
    print("\n" + "=" * 70)
    if best_return > 20 and len(best_strategy.trades) >= 20:
        print("🏆 HIGHLY PROFITABLE STRATEGY!")
    elif best_return > 10:
        print("✅ PROFITABLE STRATEGY!")
    elif best_return > 5:
        print("✅ MODERATELY PROFITABLE")
    elif best_return > 0:
        print("✅ MARGINALLY PROFITABLE (Beats 0%)")
    elif best_return > buy_hold:
        print("⚠️  LOSING BUT BEATS BUY & HOLD")
    else:
        print("❌ NOT PROFITABLE")
    
    print(f"\nStrategy returns {best_return:+.2f}% vs Buy & Hold {buy_hold:+.2f}%")
    print(f"Outperformance: {best_return - buy_hold:+.2f}%")


if __name__ == "__main__":
    main()
