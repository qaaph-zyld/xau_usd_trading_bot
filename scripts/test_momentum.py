"""Test momentum strategy."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path
from src.strategy.momentum_strategy import MomentumStrategy


def main():
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("MOMENTUM STRATEGY TEST")
    print("=" * 70)
    print(f"Data: {len(data)} bars")
    print(f"Buy & Hold: {((data['close'].iloc[-1] / data['close'].iloc[200]) - 1) * 100:+.2f}%")
    
    # Test different parameters
    best_return = -100
    best_params = None
    
    for consec in [2, 3, 4]:
        for hold in [3, 5, 7, 10]:
            for risk in [0.01, 0.02, 0.03]:
                strategy = MomentumStrategy(
                    data.copy(),
                    initial_capital=10000,
                    risk_per_trade=risk,
                    consecutive_days=consec,
                    hold_days=hold
                )
                metrics = strategy.backtest()
                
                if metrics['total_return_pct'] > best_return and metrics['total_trades'] >= 5:
                    best_return = metrics['total_return_pct']
                    best_params = {
                        'consec': consec,
                        'hold': hold,
                        'risk': risk,
                        'metrics': metrics,
                        'trades': strategy.trades
                    }
    
    print(f"\n{'BEST PARAMETERS':=^70}")
    if best_params:
        print(f"  Consecutive days: {best_params['consec']}")
        print(f"  Hold days: {best_params['hold']}")
        print(f"  Risk per trade: {best_params['risk']*100:.0f}%")
        
        m = best_params['metrics']
        print(f"\n{'RESULTS':=^70}")
        print(f"  Trades:        {m['total_trades']}")
        print(f"  Win Rate:      {m['win_rate_pct']:.1f}%")
        print(f"  Net P/L:       ${m['net_profit']:+,.2f}")
        print(f"  Return:        {m['total_return_pct']:+.2f}%")
        print(f"  Avg Win:       ${m['avg_win']:.2f}")
        print(f"  Avg Loss:      ${m['avg_loss']:.2f}")
        print(f"  R:R Ratio:     {m['risk_reward_ratio']:.2f}")
        print(f"  Profit Factor: {m['profit_factor']:.2f}")
        print(f"  Max DD:        {m['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe:        {m['sharpe_ratio']:.2f}")
        
        if best_params['trades']:
            print(f"\n  Trades:")
            for i, t in enumerate(best_params['trades'][:10]):
                print(f"    {i+1}. {t['side']:5} ${t['entry_price']:.2f} -> ${t['exit_price']:.2f} "
                      f"= ${t['pnl']:+,.2f} ({t['exit_reason']}, {t.get('bars_held', '?')} bars)")
            if len(best_params['trades']) > 10:
                print(f"    ... +{len(best_params['trades'])-10} more")
        
        # Verdict
        print("\n" + "=" * 70)
        if m['total_return_pct'] > 10 and m['win_rate_pct'] > 50:
            print("✅ PROFITABLE STRATEGY FOUND!")
        elif m['total_return_pct'] > 5 and m['profit_factor'] > 1.2:
            print("✅ MARGINALLY PROFITABLE - Worth further optimization")
        elif m['total_return_pct'] > 0:
            print("⚠️  BARELY BREAKING EVEN")
        else:
            print("❌ NOT PROFITABLE")
    else:
        print("  No valid parameter combination found")


if __name__ == "__main__":
    main()
