"""
Demo script to run backtests and generate performance reports.
This demonstrates the full capabilities of the trading bot.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime
import json

from src.analysis.technical import TechnicalAnalyzer
from src.strategy.sma_crossover import SMACrossoverStrategy
from src.strategy.rsi_mean_reversion import RSIMeanReversionStrategy
from src.strategy.backtester import Backtester


def load_sample_data(timeframe: str = "1D") -> pd.DataFrame:
    """Load sample data from the data directory."""
    data_path = Path("data") / f"XAU_USD_{timeframe}_sample.csv"
    
    if not data_path.exists():
        print("Sample data not found. Generating...")
        from scripts.generate_sample_data import main as generate_data
        generate_data()
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    return df


def run_strategy_comparison(data: pd.DataFrame) -> dict:
    """Run backtests for multiple strategies and compare results."""
    
    # Initialize backtester with strategies
    strategies = [SMACrossoverStrategy, RSIMeanReversionStrategy]
    backtester = Backtester(data, strategies)
    
    # Define strategy parameters
    params = {
        'SMACrossoverStrategy': {
            'short_window': 20,
            'long_window': 50
        },
        'RSIMeanReversionStrategy': {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70
        }
    }
    
    # Run backtests
    results = backtester.run_backtest(strategy_params=params, initial_capital=100000)
    
    return results, backtester


def generate_performance_charts(results: dict, output_dir: Path):
    """Generate comprehensive performance visualizations."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Strategy Comparison - Portfolio Value
    fig, ax = plt.subplots(figsize=(14, 7))
    
    colors = {'SMACrossoverStrategy': '#2ecc71', 'RSIMeanReversionStrategy': '#3498db'}
    
    for strategy_name, result in results.items():
        strategy = result['strategy']
        ax.plot(strategy.data.index, strategy.capital, 
                label=strategy_name.replace('Strategy', ''), 
                linewidth=2, color=colors.get(strategy_name, '#95a5a6'))
    
    ax.axhline(y=100000, color='#e74c3c', linestyle='--', alpha=0.7, label='Initial Capital')
    ax.set_title('Strategy Comparison - Portfolio Value Over Time', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    plt.tight_layout()
    plt.savefig(output_dir / 'strategy_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. Performance Metrics Bar Chart
    fig, ax = plt.subplots(figsize=(12, 6))
    
    metrics_to_plot = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
    metric_labels = ['Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Win Rate']
    
    x = np.arange(len(metrics_to_plot))
    width = 0.35
    
    strategy_names = list(results.keys())
    for i, strategy_name in enumerate(strategy_names):
        values = [results[strategy_name]['metrics'][m] for m in metrics_to_plot]
        # Convert to percentages where appropriate
        values = [v * 100 if m in ['total_return', 'max_drawdown', 'win_rate'] else v for v, m in zip(values, metrics_to_plot)]
        offset = width * (i - 0.5)
        bars = ax.bar(x + offset, values, width, label=strategy_name.replace('Strategy', ''),
                     color=colors.get(strategy_name, '#95a5a6'))
        ax.bar_label(bars, fmt='%.2f', padding=3, fontsize=9)
    
    ax.set_ylabel('Value', fontsize=12)
    ax.set_title('Strategy Performance Metrics', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels)
    ax.legend(loc='upper right')
    ax.axhline(y=0, color='black', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(output_dir / 'performance_metrics.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 3. Drawdown Analysis
    fig, axes = plt.subplots(len(results), 1, figsize=(14, 4 * len(results)), sharex=True)
    if len(results) == 1:
        axes = [axes]
    
    for ax, (strategy_name, result) in zip(axes, results.items()):
        strategy = result['strategy']
        capital = strategy.capital
        rolling_max = capital.expanding().max()
        drawdown = (capital - rolling_max) / rolling_max * 100
        
        ax.fill_between(strategy.data.index, 0, drawdown, 
                       color=colors.get(strategy_name, '#95a5a6'), alpha=0.5)
        ax.plot(strategy.data.index, drawdown, color=colors.get(strategy_name, '#95a5a6'), linewidth=1)
        ax.set_ylabel('Drawdown (%)', fontsize=11)
        ax.set_title(f'{strategy_name.replace("Strategy", "")} - Drawdown Analysis', fontsize=12, fontweight='bold')
        ax.set_ylim(drawdown.min() * 1.1, 5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    plt.xlabel('Date', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_dir / 'drawdown_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 4. Trading Signals Visualization (for best strategy)
    best_strategy_name = max(results.keys(), key=lambda k: results[k]['metrics']['sharpe_ratio'])
    best_strategy = results[best_strategy_name]['strategy']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Price with signals
    ax1.plot(best_strategy.data.index, best_strategy.data['close'], 
             label='XAU/USD Price', color='#2c3e50', linewidth=1)
    
    # Buy signals
    buy_signals = best_strategy.positions > 0
    ax1.scatter(best_strategy.data.index[buy_signals], 
               best_strategy.data['close'][buy_signals],
               marker='^', color='#2ecc71', s=100, label='Buy Signal', zorder=5)
    
    # Sell signals
    sell_signals = best_strategy.positions < 0
    ax1.scatter(best_strategy.data.index[sell_signals],
               best_strategy.data['close'][sell_signals],
               marker='v', color='#e74c3c', s=100, label='Sell Signal', zorder=5)
    
    ax1.set_title(f'{best_strategy_name.replace("Strategy", "")} - Trading Signals', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price ($)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # Portfolio value
    ax2.plot(best_strategy.data.index, best_strategy.capital, 
             color='#3498db', linewidth=2)
    ax2.axhline(y=100000, color='#e74c3c', linestyle='--', alpha=0.7)
    ax2.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'trading_signals.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Charts saved to {output_dir}")


def generate_report(results: dict, output_dir: Path):
    """Generate a text-based performance report."""
    
    report_lines = [
        "=" * 80,
        "XAU/USD TRADING BOT - BACKTEST REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
        ""
    ]
    
    for strategy_name, result in results.items():
        metrics = result['metrics']
        report_lines.extend([
            f"\n{'─' * 40}",
            f"Strategy: {strategy_name.replace('Strategy', '')}",
            f"{'─' * 40}",
            f"",
            f"Performance Metrics:",
            f"  • Total Return:      {metrics['total_return']*100:>10.2f}%",
            f"  • Annual Return:     {metrics['annual_return']*100:>10.2f}%",
            f"  • Volatility:        {metrics['volatility']*100:>10.2f}%",
            f"  • Sharpe Ratio:      {metrics['sharpe_ratio']:>10.2f}",
            f"  • Max Drawdown:      {metrics['max_drawdown']*100:>10.2f}%",
            f"  • Win Rate:          {metrics['win_rate']*100:>10.2f}%",
            f"",
            f"Capital:",
            f"  • Initial:           ${100000:>12,.2f}",
            f"  • Final:             ${metrics['final_capital']:>12,.2f}",
            f"  • P&L:               ${metrics['final_capital']-100000:>12,.2f}",
        ])
    
    # Determine winner
    best_strategy = max(results.keys(), key=lambda k: results[k]['metrics']['sharpe_ratio'])
    
    report_lines.extend([
        "",
        "=" * 80,
        f"WINNER (Highest Sharpe Ratio): {best_strategy.replace('Strategy', '')}",
        "=" * 80,
    ])
    
    report_text = "\n".join(report_lines)
    
    # Save report
    report_path = output_dir / "backtest_report.txt"
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    # Also save as JSON
    json_data = {strategy: result['metrics'] for strategy, result in results.items()}
    json_path = output_dir / "backtest_results.json"
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(report_text)
    print(f"\nReport saved to {report_path}")
    
    return report_text


def main():
    """Run the complete demo."""
    print("=" * 60)
    print("XAU/USD TRADING BOT - DEMO")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("results/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\n1. Loading sample data...")
    data = load_sample_data("1D")
    print(f"   Loaded {len(data)} data points")
    print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    
    # Add technical indicators
    print("\n2. Calculating technical indicators...")
    analyzer = TechnicalAnalyzer(data)
    data = analyzer.analyze_all()
    print("   Added: SMA, RSI, Bollinger Bands, MACD, ATR")
    
    # Run backtests
    print("\n3. Running backtests...")
    results, backtester = run_strategy_comparison(data)
    
    # Generate charts
    print("\n4. Generating performance charts...")
    generate_performance_charts(results, output_dir)
    
    # Generate report
    print("\n5. Generating performance report...")
    generate_report(results, output_dir)
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"\nAll outputs saved to: {output_dir.absolute()}")
    
    return results


if __name__ == "__main__":
    main()
