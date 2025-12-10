"""Test the aggressive prop firm strategy."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path
from src.strategy.prop_firm_strategy import PropFirmStrategy


def main():
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("🚀 AGGRESSIVE PROP FIRM STRATEGY TEST")
    print("=" * 70)
    
    # Test on full data
    print("\nFull data test:")
    strategy = PropFirmStrategy(data, risk_per_trade=0.03)
    result = strategy.backtest()
    
    print(f"  Profit: {result['profit_pct']:+.2f}%")
    print(f"  Trades: {result['trades']}")
    print(f"  Win Rate: {result['win_rate']:.1f}%")
    print(f"  Max DD: {result['max_dd']:.2f}%")
    print(f"  Passed 10% target: {'✅ YES' if result['passed'] else '❌ NO'}")
    
    # Test on 30-day windows
    print("\n" + "=" * 70)
    print("30-DAY CHALLENGE WINDOWS")
    print("=" * 70)
    print(f"{'Start':<12} {'Profit%':>10} {'Trades':>8} {'Win%':>8} {'MaxDD%':>8} {'Status'}")
    print("-" * 70)
    
    passed = 0
    failed = 0
    timeout = 0
    
    for start in range(100, len(data) - 30, 30):
        window = data.iloc[start-50:start+30]
        
        strategy = PropFirmStrategy(window, risk_per_trade=0.04)  # 4% for aggressive
        result = strategy.backtest()
        
        status = "✅ PASS" if result['passed'] else ("❌ FAIL" if result['failed'] else "⏳ TIME")
        
        if result['passed']:
            passed += 1
        elif result['failed']:
            failed += 1
        else:
            timeout += 1
        
        print(f"{data.index[start].strftime('%Y-%m-%d'):<12} "
              f"{result['profit_pct']:>+10.2f} {result['trades']:>8} "
              f"{result['win_rate']:>8.1f} {result['max_dd']:>8.2f} {status}")
    
    print("-" * 70)
    total = passed + failed + timeout
    print(f"\n📊 SUMMARY")
    print(f"   Passed:    {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"   Failed:    {failed}/{total} ({failed/total*100:.0f}%)")
    print(f"   Timeout:   {timeout}/{total} ({timeout/total*100:.0f}%)")
    
    # Verdict
    print("\n" + "=" * 70)
    pass_rate = passed / total * 100 if total > 0 else 0
    
    if pass_rate >= 30:
        print(f"""
    ✅ PROP FIRM VIABLE!
    
    Pass rate: {pass_rate:.0f}%
    
    YOUR $100 STRATEGY:
    1. Buy prop firm challenge (~$100)
    2. Use this aggressive strategy
    3. {pass_rate:.0f}% chance of passing
    4. If passed: Trade $10K+ of their money!
    
    EXPECTED VALUE:
    Win: ${pass_rate/100 * 800:.0f} (80% of potential $1000 profit)
    Lose: ${(100-pass_rate)/100 * 100:.0f} (challenge fee)
    EV: ${pass_rate/100 * 800 - (100-pass_rate)/100 * 100:.0f}
    """)
    else:
        print(f"""
    ⚠️  PROP FIRM RISKY
    
    Pass rate: {pass_rate:.0f}% (need 30%+ to be +EV)
    
    RECOMMENDATION:
    - Paper trade for 2-3 months first
    - Save up $500+ for personal trading
    - Prop firm is gambling at this pass rate
    """)


if __name__ == "__main__":
    main()
