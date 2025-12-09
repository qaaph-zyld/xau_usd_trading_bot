"""
Generate realistic XAU/USD sample data for demonstration purposes.
This allows users to run the bot without needing an API key.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def generate_gold_price_data(
    start_date: str = "2023-01-01",
    end_date: str = "2024-12-01",
    initial_price: float = 1850.0,
    volatility: float = 0.015,
    trend: float = 0.0002,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate realistic XAU/USD OHLCV data using geometric Brownian motion
    with mean reversion characteristics typical of gold prices.
    
    Args:
        start_date: Start date for the data
        end_date: End date for the data
        initial_price: Starting gold price
        volatility: Daily volatility (default ~1.5%)
        trend: Daily trend (default slight upward bias)
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(seed)
    
    # Generate date range (hourly data)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    n = len(dates)
    
    # Generate returns using GBM with mean reversion
    dt = 1/24  # hourly
    mean_price = initial_price * 1.1  # Mean reversion target
    reversion_speed = 0.01
    
    prices = [initial_price]
    for i in range(1, n):
        prev_price = prices[-1]
        
        # Mean reversion component
        mean_reversion = reversion_speed * (mean_price - prev_price) * dt
        
        # Random component (Brownian motion)
        random_shock = volatility * np.sqrt(dt) * np.random.normal()
        
        # Trend component
        drift = trend * dt * prev_price
        
        # New price
        new_price = prev_price * (1 + random_shock) + mean_reversion + drift
        
        # Add occasional jumps (news events)
        if np.random.random() < 0.005:  # 0.5% chance of jump
            jump = np.random.choice([-1, 1]) * np.random.uniform(0.01, 0.03)
            new_price *= (1 + jump)
        
        prices.append(max(new_price, initial_price * 0.7))  # Floor at 70% of initial
    
    prices = np.array(prices)
    
    # Generate OHLC from close prices
    data = []
    for i, date in enumerate(dates):
        close = prices[i]
        
        # Generate realistic intraday range
        daily_range = close * np.random.uniform(0.002, 0.008)
        
        # High and low with some randomness
        high_offset = np.random.uniform(0.3, 0.8) * daily_range
        low_offset = np.random.uniform(0.3, 0.8) * daily_range
        
        high = close + high_offset
        low = close - low_offset
        
        # Open between high and low
        open_price = np.random.uniform(low, high)
        
        # Volume with some patterns (higher during market hours)
        hour = date.hour
        base_volume = 50000
        if 8 <= hour <= 16:  # London/NY overlap
            volume_mult = np.random.uniform(1.5, 2.5)
        elif 0 <= hour <= 7:  # Asian session
            volume_mult = np.random.uniform(0.8, 1.2)
        else:
            volume_mult = np.random.uniform(1.0, 1.5)
        
        volume = int(base_volume * volume_mult * np.random.uniform(0.8, 1.2))
        
        data.append({
            'datetime': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    return df


def generate_multiple_timeframes(base_data: pd.DataFrame) -> dict:
    """
    Generate multiple timeframe data from hourly data.
    
    Args:
        base_data: Hourly OHLCV data
        
    Returns:
        Dictionary with different timeframe DataFrames
    """
    timeframes = {
        '1H': base_data.copy(),
        '4H': resample_ohlcv(base_data, '4H'),
        '1D': resample_ohlcv(base_data, '1D'),
        '1W': resample_ohlcv(base_data, '1W')
    }
    return timeframes


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample OHLCV data to a different timeframe."""
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    return resampled


def main():
    """Generate and save sample data."""
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    print("Generating XAU/USD sample data...")
    
    # Generate hourly data
    hourly_data = generate_gold_price_data(
        start_date="2023-01-01",
        end_date="2024-12-01",
        initial_price=1850.0
    )
    
    # Generate multiple timeframes
    timeframes = generate_multiple_timeframes(hourly_data)
    
    # Save all timeframes
    for tf, data in timeframes.items():
        filename = output_dir / f"XAU_USD_{tf}_sample.csv"
        data.to_csv(filename)
        print(f"  Saved {filename} ({len(data)} rows)")
    
    print("\nSample data generation complete!")
    print(f"\nData summary:")
    print(f"  Date range: {hourly_data.index[0]} to {hourly_data.index[-1]}")
    print(f"  Price range: ${hourly_data['low'].min():.2f} - ${hourly_data['high'].max():.2f}")
    print(f"  Average price: ${hourly_data['close'].mean():.2f}")
    
    return timeframes


if __name__ == "__main__":
    main()
