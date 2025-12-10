"""Test optimized prop firm strategy."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from src.strategy.optimized_prop_strategy import OptimizedPropStrategy


def main():
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("🚀 OPTIMIZED PROP FIRM STRATEGY TEST")
    print("=" * 70)
    
    # Test different risk levels
    print("\nFinding optimal risk level...")
    print(f"{'Risk%':>8} {'Pass Rate':>12} {'Avg Profit':>12} {'Avg DD':>10}")
    print("-" * 50)
    
    best_pass_rate = 0
    best_risk = 0.02
    
    for base_risk in [0.015, 0.02, 0.025, 0.03, 0.035]:
        results = []
        
        for start in range(100, len(data) - 40, 20):
            window = data.iloc[start-50:start+35]
            if len(window) < 80:
                continue
            
            strategy = OptimizedPropStrategy(window, base_risk=base_risk, max_risk=base_risk * 2)
            result = strategy.backtest_challenge()
            results.append(result)
        
        passed = len([r for r in results if r['passed']])
        pass_rate = passed / len(results) * 100 if results else 0
        avg_profit = np.mean([r['profit_pct'] for r in results])
        avg_dd = np.mean([r['max_dd'] for r in results])
        
        print(f"{base_risk*100:>8.1f} {pass_rate:>12.1f}% {avg_profit:>+12.2f}% {avg_dd:>10.2f}%")
        
        if pass_rate > best_pass_rate:
            best_pass_rate = pass_rate
            best_risk = base_risk
    
    print("-" * 50)
    print(f"Best risk: {best_risk*100:.1f}% with {best_pass_rate:.1f}% pass rate")
    
    # Full test with best risk
    print("\n" + "=" * 70)
    print(f"FULL TEST WITH {best_risk*100:.1f}% RISK")
    print("=" * 70)
    print(f"{'Start':<12} {'Profit%':>10} {'Trades':>8} {'Win%':>8} {'MaxDD%':>8} {'Status'}")
    print("-" * 70)
    
    all_results = []
    
    for start in range(100, len(data) - 40, 15):  # More frequent testing
        window = data.iloc[start-50:start+35]
        if len(window) < 80:
            continue
        
        strategy = OptimizedPropStrategy(window, base_risk=best_risk, max_risk=best_risk * 2)
        result = strategy.backtest_challenge()
        result['start_date'] = data.index[start].strftime('%Y-%m-%d')
        all_results.append(result)
        
        status = "✅ PASS" if result['passed'] else ("❌ FAIL" if result['failed'] else "⏳ TIME")
        days = result.get('days_to_pass', 30)
        
        print(f"{result['start_date']:<12} {result['profit_pct']:>+10.2f} "
              f"{result['trades']:>8} {result['win_rate']:>8.1f} "
              f"{result['max_dd']:>8.2f} {status}")
    
    print("-" * 70)
    
    # Summary
    passed = [r for r in all_results if r['passed']]
    failed = [r for r in all_results if r['failed']]
    timeout = [r for r in all_results if not r['passed'] and not r['failed']]
    
    total = len(all_results)
    pass_rate = len(passed) / total * 100
    
    print(f"\n📊 FINAL RESULTS")
    print(f"   Total Tests:    {total}")
    print(f"   Passed:         {len(passed)} ({pass_rate:.1f}%)")
    print(f"   Failed:         {len(failed)} ({len(failed)/total*100:.1f}%)")
    print(f"   Timeout:        {len(timeout)} ({len(timeout)/total*100:.1f}%)")
    
    if passed:
        print(f"\n   When Passed:")
        print(f"   - Avg profit:   {np.mean([r['profit_pct'] for r in passed]):.2f}%")
        print(f"   - Avg days:     {np.mean([r.get('days_to_pass', 30) for r in passed]):.1f}")
    
    # Expected value calculation
    print("\n" + "=" * 70)
    print("💰 EXPECTED VALUE CALCULATION")
    print("=" * 70)
    
    challenge_cost = 100
    account_size = 10000
    profit_split = 0.80
    
    if pass_rate >= 10:
        avg_profit_when_pass = np.mean([r['profit_pct'] for r in passed]) if passed else 10
        profit_when_pass = account_size * (avg_profit_when_pass / 100) * profit_split
        
        ev = (pass_rate / 100) * profit_when_pass - ((100 - pass_rate) / 100) * challenge_cost
        
        print(f"""
    Challenge cost:     ${challenge_cost}
    Account size:       ${account_size:,}
    Profit split:       {profit_split*100:.0f}%
    
    Pass rate:          {pass_rate:.1f}%
    Avg profit (pass):  {avg_profit_when_pass:.2f}%
    Your profit (pass): ${profit_when_pass:.2f}
    
    EXPECTED VALUE:     ${ev:+.2f}
    
    Calculation:
    {pass_rate:.1f}% × ${profit_when_pass:.2f} - {100-pass_rate:.1f}% × ${challenge_cost} = ${ev:+.2f}
    """)
        
        if ev > 0:
            print(f"    ✅ POSITIVE EV! Worth attempting prop firm challenge.")
            print(f"    📈 Over 10 attempts, expected profit: ${ev * 10:.2f}")
        else:
            print(f"    ❌ NEGATIVE EV. Need to improve strategy first.")
    else:
        print(f"\n    Pass rate too low ({pass_rate:.1f}%) - need more optimization.")
    
    return pass_rate, all_results


if __name__ == "__main__":
    pass_rate, results = main()
