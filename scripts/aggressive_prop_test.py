"""
AGGRESSIVE PROP FIRM TEST

Use high risk to hit 10% target in 30 days.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


def aggressive_backtest(data, risk_pct=0.05, atr_sl=1.0, atr_tp=2.0):
    """
    Ultra-aggressive strategy for prop firm.
    Higher risk, tighter stops, multiple signals.
    """
    
    df = data.copy()
    
    # Fast indicators
    df['ema_3'] = ta.trend.ema_indicator(df['close'], window=3)
    df['ema_8'] = ta.trend.ema_indicator(df['close'], window=8)
    df['ema_21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['rsi'] = ta.momentum.rsi(df['close'], window=5)  # Fast RSI
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=10)
    
    # MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_sig'] = macd.macd_signal()
    
    capital = 10000
    start = capital
    highest = capital
    position = 0
    entry = 0
    sl = 0
    tp = 0
    trail = 0
    
    trades = []
    
    for i in range(25, min(55, len(df))):  # 30 day window
        close = df['close'].iloc[i]
        high = df['high'].iloc[i]
        low = df['low'].iloc[i]
        atr = df['atr'].iloc[i] if not pd.isna(df['atr'].iloc[i]) else close * 0.01
        
        # Manage position
        if position > 0:
            # Trailing stop
            if high > entry + atr:
                trail = max(trail, high - atr * 0.5)
            eff_sl = max(sl, trail)
            
            if low <= eff_sl:
                pnl = (eff_sl - entry) * position
                capital += pnl
                trades.append(pnl)
                position = 0
            elif high >= tp:
                pnl = (tp - entry) * position
                capital += pnl
                trades.append(pnl)
                position = 0
        
        elif position < 0:
            if low < entry - atr:
                trail = min(trail if trail > 0 else 99999, low + atr * 0.5)
            eff_sl = min(sl, trail) if trail > 0 else sl
            
            if high >= eff_sl:
                pnl = (entry - eff_sl) * abs(position)
                capital += pnl
                trades.append(pnl)
                position = 0
            elif low <= tp:
                pnl = (entry - tp) * abs(position)
                capital += pnl
                trades.append(pnl)
                position = 0
        
        # New entry - multiple signal types
        if position == 0:
            ema3 = df['ema_3'].iloc[i]
            ema8 = df['ema_8'].iloc[i]
            ema21 = df['ema_21'].iloc[i]
            rsi = df['rsi'].iloc[i]
            macd_val = df['macd'].iloc[i]
            macd_sig_val = df['macd_sig'].iloc[i]
            
            prev_ema3 = df['ema_3'].iloc[i-1]
            prev_ema8 = df['ema_8'].iloc[i-1]
            prev_macd = df['macd'].iloc[i-1]
            prev_macd_sig = df['macd_sig'].iloc[i-1]
            
            long = False
            short = False
            
            # Signal 1: EMA crossover
            if ema3 > ema8 and prev_ema3 <= prev_ema8:
                long = True
            elif ema3 < ema8 and prev_ema3 >= prev_ema8:
                short = True
            
            # Signal 2: MACD crossover
            if macd_val > macd_sig_val and prev_macd <= prev_macd_sig:
                long = True
            elif macd_val < macd_sig_val and prev_macd >= prev_macd_sig:
                short = True
            
            # Signal 3: RSI extremes with reversal
            if rsi < 20 and close > df['close'].iloc[i-1]:
                long = True
            elif rsi > 80 and close < df['close'].iloc[i-1]:
                short = True
            
            if long:
                sl = close - atr * atr_sl
                tp = close + atr * atr_tp
                risk = close - sl
                size = (capital * risk_pct) / risk
                position = size
                entry = close
                trail = 0
            
            elif short:
                sl = close + atr * atr_sl
                tp = close - atr * atr_tp
                risk = sl - close
                size = (capital * risk_pct) / risk
                position = -size
                entry = close
                trail = 99999
        
        highest = max(highest, capital)
        
        # Check drawdown limit
        if highest - capital > start * 0.10:
            return {'passed': False, 'failed': True, 'reason': 'DD', 
                    'profit': (capital - start) / start * 100, 'trades': len(trades)}
        
        # Check if passed
        if capital >= start * 1.10:
            return {'passed': True, 'failed': False, 'reason': None,
                    'profit': (capital - start) / start * 100, 'trades': len(trades),
                    'days': i - 25 + 1}
    
    # Close position at end
    if position != 0:
        close = df['close'].iloc[min(54, len(df)-1)]
        if position > 0:
            pnl = (close - entry) * position
        else:
            pnl = (entry - close) * abs(position)
        capital += pnl
        trades.append(pnl)
    
    return {'passed': capital >= start * 1.10, 'failed': False,
            'reason': 'TIME' if capital < start * 1.10 else None,
            'profit': (capital - start) / start * 100, 'trades': len(trades),
            'win_rate': len([t for t in trades if t > 0]) / len(trades) * 100 if trades else 0}


def main():
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("🔥 AGGRESSIVE PROP FIRM OPTIMIZATION")
    print("=" * 70)
    
    # Test different parameter combinations
    print("\nTesting parameter combinations...")
    print(f"{'Risk%':>6} {'SL':>5} {'TP':>5} {'Pass%':>8} {'AvgProfit':>10}")
    print("-" * 45)
    
    best_params = None
    best_pass_rate = 0
    
    for risk in [0.04, 0.05, 0.06, 0.08]:
        for sl in [0.8, 1.0, 1.2]:
            for tp in [1.5, 2.0, 2.5, 3.0]:
                results = []
                
                for start in range(80, len(data) - 60, 15):
                    window = data.iloc[start:start+60]
                    if len(window) < 55:
                        continue
                    
                    result = aggressive_backtest(window, risk_pct=risk, atr_sl=sl, atr_tp=tp)
                    results.append(result)
                
                if results:
                    passed = len([r for r in results if r['passed']])
                    pass_rate = passed / len(results) * 100
                    avg_profit = np.mean([r['profit'] for r in results])
                    
                    if pass_rate > best_pass_rate:
                        best_pass_rate = pass_rate
                        best_params = (risk, sl, tp)
                        print(f"{risk*100:>6.0f} {sl:>5.1f} {tp:>5.1f} {pass_rate:>8.1f} {avg_profit:>+10.2f} *** NEW BEST")
    
    print("-" * 45)
    
    if best_params:
        risk, sl, tp = best_params
        print(f"\nBest: Risk={risk*100:.0f}%, SL={sl:.1f}×ATR, TP={tp:.1f}×ATR")
        print(f"Pass Rate: {best_pass_rate:.1f}%")
        
        # Full test with best params
        print("\n" + "=" * 70)
        print("FULL TEST WITH BEST PARAMETERS")
        print("=" * 70)
        print(f"{'Start':<12} {'Profit%':>10} {'Trades':>8} {'Status'}")
        print("-" * 50)
        
        all_results = []
        for start in range(80, len(data) - 60, 10):
            window = data.iloc[start:start+60]
            if len(window) < 55:
                continue
            
            result = aggressive_backtest(window, risk_pct=risk, atr_sl=sl, atr_tp=tp)
            result['date'] = data.index[start].strftime('%Y-%m-%d')
            all_results.append(result)
            
            status = "✅ PASS" if result['passed'] else ("❌ FAIL" if result['failed'] else "⏳ TIME")
            print(f"{result['date']:<12} {result['profit']:>+10.2f} {result['trades']:>8} {status}")
        
        print("-" * 50)
        
        passed = len([r for r in all_results if r['passed']])
        failed = len([r for r in all_results if r['failed']])
        total = len(all_results)
        final_pass_rate = passed / total * 100
        
        print(f"\n📊 RESULTS")
        print(f"   Passed: {passed}/{total} ({final_pass_rate:.1f}%)")
        print(f"   Failed: {failed}/{total}")
        
        # EV Calculation
        print("\n" + "=" * 70)
        print("💰 EXPECTED VALUE")
        print("=" * 70)
        
        challenge_cost = 100
        if_pass_profit = 800  # 80% of 10% of $10K
        
        ev = (final_pass_rate / 100) * if_pass_profit - ((100 - final_pass_rate) / 100) * challenge_cost
        
        print(f"""
    Pass rate:      {final_pass_rate:.1f}%
    Challenge cost: ${challenge_cost}
    Win payout:     ${if_pass_profit}
    
    EXPECTED VALUE: ${ev:+.2f}
    """)
        
        if ev > 0:
            print("    ✅ POSITIVE EXPECTED VALUE!")
            print(f"    💵 Over 10 attempts: ${ev * 10:+.2f} expected")
            print("\n    RECOMMENDATION: Proceed with prop firm challenge!")
        else:
            breakeven = challenge_cost / (if_pass_profit + challenge_cost) * 100
            print(f"    ⚠️  Need {breakeven:.0f}% pass rate for break-even")
    
    else:
        print("\nNo profitable configuration found.")


if __name__ == "__main__":
    main()
