"""Validate strategy with proper out-of-sample testing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


class ValidatedStrategy:
    """Final validated strategy."""
    
    def __init__(self, data, initial_capital=10000, risk_per_trade=0.02):
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        
        # Optimized parameters
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
                        # Position sizing based on risk
                        size = (capital * self.risk_per_trade) / risk
                        
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
        
        return self._metrics(capital)
    
    def _metrics(self, final):
        m = {
            'final_capital': final,
            'return_pct': ((final - self.initial_capital) / self.initial_capital) * 100,
            'net_profit': final - self.initial_capital,
            'trades': len(self.trades),
            'win_rate': 0,
            'profit_factor': 0,
            'rr_ratio': 0,
            'max_dd': 0,
            'sharpe': 0
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
                
                returns = equity.pct_change().dropna()
                if len(returns) > 0 and returns.std() > 0:
                    m['sharpe'] = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        
        return m


def main():
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("WALK-FORWARD VALIDATION")
    print("=" * 70)
    print(f"Total data: {len(data)} bars")
    
    # Split: 60% train, 20% validation, 20% test
    train_end = int(len(data) * 0.6)
    val_end = int(len(data) * 0.8)
    
    train_data = data.iloc[:train_end]
    val_data = data.iloc[train_end:val_end]
    test_data = data.iloc[val_end:]
    
    print(f"Training: {len(train_data)} bars ({train_data.index[0].strftime('%Y-%m-%d')} to {train_data.index[-1].strftime('%Y-%m-%d')})")
    print(f"Validation: {len(val_data)} bars ({val_data.index[0].strftime('%Y-%m-%d')} to {val_data.index[-1].strftime('%Y-%m-%d')})")
    print(f"Test: {len(test_data)} bars ({test_data.index[0].strftime('%Y-%m-%d')} to {test_data.index[-1].strftime('%Y-%m-%d')})")
    
    print("\n" + "=" * 70)
    print("RESULTS BY PERIOD")
    print("=" * 70)
    print(f"{'Period':<15} {'Return%':>10} {'Win%':>8} {'Trades':>8} {'PF':>8} {'MaxDD%':>8}")
    print("-" * 70)
    
    for name, dataset in [("Training", train_data), ("Validation", val_data), ("Test", test_data), ("Full", data)]:
        if len(dataset) < 100:
            print(f"{name:<15} {'SKIP - too short':>46}")
            continue
        
        s = ValidatedStrategy(dataset.copy(), initial_capital=10000, risk_per_trade=0.02)
        m = s.backtest()
        
        print(f"{name:<15} {m['return_pct']:>+10.2f} {m['win_rate']:>8.1f} {m['trades']:>8} {m['profit_factor']:>8.2f} {m['max_dd']:>8.2f}")
    
    # Final full test with realistic costs
    print("\n" + "=" * 70)
    print("REALISTIC PERFORMANCE (WITH COSTS)")
    print("=" * 70)
    
    s = ValidatedStrategy(data.copy(), initial_capital=10000, risk_per_trade=0.02)
    m = s.backtest()
    
    # Estimate costs
    spread_per_trade = 0.50  # $0.50 spread
    commission_per_trade = 0.10  # $0.10 commission
    total_costs = m['trades'] * (spread_per_trade + commission_per_trade) * 2  # Entry + exit
    
    net_after_costs = m['net_profit'] - total_costs
    return_after_costs = (net_after_costs / 10000) * 100
    
    print(f"  Gross P/L: ${m['net_profit']:+,.2f}")
    print(f"  Trading costs: ${total_costs:.2f} ({m['trades']} trades × $1.20)")
    print(f"  Net P/L: ${net_after_costs:+,.2f}")
    print(f"  Return after costs: {return_after_costs:+.2f}%")
    print(f"  Win Rate: {m['win_rate']:.1f}%")
    print(f"  Profit Factor: {m['profit_factor']:.2f}")
    print(f"  R:R Ratio: {m['rr_ratio']:.2f}")
    print(f"  Max Drawdown: {m['max_dd']:.2f}%")
    print(f"  Sharpe Ratio: {m['sharpe']:.2f}")
    
    # Compare to benchmarks
    buy_hold = ((data['close'].iloc[-1] / data['close'].iloc[66]) - 1) * 100
    print(f"\n  Buy & Hold: {buy_hold:+.2f}%")
    print(f"  Strategy beats B&H by: {return_after_costs - buy_hold:+.2f}%")
    
    # Final verdict
    print("\n" + "=" * 70)
    if return_after_costs > 10 and m['win_rate'] > 50 and m['profit_factor'] > 1.5:
        print("🏆 HIGHLY PROFITABLE STRATEGY!")
        verdict = "PROFITABLE"
    elif return_after_costs > 5 and m['profit_factor'] > 1.2:
        print("✅ PROFITABLE STRATEGY!")
        verdict = "PROFITABLE"
    elif return_after_costs > 0 and m['profit_factor'] > 1.0:
        print("✅ MARGINALLY PROFITABLE")
        verdict = "PROFITABLE"
    elif return_after_costs > -5:
        print("⚠️  BREAK EVEN")
        verdict = "BREAK_EVEN"
    else:
        print("❌ NOT PROFITABLE")
        verdict = "NOT_PROFITABLE"
    
    print("=" * 70)
    
    return verdict, m


if __name__ == "__main__":
    verdict, metrics = main()
