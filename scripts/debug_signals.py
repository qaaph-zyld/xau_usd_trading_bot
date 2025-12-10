"""Debug why no signals are generated."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


def main():
    # Load data
    data_path = Path("data") / "XAU_USD_1D_sample.csv"
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    print(f"Data: {len(data)} bars")
    
    # Calculate indicators
    data['ema_8'] = ta.trend.ema_indicator(data['close'], window=8)
    data['ema_21'] = ta.trend.ema_indicator(data['close'], window=21)
    data['ema_55'] = ta.trend.ema_indicator(data['close'], window=55)
    data['adx'] = ta.trend.adx(data['high'], data['low'], data['close'], window=14)
    data['di_plus'] = ta.trend.adx_pos(data['high'], data['low'], data['close'], window=14)
    data['di_minus'] = ta.trend.adx_neg(data['high'], data['low'], data['close'], window=14)
    data['rsi'] = ta.momentum.rsi(data['close'], window=14)
    macd = ta.trend.MACD(data['close'])
    data['macd_hist'] = macd.macd_diff()
    data['atr'] = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=14)
    bb = ta.volatility.BollingerBands(data['close'], window=20, window_dev=2)
    data['bb_pct'] = bb.bollinger_pband()
    
    # Check trend conditions
    print("\n--- Checking Trend Conditions ---")
    
    uptrends = 0
    downtrends = 0
    momentum_matches = 0
    pullbacks = 0
    
    for i in range(60, len(data)):
        # Trend check
        ema_8 = data['ema_8'].iloc[i]
        ema_21 = data['ema_21'].iloc[i]
        ema_55 = data['ema_55'].iloc[i]
        adx = data['adx'].iloc[i]
        di_plus = data['di_plus'].iloc[i]
        di_minus = data['di_minus'].iloc[i]
        
        # Check uptrend
        if ema_8 > ema_21 > ema_55 and adx > 20 and di_plus > di_minus:
            uptrends += 1
            trend = 1
        elif ema_8 < ema_21 < ema_55 and adx > 20 and di_minus > di_plus:
            downtrends += 1
            trend = -1
        else:
            trend = 0
            continue
        
        # Check momentum
        macd_hist = data['macd_hist'].iloc[i]
        macd_hist_prev = data['macd_hist'].iloc[i-1]
        rsi = data['rsi'].iloc[i]
        
        if trend == 1 and macd_hist > macd_hist_prev and rsi < 70:
            momentum_matches += 1
            
            # Check pullback
            close = data['close'].iloc[i]
            bb_pct = data['bb_pct'].iloc[i]
            
            if bb_pct < 0.3 or rsi < 45:
                pullbacks += 1
    
    print(f"Uptrend bars: {uptrends}")
    print(f"Downtrend bars: {downtrends}")
    print(f"Momentum matches: {momentum_matches}")
    print(f"Pullbacks: {pullbacks}")
    
    # Let's look at a simpler approach
    print("\n--- Simple Signal Check ---")
    
    # Simple: EMA crossover + trend filter
    signals = 0
    for i in range(60, len(data)):
        ema_8 = data['ema_8'].iloc[i]
        ema_21 = data['ema_21'].iloc[i]
        ema_8_prev = data['ema_8'].iloc[i-1]
        ema_21_prev = data['ema_21'].iloc[i-1]
        ema_55 = data['ema_55'].iloc[i]
        rsi = data['rsi'].iloc[i]
        
        # Long: EMA 8 crosses above EMA 21, price above EMA 55, RSI not overbought
        if ema_8 > ema_21 and ema_8_prev <= ema_21_prev:
            if data['close'].iloc[i] > ema_55 and rsi < 70:
                signals += 1
        
        # Short: EMA 8 crosses below EMA 21
        if ema_8 < ema_21 and ema_8_prev >= ema_21_prev:
            if data['close'].iloc[i] < ema_55 and rsi > 30:
                signals += 1
    
    print(f"EMA crossover signals: {signals}")
    
    # Even simpler: just RSI extremes + trend
    print("\n--- RSI Extreme Signals ---")
    rsi_signals = 0
    for i in range(60, len(data)):
        rsi = data['rsi'].iloc[i]
        rsi_prev = data['rsi'].iloc[i-1]
        close = data['close'].iloc[i]
        ema_55 = data['ema_55'].iloc[i]
        
        # RSI crossing 30 from below in uptrend
        if rsi > 30 and rsi_prev <= 30 and close > ema_55:
            rsi_signals += 1
        
        # RSI crossing 70 from above in downtrend  
        if rsi < 70 and rsi_prev >= 70 and close < ema_55:
            rsi_signals += 1
    
    print(f"RSI extreme signals: {rsi_signals}")
    
    # Check actual price action
    print("\n--- Price Summary ---")
    print(f"Start price: ${data['close'].iloc[60]:.2f}")
    print(f"End price: ${data['close'].iloc[-1]:.2f}")
    print(f"Change: {((data['close'].iloc[-1] / data['close'].iloc[60]) - 1) * 100:.1f}%")
    print(f"High: ${data['high'].max():.2f}")
    print(f"Low: ${data['low'].min():.2f}")


if __name__ == "__main__":
    main()
