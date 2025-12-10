"""
Realistic Trading Bot Test

This script tests the trading bot with:
1. Realistic transaction costs
2. Different starting capital amounts ($100, $1000, $10000)
3. Multiple strategies
4. Honest performance metrics

The goal is to answer: "What would REALLY happen if I put $X in an account?"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from src.analysis.technical import TechnicalAnalyzer
from src.strategy.trend_momentum_strategy import TrendMomentumStrategy
from src.strategy.sma_crossover import SMACrossoverStrategy
from src.strategy.rsi_mean_reversion import RSIMeanReversionStrategy
from src.strategy.realistic_backtester import RealisticBacktester


def load_data(timeframe: str = "1D") -> pd.DataFrame:
    """Load sample data."""
    data_path = Path("data") / f"XAU_USD_{timeframe}_sample.csv"
    
    if not data_path.exists():
        print("Generating sample data...")
        from scripts.generate_sample_data import main as generate_data
        generate_data()
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    # Add technical indicators
    analyzer = TechnicalAnalyzer(df)
    df = analyzer.analyze_all()
    
    return df


def test_with_capital(capital: float, data: pd.DataFrame) -> dict:
    """Test the trading bot with a specific capital amount."""
    
    print(f"\n{'='*70}")
    print(f"TESTING WITH ${capital:,.2f} STARTING CAPITAL")
    print(f"{'='*70}")
    
    results = {}
    
    # Test 1: Trend Momentum Strategy
    print("\n--- Trend Momentum Strategy ---")
    try:
        strategy = TrendMomentumStrategy(data.copy(), initial_capital=capital)
        backtester = RealisticBacktester(initial_capital=capital)
        metrics = backtester.run_backtest(strategy, data.copy())
        results['TrendMomentum'] = metrics
        
        print(f"  Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate_pct']:.1f}%")
        print(f"  Return: {metrics['total_return_pct']:.2f}%")
        print(f"  Final: ${metrics['final_capital']:.2f}")
        print(f"  Costs: ${metrics['total_costs']:.2f} ({metrics['cost_pct_of_capital']:.1f}% of capital)")
    except Exception as e:
        print(f"  Error: {str(e)}")
        results['TrendMomentum'] = {'error': str(e)}
    
    # Test 2: RSI Mean Reversion (simpler strategy)
    print("\n--- RSI Mean Reversion Strategy ---")
    try:
        strategy = RSIMeanReversionStrategy(data.copy(), initial_capital=capital)
        backtester = RealisticBacktester(initial_capital=capital)
        metrics = backtester.run_backtest(strategy, data.copy())
        results['RSIMeanReversion'] = metrics
        
        print(f"  Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate_pct']:.1f}%")
        print(f"  Return: {metrics['total_return_pct']:.2f}%")
        print(f"  Final: ${metrics['final_capital']:.2f}")
        print(f"  Costs: ${metrics['total_costs']:.2f} ({metrics['cost_pct_of_capital']:.1f}% of capital)")
    except Exception as e:
        print(f"  Error: {str(e)}")
        results['RSIMeanReversion'] = {'error': str(e)}
    
    # Test 3: SMA Crossover
    print("\n--- SMA Crossover Strategy ---")
    try:
        strategy = SMACrossoverStrategy(data.copy(), initial_capital=capital)
        backtester = RealisticBacktester(initial_capital=capital)
        metrics = backtester.run_backtest(strategy, data.copy())
        results['SMACrossover'] = metrics
        
        print(f"  Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate_pct']:.1f}%")
        print(f"  Return: {metrics['total_return_pct']:.2f}%")
        print(f"  Final: ${metrics['final_capital']:.2f}")
        print(f"  Costs: ${metrics['total_costs']:.2f} ({metrics['cost_pct_of_capital']:.1f}% of capital)")
    except Exception as e:
        print(f"  Error: {str(e)}")
        results['SMACrossover'] = {'error': str(e)}
    
    return results


def main():
    """Run comprehensive realistic tests."""
    
    print("=" * 70)
    print("REALISTIC TRADING BOT ASSESSMENT")
    print("The Hard Truth About Algorithmic Trading")
    print("=" * 70)
    
    # Load data
    print("\nLoading 2 years of XAU/USD daily data...")
    data = load_data("1D")
    print(f"Loaded {len(data)} data points")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    print(f"Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    
    # Test with different capital amounts
    capital_amounts = [100, 1000, 10000]
    all_results = {}
    
    for capital in capital_amounts:
        all_results[capital] = test_with_capital(capital, data)
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("SUMMARY: WHAT WOULD HAPPEN WITH YOUR MONEY")
    print("=" * 70)
    
    print("\n" + "-" * 70)
    print(f"{'Capital':<12} {'Strategy':<20} {'Return':<12} {'Final':<12} {'Verdict'}")
    print("-" * 70)
    
    for capital in capital_amounts:
        for strategy_name, metrics in all_results[capital].items():
            if 'error' in metrics:
                print(f"${capital:<11,} {strategy_name:<20} {'ERROR':<12} {'-':<12} {'FAILED'}")
            else:
                ret = metrics['total_return_pct']
                final = metrics['final_capital']
                
                if metrics['total_trades'] == 0:
                    verdict = "NO TRADES POSSIBLE"
                elif ret < -20:
                    verdict = "ACCOUNT BLOWN"
                elif ret < -10:
                    verdict = "MAJOR LOSS"
                elif ret < 0:
                    verdict = "LOSING MONEY"
                elif ret < 5:
                    verdict = "BARELY BREAKING EVEN"
                elif ret < 15:
                    verdict = "MODEST GAIN"
                else:
                    verdict = "PROFITABLE"
                
                print(f"${capital:<11,} {strategy_name:<20} {ret:>+10.2f}% ${final:>10,.2f} {verdict}")
    
    print("-" * 70)
    
    # Honest conclusions
    print("\n" + "=" * 70)
    print("HONEST CONCLUSIONS")
    print("=" * 70)
    
    print("""
1. WITH $100:
   - Most positions are TOO SMALL to execute (minimum lot = 0.01 = $200+ margin)
   - Even if trades execute, costs eat into any profits
   - High probability of account wipeout with any leverage
   
2. WITH $1,000:
   - Can execute a few trades, but position sizes are still very small
   - Transaction costs (~$5-10 per trade) significantly impact returns
   - Need consistent 10%+ returns just to cover costs
   
3. WITH $10,000:
   - Now we're talking. Can properly size positions.
   - Transaction costs are ~1% of capital, manageable
   - But still need a GOOD strategy to be profitable
   
4. THE REAL REQUIREMENTS FOR PROFITABLE TRADING:
   - Minimum $5,000-10,000 starting capital
   - Win rate > 45% with Risk/Reward > 1.5
   - Sharpe ratio > 1.0
   - Max drawdown < 15%
   - Strategy that works across market conditions
   
5. WHAT THIS BOT NEEDS TO BE VIABLE:
   - Higher win rate (aim for 55%+)
   - Better risk/reward (aim for 2:1 or higher)
   - More sophisticated entry/exit timing
   - Market regime detection
   - Proper money management
""")
    
    # Final recommendation
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print("""
DO NOT put real money into this bot yet.

Before trading real money, the bot needs:
1. ✅ Backtested with realistic costs (DONE)
2. ⬜ Consistent positive returns after costs
3. ⬜ Tested on out-of-sample data
4. ⬜ Paper trading for 3-6 months
5. ⬜ Strategy optimization and validation
6. ⬜ Proper risk management rules

Current Status: DEVELOPMENT/EDUCATIONAL USE ONLY
""")
    
    return all_results


if __name__ == "__main__":
    results = main()
