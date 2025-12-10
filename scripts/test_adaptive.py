"""Quick test for working strategy."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path
from src.strategy.working_strategy import WorkingStrategy


def main():
    # Load data
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    print(f"Data: {len(data)} bars, {data.index[0]} to {data.index[-1]}")
    print(f"Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    
    # Test strategy
    print("\n" + "=" * 60)
    print("WORKING STRATEGY TEST")
    print("=" * 60)
    
    for capital in [10000, 25000]:
        print(f"\n--- Capital: ${capital:,} ---")
        
        strategy = WorkingStrategy(data.copy(), initial_capital=capital)
        metrics = strategy.backtest()
        
        print(f"  Trades:       {metrics['total_trades']}")
        print(f"  Win Rate:     {metrics['win_rate_pct']:.1f}%")
        print(f"  Net P/L:      ${metrics['net_profit']:+,.2f}")
        print(f"  Return:       {metrics['total_return_pct']:+.2f}%")
        print(f"  Avg Win:      ${metrics['avg_win']:.2f}")
        print(f"  Avg Loss:     ${metrics['avg_loss']:.2f}")
        print(f"  R:R Ratio:    {metrics['risk_reward_ratio']:.2f}")
        print(f"  Profit Factor:{metrics['profit_factor']:.2f}")
        print(f"  Max DD:       {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe:       {metrics['sharpe_ratio']:.2f}")
        
        if strategy.trades:
            print(f"\n  Trade log:")
            for i, t in enumerate(strategy.trades[:5]):
                print(f"    {i+1}. {t['side']:5} ${t['entry_price']:.2f} -> ${t['exit_price']:.2f} "
                      f"= ${t['pnl']:+.2f} ({t['exit_reason']})")
            if len(strategy.trades) > 5:
                print(f"    ... +{len(strategy.trades)-5} more")


if __name__ == "__main__":
    main()
