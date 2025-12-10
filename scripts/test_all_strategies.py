"""Test all strategies and find the best one."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path

from src.strategy.working_strategy import WorkingStrategy
from src.strategy.trend_following_strategy import TrendFollowingStrategy
from src.strategy.momentum_strategy import MomentumStrategy
from src.strategy.breakout_strategy import BreakoutStrategy


def test_strategy(name, strategy_class, data, **kwargs):
    """Test a strategy and return metrics."""
    try:
        strategy = strategy_class(data.copy(), initial_capital=10000, **kwargs)
        metrics = strategy.backtest()
        return {
            'name': name,
            'metrics': metrics,
            'trades': strategy.trades
        }
    except Exception as e:
        print(f"  Error testing {name}: {e}")
        return None


def main():
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("COMPREHENSIVE STRATEGY COMPARISON")
    print("=" * 70)
    print(f"Data: {len(data)} bars")
    print(f"Period: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    
    buy_hold = ((data['close'].iloc[-1] / data['close'].iloc[200]) - 1) * 100
    print(f"Buy & Hold Return: {buy_hold:+.2f}%")
    
    results = []
    
    # Test different strategies
    print("\nTesting strategies...")
    
    # Working Strategy
    result = test_strategy("EMA Crossover", WorkingStrategy, data, risk_per_trade=0.02)
    if result: results.append(result)
    
    # Trend Following
    result = test_strategy("Trend Following", TrendFollowingStrategy, data, risk_per_trade=0.02)
    if result: results.append(result)
    
    # Momentum
    result = test_strategy("Momentum (2-day)", MomentumStrategy, data, 
                          risk_per_trade=0.02, consecutive_days=2, hold_days=5)
    if result: results.append(result)
    
    result = test_strategy("Momentum (3-day)", MomentumStrategy, data,
                          risk_per_trade=0.02, consecutive_days=3, hold_days=5)
    if result: results.append(result)
    
    # Breakout
    result = test_strategy("Breakout (20-day)", BreakoutStrategy, data,
                          risk_per_trade=0.02, breakout_period=20)
    if result: results.append(result)
    
    result = test_strategy("Breakout (10-day)", BreakoutStrategy, data,
                          risk_per_trade=0.02, breakout_period=10)
    if result: results.append(result)
    
    # Sort by return
    results.sort(key=lambda x: x['metrics']['total_return_pct'], reverse=True)
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS RANKED BY RETURN")
    print("=" * 70)
    print(f"{'Strategy':<20} {'Return%':>10} {'Win%':>8} {'Trades':>7} {'PF':>7} {'R:R':>7} {'MaxDD%':>8}")
    print("-" * 70)
    
    for r in results:
        m = r['metrics']
        print(f"{r['name']:<20} {m['total_return_pct']:>+10.2f} {m['win_rate_pct']:>8.1f} "
              f"{m['total_trades']:>7} {m['profit_factor']:>7.2f} {m['risk_reward_ratio']:>7.2f} "
              f"{m['max_drawdown_pct']:>8.2f}")
    
    print("-" * 70)
    print(f"{'Buy & Hold':<20} {buy_hold:>+10.2f}")
    
    # Best strategy details
    if results:
        best = results[0]
        print(f"\n{'BEST STRATEGY: ' + best['name']:=^70}")
        m = best['metrics']
        
        print(f"\n  Performance:")
        print(f"    Return:        {m['total_return_pct']:+.2f}%")
        print(f"    Net Profit:    ${m['net_profit']:+,.2f}")
        print(f"    Win Rate:      {m['win_rate_pct']:.1f}%")
        print(f"    Profit Factor: {m['profit_factor']:.2f}")
        print(f"    R:R Ratio:     {m['risk_reward_ratio']:.2f}")
        print(f"    Max Drawdown:  {m['max_drawdown_pct']:.2f}%")
        print(f"    Sharpe Ratio:  {m['sharpe_ratio']:.2f}")
        
        if best['trades']:
            print(f"\n  Sample Trades:")
            for i, t in enumerate(best['trades'][:5]):
                print(f"    {i+1}. {t['side']:5} ${t['entry_price']:.2f} -> ${t['exit_price']:.2f} "
                      f"= ${t['pnl']:+,.2f} ({t['exit_reason']})")
        
        # Verdict
        print("\n" + "=" * 70)
        if m['total_return_pct'] > 15 and m['win_rate_pct'] > 50 and m['profit_factor'] > 1.5:
            print("🏆 HIGHLY PROFITABLE STRATEGY!")
        elif m['total_return_pct'] > 10 and m['profit_factor'] > 1.3:
            print("✅ PROFITABLE STRATEGY FOUND!")
        elif m['total_return_pct'] > 5 and m['profit_factor'] > 1.1:
            print("✅ MODERATELY PROFITABLE")
        elif m['total_return_pct'] > 0:
            print("⚠️  MARGINALLY PROFITABLE")
        elif m['total_return_pct'] > buy_hold:
            print("⚠️  LOSING BUT BEATS BUY & HOLD")
        else:
            print("❌ NOT PROFITABLE")


if __name__ == "__main__":
    main()
