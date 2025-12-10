"""Optimize strategy parameters for maximum profitability."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import product
from src.strategy.working_strategy import WorkingStrategy


def main():
    # Load data
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("PARAMETER OPTIMIZATION")
    print("=" * 70)
    print(f"\nData: {len(data)} bars")
    
    # Split data: 70% training, 30% validation
    split_idx = int(len(data) * 0.7)
    train_data = data.iloc[:split_idx].copy()
    test_data = data.iloc[split_idx:].copy()
    
    print(f"Training: {len(train_data)} bars")
    print(f"Testing: {len(test_data)} bars")
    
    # Parameter grid
    risk_levels = [0.01, 0.02, 0.03]
    sl_mults = [1.5, 2.0, 2.5, 3.0]
    tp_mults = [3.0, 4.0, 5.0, 6.0]
    trail_mults = [1.0, 1.5, 2.0]
    
    results = []
    total = len(risk_levels) * len(sl_mults) * len(tp_mults) * len(trail_mults)
    
    print(f"\nTesting {total} parameter combinations...")
    
    for risk, sl, tp, trail in product(risk_levels, sl_mults, tp_mults, trail_mults):
        # Skip invalid combinations (TP must be > SL for positive expectancy)
        if tp <= sl:
            continue
        
        try:
            strategy = WorkingStrategy(
                train_data.copy(),
                initial_capital=10000,
                risk_per_trade=risk,
                sl_atr_mult=sl,
                tp_atr_mult=tp,
                trail_atr_mult=trail
            )
            metrics = strategy.backtest()
            
            if metrics['total_trades'] >= 5:  # Minimum trades
                results.append({
                    'risk': risk,
                    'sl_mult': sl,
                    'tp_mult': tp,
                    'trail_mult': trail,
                    'return_pct': metrics['total_return_pct'],
                    'win_rate': metrics['win_rate_pct'],
                    'trades': metrics['total_trades'],
                    'profit_factor': metrics['profit_factor'],
                    'rr_ratio': metrics['risk_reward_ratio'],
                    'max_dd': metrics['max_drawdown_pct'],
                    'sharpe': metrics['sharpe_ratio']
                })
        except Exception as e:
            pass
    
    if not results:
        print("No valid results!")
        return
    
    # Sort by return
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('return_pct', ascending=False)
    
    print(f"\n{'TOP 10 PARAMETER COMBINATIONS':=^70}")
    print("-" * 70)
    print(f"{'Risk%':<7} {'SL':<5} {'TP':<5} {'Trail':<6} {'Return%':<9} {'WR%':<7} {'Trades':<7} {'PF':<7} {'R:R':<6}")
    print("-" * 70)
    
    for _, row in results_df.head(10).iterrows():
        print(f"{row['risk']*100:<7.1f} {row['sl_mult']:<5.1f} {row['tp_mult']:<5.1f} "
              f"{row['trail_mult']:<6.1f} {row['return_pct']:<+9.2f} {row['win_rate']:<7.1f} "
              f"{row['trades']:<7} {row['profit_factor']:<7.2f} {row['rr_ratio']:<6.2f}")
    
    # Get best parameters
    best = results_df.iloc[0]
    
    print(f"\n{'BEST PARAMETERS':=^70}")
    print(f"  Risk per trade: {best['risk']*100:.1f}%")
    print(f"  Stop Loss ATR mult: {best['sl_mult']:.1f}")
    print(f"  Take Profit ATR mult: {best['tp_mult']:.1f}")
    print(f"  Trailing Stop ATR mult: {best['trail_mult']:.1f}")
    
    # Validate on test data
    print(f"\n{'OUT-OF-SAMPLE VALIDATION':=^70}")
    
    strategy = WorkingStrategy(
        test_data.copy(),
        initial_capital=10000,
        risk_per_trade=best['risk'],
        sl_atr_mult=best['sl_mult'],
        tp_atr_mult=best['tp_mult'],
        trail_atr_mult=best['trail_mult']
    )
    test_metrics = strategy.backtest()
    
    print(f"  Trades: {test_metrics['total_trades']}")
    print(f"  Win Rate: {test_metrics['win_rate_pct']:.1f}%")
    print(f"  Return: {test_metrics['total_return_pct']:+.2f}%")
    print(f"  Profit Factor: {test_metrics['profit_factor']:.2f}")
    print(f"  R:R Ratio: {test_metrics['risk_reward_ratio']:.2f}")
    print(f"  Max DD: {test_metrics['max_drawdown_pct']:.2f}%")
    
    # Full data test
    print(f"\n{'FULL DATA RESULTS':=^70}")
    
    strategy = WorkingStrategy(
        data.copy(),
        initial_capital=10000,
        risk_per_trade=best['risk'],
        sl_atr_mult=best['sl_mult'],
        tp_atr_mult=best['tp_mult'],
        trail_atr_mult=best['trail_mult']
    )
    full_metrics = strategy.backtest()
    
    print(f"  Trades: {full_metrics['total_trades']}")
    print(f"  Win Rate: {full_metrics['win_rate_pct']:.1f}%")
    print(f"  Return: {full_metrics['total_return_pct']:+.2f}%")
    print(f"  Net Profit: ${full_metrics['net_profit']:+,.2f}")
    print(f"  Profit Factor: {full_metrics['profit_factor']:.2f}")
    print(f"  R:R Ratio: {full_metrics['risk_reward_ratio']:.2f}")
    print(f"  Max DD: {full_metrics['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe: {full_metrics['sharpe_ratio']:.2f}")
    
    # Verdict
    print("\n" + "=" * 70)
    if full_metrics['total_return_pct'] > 10 and full_metrics['win_rate_pct'] > 45:
        print("✅ STRATEGY IS PROFITABLE!")
    elif full_metrics['total_return_pct'] > 5:
        print("⚠️  MARGINALLY PROFITABLE - Needs more optimization")
    elif full_metrics['total_return_pct'] > 0:
        print("⚠️  BARELY BREAKING EVEN - Significant changes needed")
    else:
        print("❌ STRATEGY IS NOT PROFITABLE")
    
    return best, full_metrics


if __name__ == "__main__":
    best_params, metrics = main()
