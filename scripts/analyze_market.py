"""Analyze the market data to understand what strategies could work."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


def main():
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("MARKET ANALYSIS")
    print("=" * 70)
    
    # Overall trend
    print("\n--- PRICE MOVEMENT ---")
    start = data['close'].iloc[0]
    end = data['close'].iloc[-1]
    high = data['high'].max()
    low = data['low'].min()
    
    print(f"Start: ${start:.2f}")
    print(f"End: ${end:.2f}")
    print(f"Change: {((end/start)-1)*100:+.2f}%")
    print(f"High: ${high:.2f} (+{((high/start)-1)*100:.1f}% from start)")
    print(f"Low: ${low:.2f} ({((low/start)-1)*100:.1f}% from start)")
    
    # Perfect hindsight trading
    print("\n--- PERFECT HINDSIGHT (Theoretical Maximum) ---")
    
    # Calculate returns from all swings
    data['returns'] = data['close'].pct_change()
    data['direction'] = np.sign(data['returns'])
    
    # If we perfectly traded every move
    perfect_returns = data['returns'].abs().sum()
    print(f"Sum of all daily moves: {perfect_returns*100:.1f}%")
    print(f"With $10,000: ${10000 * (1 + perfect_returns):,.2f}")
    
    # Major swings
    print("\n--- MAJOR PRICE SWINGS ---")
    
    data['ema_50'] = ta.trend.ema_indicator(data['close'], window=50)
    
    # Find major peaks and troughs
    # Simple approach: local max/min over 20 bars
    data['local_max'] = data['high'].rolling(20, center=True).max() == data['high']
    data['local_min'] = data['low'].rolling(20, center=True).min() == data['low']
    
    peaks = data[data['local_max']]['high']
    troughs = data[data['local_min']]['low']
    
    print(f"Major peaks: {len(peaks)}")
    print(f"Major troughs: {len(troughs)}")
    
    # Show major swings
    print("\nMajor turning points:")
    all_points = []
    for idx, val in peaks.items():
        all_points.append((idx, val, 'PEAK'))
    for idx, val in troughs.items():
        all_points.append((idx, val, 'TROUGH'))
    
    all_points.sort(key=lambda x: x[0])
    
    for i, (date, price, ptype) in enumerate(all_points[:15]):
        print(f"  {date.strftime('%Y-%m-%d')}: ${price:.2f} ({ptype})")
    
    # What percentage of days are up vs down
    print("\n--- DAILY STATISTICS ---")
    up_days = (data['returns'] > 0).sum()
    down_days = (data['returns'] < 0).sum()
    print(f"Up days: {up_days} ({up_days/len(data)*100:.1f}%)")
    print(f"Down days: {down_days} ({down_days/len(data)*100:.1f}%)")
    print(f"Average up day: +{data[data['returns']>0]['returns'].mean()*100:.2f}%")
    print(f"Average down day: {data[data['returns']<0]['returns'].mean()*100:.2f}%")
    
    # Best strategy type
    print("\n--- REGIME ANALYSIS ---")
    
    data['atr'] = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=14)
    data['atr_pct'] = data['atr'] / data['close'] * 100
    
    print(f"Average ATR%: {data['atr_pct'].mean():.2f}%")
    print(f"Min ATR%: {data['atr_pct'].min():.2f}%")
    print(f"Max ATR%: {data['atr_pct'].max():.2f}%")
    
    # Trend persistence
    data['trend_day'] = (data['close'] > data['close'].shift(1)).astype(int)
    data['trend_streak'] = data['trend_day'].groupby((data['trend_day'] != data['trend_day'].shift()).cumsum()).cumcount() + 1
    
    print(f"\nLongest up streak: {data[data['trend_day']==1]['trend_streak'].max()} days")
    print(f"Longest down streak: {data[data['trend_day']==0]['trend_streak'].max()} days")
    
    # What if we just bought and held when above 200 SMA?
    print("\n--- SIMPLE 200 SMA FILTER STRATEGY ---")
    data['sma_200'] = ta.trend.sma_indicator(data['close'], window=200)
    data['above_200'] = data['close'] > data['sma_200']
    
    # Calculate returns only when above 200 SMA
    data['filtered_returns'] = data['returns'] * data['above_200'].shift(1).fillna(0)
    total_filtered = (1 + data['filtered_returns']).prod() - 1
    print(f"Return when above 200 SMA: {total_filtered*100:+.2f}%")
    
    # What about buying after 3 down days?
    print("\n--- MEAN REVERSION TEST ---")
    data['down_streak'] = 0
    down_streak = 0
    for i in range(len(data)):
        if data['returns'].iloc[i] < 0:
            down_streak += 1
        else:
            down_streak = 0
        data.iloc[i, data.columns.get_loc('down_streak')] = down_streak
    
    # Return after 3+ down days
    data['buy_after_3_down'] = data['down_streak'].shift(1) >= 3
    post_drop_returns = data[data['buy_after_3_down']]['returns']
    print(f"Instances of 3+ down days: {len(post_drop_returns)}")
    print(f"Avg return after 3+ down days: {post_drop_returns.mean()*100:+.2f}%")
    print(f"Win rate after 3+ down days: {(post_drop_returns > 0).sum()/len(post_drop_returns)*100:.1f}%")
    
    # What about momentum? Buy after 3 up days?
    print("\n--- MOMENTUM TEST ---")
    data['up_streak'] = 0
    up_streak = 0
    for i in range(len(data)):
        if data['returns'].iloc[i] > 0:
            up_streak += 1
        else:
            up_streak = 0
        data.iloc[i, data.columns.get_loc('up_streak')] = up_streak
    
    data['buy_after_3_up'] = data['up_streak'].shift(1) >= 3
    post_run_returns = data[data['buy_after_3_up']]['returns']
    print(f"Instances of 3+ up days: {len(post_run_returns)}")
    print(f"Avg return after 3+ up days: {post_run_returns.mean()*100:+.2f}%")
    print(f"Win rate after 3+ up days: {(post_run_returns > 0).sum()/len(post_run_returns)*100:.1f}%")


if __name__ == "__main__":
    main()
