"""
Test the Profitable Strategy

This script tests the new strategy designed for real profitability.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path

from src.analysis.technical import TechnicalAnalyzer
from src.strategy.profitable_strategy import ProfitableStrategy
from src.strategy.realistic_backtester import RealisticBacktester


def load_data() -> pd.DataFrame:
    """Load sample data."""
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    
    if not data_path.exists():
        print("Generating sample data...")
        from scripts.generate_sample_data import main as generate_data
        generate_data()
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    return df


def test_strategy(capital: float = 10000):
    """Test the profitable strategy."""
    
    print("=" * 70)
    print("PROFITABLE STRATEGY TEST")
    print("=" * 70)
    
    # Load data
    print("\nLoading data...")
    data = load_data()
    print(f"Loaded {len(data)} bars")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    
    # Split into training and testing
    split_idx = int(len(data) * 0.7)
    train_data = data.iloc[:split_idx].copy()
    test_data = data.iloc[split_idx:].copy()
    
    print(f"\nTraining data: {len(train_data)} bars ({train_data.index[0]} to {train_data.index[-1]})")
    print(f"Testing data: {len(test_data)} bars ({test_data.index[0]} to {test_data.index[-1]})")
    
    # Test on training data
    print("\n" + "-" * 70)
    print("TRAINING PERIOD RESULTS")
    print("-" * 70)
    
    strategy = ProfitableStrategy(train_data, initial_capital=capital)
    train_metrics = strategy.backtest()
    
    print_metrics(train_metrics)
    
    # Test on out-of-sample data
    print("\n" + "-" * 70)
    print("OUT-OF-SAMPLE TESTING (Validation)")
    print("-" * 70)
    
    # Need enough history for indicators
    if len(test_data) > 250:
        test_strategy = ProfitableStrategy(test_data, initial_capital=capital)
        test_metrics = test_strategy.backtest()
        print_metrics(test_metrics)
    else:
        print("Not enough test data for out-of-sample testing")
        test_metrics = None
    
    # Test on full data with realistic costs
    print("\n" + "-" * 70)
    print("FULL PERIOD WITH REALISTIC COSTS")
    print("-" * 70)
    
    full_strategy = ProfitableStrategy(data, initial_capital=capital)
    full_metrics = full_strategy.backtest()
    
    print_metrics(full_metrics)
    
    # Trade analysis
    if full_strategy.trades:
        print("\n" + "-" * 70)
        print("TRADE ANALYSIS")
        print("-" * 70)
        
        trades_df = pd.DataFrame(full_strategy.trades)
        
        print(f"\nExit Reason Breakdown:")
        exit_counts = trades_df['exit_reason'].value_counts()
        for reason, count in exit_counts.items():
            pnl = trades_df[trades_df['exit_reason'] == reason]['pnl'].sum()
            print(f"  {reason}: {count} trades, ${pnl:+,.2f} P/L")
        
        print(f"\nTrade Details:")
        for i, trade in enumerate(full_strategy.trades[:10]):  # Show first 10
            print(f"  {i+1}. {trade['side'].upper():5} @ ${trade['entry_price']:.2f} -> ${trade['exit_price']:.2f} "
                  f"= ${trade['pnl']:+,.2f} ({trade['exit_reason']})")
        
        if len(full_strategy.trades) > 10:
            print(f"  ... and {len(full_strategy.trades) - 10} more trades")
    
    return full_metrics


def print_metrics(metrics: dict):
    """Print formatted metrics."""
    print(f"\n  Capital:     ${metrics['initial_capital']:>12,.2f} -> ${metrics['final_capital']:>12,.2f}")
    print(f"  Net P/L:     ${metrics['net_profit']:>12,.2f} ({metrics['total_return_pct']:+.2f}%)")
    print(f"  Trades:      {metrics['total_trades']:>12}")
    print(f"  Win Rate:    {metrics['win_rate_pct']:>12.1f}%")
    print(f"  Avg Win:     ${metrics['avg_win']:>12,.2f}")
    print(f"  Avg Loss:    ${metrics['avg_loss']:>12,.2f}")
    print(f"  R:R Ratio:   {metrics['risk_reward_ratio']:>12.2f}")
    print(f"  Profit Factor: {metrics['profit_factor']:>10.2f}")
    print(f"  Max DD:      {metrics['max_drawdown_pct']:>12.2f}%")
    print(f"  Sharpe:      {metrics['sharpe_ratio']:>12.2f}")
    
    # Verdict
    if metrics['total_trades'] == 0:
        verdict = "NO TRADES"
    elif metrics['total_return_pct'] > 20 and metrics['win_rate_pct'] > 50:
        verdict = "EXCELLENT"
    elif metrics['total_return_pct'] > 10 and metrics['win_rate_pct'] > 45:
        verdict = "GOOD"
    elif metrics['total_return_pct'] > 5:
        verdict = "ACCEPTABLE"
    elif metrics['total_return_pct'] > 0:
        verdict = "MARGINAL"
    else:
        verdict = "NEEDS WORK"
    
    print(f"\n  VERDICT: {verdict}")


def optimize_parameters(data: pd.DataFrame, capital: float = 10000):
    """Try different parameter combinations."""
    
    print("\n" + "=" * 70)
    print("PARAMETER OPTIMIZATION")
    print("=" * 70)
    
    results = []
    
    risk_levels = [0.005, 0.01, 0.015, 0.02]  # 0.5% to 2% risk
    min_rr_ratios = [1.5, 2.0, 2.5, 3.0]
    
    for risk in risk_levels:
        for rr in min_rr_ratios:
            try:
                strategy = ProfitableStrategy(
                    data.copy(),
                    initial_capital=capital,
                    risk_per_trade=risk,
                    min_rr_ratio=rr
                )
                metrics = strategy.backtest()
                
                results.append({
                    'risk': risk,
                    'min_rr': rr,
                    'return': metrics['total_return_pct'],
                    'win_rate': metrics['win_rate_pct'],
                    'trades': metrics['total_trades'],
                    'profit_factor': metrics['profit_factor'],
                    'max_dd': metrics['max_drawdown_pct'],
                    'sharpe': metrics['sharpe_ratio']
                })
            except Exception as e:
                print(f"  Error with risk={risk}, rr={rr}: {e}")
    
    if results:
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('return', ascending=False)
        
        print("\nTop 5 Parameter Combinations:")
        print("-" * 70)
        print(f"{'Risk%':<8} {'R:R':<6} {'Return%':<10} {'Win%':<8} {'Trades':<8} {'PF':<8} {'MaxDD%':<8}")
        print("-" * 70)
        
        for _, row in results_df.head(5).iterrows():
            print(f"{row['risk']*100:<8.1f} {row['min_rr']:<6.1f} {row['return']:<+10.2f} "
                  f"{row['win_rate']:<8.1f} {row['trades']:<8} {row['profit_factor']:<8.2f} "
                  f"{row['max_dd']:<8.2f}")
        
        # Return best parameters
        best = results_df.iloc[0]
        return {'risk': best['risk'], 'min_rr': best['min_rr']}
    
    return None


if __name__ == "__main__":
    # Test with different capital levels
    for capital in [10000, 25000, 50000]:
        print(f"\n{'='*70}")
        print(f"TESTING WITH ${capital:,} CAPITAL")
        print(f"{'='*70}")
        
        metrics = test_strategy(capital)
    
    # Run optimization
    print("\n" + "=" * 70)
    data = load_data()
    best_params = optimize_parameters(data)
    
    if best_params:
        print(f"\nBest parameters: Risk={best_params['risk']*100:.1f}%, Min R:R={best_params['min_rr']:.1f}")
