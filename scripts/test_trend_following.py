"""Test trend following strategy."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path
from src.strategy.trend_following_strategy import TrendFollowingStrategy


def main():
    # Load data
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("TREND FOLLOWING STRATEGY TEST")
    print("=" * 70)
    print(f"\nData: {len(data)} bars")
    print(f"Period: {data.index[0]} to {data.index[-1]}")
    print(f"Buy & Hold Return: {((data['close'].iloc[-1] / data['close'].iloc[200]) - 1) * 100:.2f}%")
    
    # Test with different risk levels
    for risk in [0.01, 0.02, 0.03]:
        print(f"\n{'='*70}")
        print(f"Risk per trade: {risk*100:.0f}%")
        print("-" * 70)
        
        strategy = TrendFollowingStrategy(
            data.copy(),
            initial_capital=10000,
            risk_per_trade=risk
        )
        metrics = strategy.backtest()
        
        print(f"  Trades:        {metrics['total_trades']}")
        print(f"  Win Rate:      {metrics['win_rate_pct']:.1f}%")
        print(f"  Net P/L:       ${metrics['net_profit']:+,.2f}")
        print(f"  Return:        {metrics['total_return_pct']:+.2f}%")
        print(f"  Avg Win:       ${metrics['avg_win']:.2f}")
        print(f"  Avg Loss:      ${metrics['avg_loss']:.2f}")
        print(f"  R:R Ratio:     {metrics['risk_reward_ratio']:.2f}")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  Max DD:        {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe:        {metrics['sharpe_ratio']:.2f}")
        
        if strategy.trades:
            print(f"\n  Trades:")
            for i, t in enumerate(strategy.trades):
                print(f"    {i+1}. {t['side']:5} ${t['entry_price']:.2f} -> ${t['exit_price']:.2f} "
                      f"= ${t['pnl']:+,.2f} ({t['exit_reason']})")


if __name__ == "__main__":
    main()
