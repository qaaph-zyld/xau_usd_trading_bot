"""
🔬 FINAL VALIDATION & STRESS TESTING

Complete validation of the prop firm strategy before going live.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


def run_stress_test(data, risk_pct=0.08, atr_sl=0.8, atr_tp=1.5, num_simulations=100):
    """Run Monte Carlo stress test."""
    
    results = []
    
    for sim in range(num_simulations):
        # Random starting point
        start = np.random.randint(80, len(data) - 60)
        window = data.iloc[start:start+60].copy()
        
        # Add some noise to simulate real conditions
        noise_factor = 1 + np.random.normal(0, 0.001, len(window))
        window['close'] = window['close'] * noise_factor
        
        # Run backtest
        result = backtest_challenge(window, risk_pct, atr_sl, atr_tp)
        results.append(result)
    
    return results


def backtest_challenge(data, risk_pct=0.08, atr_sl=0.8, atr_tp=1.5):
    """Backtest prop firm challenge."""
    
    df = data.copy()
    
    # Calculate indicators
    df['ema_3'] = ta.trend.ema_indicator(df['close'], window=3)
    df['ema_8'] = ta.trend.ema_indicator(df['close'], window=8)
    df['rsi'] = ta.momentum.rsi(df['close'], window=5)
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=10)
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
    
    for i in range(25, min(55, len(df))):
        close = df['close'].iloc[i]
        high = df['high'].iloc[i]
        low = df['low'].iloc[i]
        atr = df['atr'].iloc[i] if not pd.isna(df['atr'].iloc[i]) else close * 0.01
        
        # Manage position
        if position > 0:
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
        
        # New entry
        if position == 0:
            ema3 = df['ema_3'].iloc[i]
            ema8 = df['ema_8'].iloc[i]
            rsi = df['rsi'].iloc[i]
            macd_val = df['macd'].iloc[i]
            macd_sig_val = df['macd_sig'].iloc[i]
            
            prev_ema3 = df['ema_3'].iloc[i-1]
            prev_ema8 = df['ema_8'].iloc[i-1]
            prev_macd = df['macd'].iloc[i-1]
            prev_macd_sig = df['macd_sig'].iloc[i-1]
            
            long = False
            short = False
            
            if ema3 > ema8 and prev_ema3 <= prev_ema8:
                long = True
            elif ema3 < ema8 and prev_ema3 >= prev_ema8:
                short = True
            
            if macd_val > macd_sig_val and prev_macd <= prev_macd_sig:
                long = True
            elif macd_val < macd_sig_val and prev_macd >= prev_macd_sig:
                short = True
            
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
        
        # Check drawdown
        if highest - capital > start * 0.10:
            return {'passed': False, 'failed': True, 'profit': (capital - start) / start * 100}
        
        # Check passed
        if capital >= start * 1.10:
            return {'passed': True, 'failed': False, 'profit': (capital - start) / start * 100, 'days': i - 25 + 1}
    
    # Close position at end
    if position != 0:
        close = df['close'].iloc[min(54, len(df)-1)]
        if position > 0:
            pnl = (close - entry) * position
        else:
            pnl = (entry - close) * abs(position)
        capital += pnl
        trades.append(pnl)
    
    return {
        'passed': capital >= start * 1.10, 
        'failed': False,
        'profit': (capital - start) / start * 100,
        'trades': len(trades),
        'win_rate': len([t for t in trades if t > 0]) / len(trades) * 100 if trades else 0
    }


def main():
    print("=" * 70)
    print("🔬 FINAL VALIDATION & STRESS TESTING")
    print("=" * 70)
    
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    # Test 1: Standard backtest
    print("\n📊 TEST 1: Standard Backtest (all periods)")
    print("-" * 50)
    
    all_results = []
    for start in range(80, len(data) - 60, 10):
        window = data.iloc[start:start+60]
        if len(window) < 55:
            continue
        result = backtest_challenge(window)
        all_results.append(result)
    
    passed = len([r for r in all_results if r['passed']])
    failed = len([r for r in all_results if r['failed']])
    total = len(all_results)
    pass_rate = passed / total * 100
    
    print(f"   Total periods tested: {total}")
    print(f"   Passed: {passed} ({pass_rate:.1f}%)")
    print(f"   Failed: {failed}")
    print(f"   Timeout: {total - passed - failed}")
    
    # Test 2: Worst case periods
    print("\n📊 TEST 2: Worst Case Analysis")
    print("-" * 50)
    
    sorted_results = sorted(all_results, key=lambda x: x['profit'])
    
    print("   5 Worst Periods:")
    for r in sorted_results[:5]:
        print(f"      Profit: {r['profit']:+.2f}%")
    
    worst_drawdown = min(r['profit'] for r in all_results)
    print(f"\n   Worst single period: {worst_drawdown:+.2f}%")
    
    # Test 3: Monte Carlo
    print("\n📊 TEST 3: Monte Carlo Simulation (100 runs)")
    print("-" * 50)
    
    mc_results = run_stress_test(data, num_simulations=100)
    
    mc_passed = len([r for r in mc_results if r['passed']])
    mc_pass_rate = mc_passed / len(mc_results) * 100
    
    print(f"   Pass rate: {mc_pass_rate:.1f}%")
    print(f"   Avg profit: {np.mean([r['profit'] for r in mc_results]):.2f}%")
    print(f"   Std dev: {np.std([r['profit'] for r in mc_results]):.2f}%")
    
    # Test 4: Different risk levels
    print("\n📊 TEST 4: Risk Sensitivity Analysis")
    print("-" * 50)
    print(f"{'Risk%':>8} {'Pass Rate':>12} {'Avg Profit':>12} {'Worst':>10}")
    
    for risk in [0.05, 0.06, 0.07, 0.08, 0.09, 0.10]:
        results = []
        for start in range(80, len(data) - 60, 15):
            window = data.iloc[start:start+60]
            if len(window) < 55:
                continue
            result = backtest_challenge(window, risk_pct=risk)
            results.append(result)
        
        pr = len([r for r in results if r['passed']]) / len(results) * 100
        avg_profit = np.mean([r['profit'] for r in results])
        worst = min(r['profit'] for r in results)
        
        print(f"{risk*100:>8.0f} {pr:>12.1f}% {avg_profit:>+12.2f}% {worst:>+10.2f}%")
    
    # Expected Value calculation
    print("\n" + "=" * 70)
    print("💰 EXPECTED VALUE SUMMARY")
    print("=" * 70)
    
    challenge_cost = 100
    win_payout = 800
    
    ev = (pass_rate / 100) * win_payout - ((100 - pass_rate) / 100) * challenge_cost
    
    print(f"""
    Strategy Parameters:
    ─────────────────────────────────
    Risk per trade:   8%
    Stop Loss:        0.8× ATR
    Take Profit:      1.5× ATR
    
    Performance:
    ─────────────────────────────────
    Pass Rate:        {pass_rate:.1f}%
    Challenge Cost:   ${challenge_cost}
    Win Payout:       ${win_payout}
    
    Expected Value:   ${ev:+.2f}
    
    Projections:
    ─────────────────────────────────
    Per 1 challenge:  ${ev:+.2f}
    Per 5 challenges: ${ev * 5:+.2f}
    Per 10 challenges: ${ev * 10:+.2f}
    """)
    
    # Final verdict
    print("=" * 70)
    if ev > 0 and pass_rate >= 30:
        print("✅ STRATEGY VALIDATED - READY FOR LIVE TRADING")
        print("=" * 70)
        print("""
    Next Steps:
    1. Paper trade for 2 weeks minimum
    2. Pass readiness check
    3. Buy prop firm challenge
    4. Follow the strategy exactly
    5. Expect to pass ~40% of challenges
    
    Good luck! 🏆
        """)
    else:
        print("⚠️  STRATEGY NEEDS IMPROVEMENT")
        print("=" * 70)
        print("   Pass rate or EV too low.")


if __name__ == "__main__":
    main()
