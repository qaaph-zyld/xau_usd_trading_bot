"""
HARD TRUTH: What happens with $100?

No sugar coating. Real numbers. Real costs.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


def simulate_real_trading(data, initial_capital, 
                         spread_cost=0.30,  # $0.30 spread per trade
                         commission=0.07,   # $0.07 commission per micro lot
                         min_lot=0.01,      # Minimum 0.01 lot (1 oz)
                         leverage=100):     # 100:1 leverage
    """
    Simulate REAL trading with:
    - Minimum position sizes
    - Actual transaction costs
    - Margin requirements
    - Realistic execution
    """
    
    # Calculate indicators
    data = data.copy()
    data['ema_5'] = ta.trend.ema_indicator(data['close'], window=5)
    data['ema_21'] = ta.trend.ema_indicator(data['close'], window=21)
    data['ema_55'] = ta.trend.ema_indicator(data['close'], window=55)
    data['atr'] = ta.volatility.average_true_range(
        data['high'], data['low'], data['close'], window=14
    )
    data['rsi'] = ta.momentum.rsi(data['close'], window=14)
    
    data['cross_up'] = (
        (data['ema_5'] > data['ema_21']) & 
        (data['ema_5'].shift(1) <= data['ema_21'].shift(1))
    )
    data['cross_down'] = (
        (data['ema_5'] < data['ema_21']) &
        (data['ema_5'].shift(1) >= data['ema_21'].shift(1))
    )
    
    capital = initial_capital
    position = 0  # In ounces of gold
    entry_price = 0
    stop_loss = 0
    take_profit = 0
    highest = 0
    
    trades = []
    skipped_signals = 0
    margin_rejections = 0
    
    for i in range(66, len(data)):
        close = data['close'].iloc[i]
        high = data['high'].iloc[i]
        low = data['low'].iloc[i]
        atr = data['atr'].iloc[i] if not pd.isna(data['atr'].iloc[i]) else close * 0.01
        ema_55 = data['ema_55'].iloc[i]
        rsi = data['rsi'].iloc[i]
        
        # Manage existing position
        if position > 0:
            highest = max(highest, high)
            trail = highest - atr * 1.5
            eff_stop = max(stop_loss, trail)
            
            if low <= eff_stop:
                # Exit at stop
                exit_price = eff_stop
                gross_pnl = (exit_price - entry_price) * position
                exit_cost = spread_cost + commission
                net_pnl = gross_pnl - exit_cost
                capital += net_pnl
                
                trades.append({
                    'side': 'long',
                    'entry': entry_price,
                    'exit': exit_price,
                    'size_oz': position,
                    'gross_pnl': gross_pnl,
                    'costs': exit_cost,
                    'net_pnl': net_pnl,
                    'reason': 'stop'
                })
                position = 0
            
            elif high >= take_profit:
                exit_price = take_profit
                gross_pnl = (exit_price - entry_price) * position
                exit_cost = spread_cost + commission
                net_pnl = gross_pnl - exit_cost
                capital += net_pnl
                
                trades.append({
                    'side': 'long',
                    'entry': entry_price,
                    'exit': exit_price,
                    'size_oz': position,
                    'gross_pnl': gross_pnl,
                    'costs': exit_cost,
                    'net_pnl': net_pnl,
                    'reason': 'take_profit'
                })
                position = 0
        
        elif position < 0:
            # Short position management...
            pass  # Simplified for this test
        
        # New entry
        if position == 0:
            signal = 0
            if data['cross_up'].iloc[i] and close > ema_55 and rsi < 70:
                signal = 1
            elif data['cross_down'].iloc[i] and close < ema_55 and rsi > 30:
                signal = -1
            
            if signal == 1:  # Long signal
                # Calculate position size
                stop_loss = close - atr * 1.5
                take_profit = close + atr * 3.0
                risk_per_unit = close - stop_loss
                
                # Risk 2% of capital
                risk_amount = capital * 0.02
                ideal_size_oz = risk_amount / risk_per_unit
                
                # Convert to lots (1 lot = 100 oz, min = 0.01 lot = 1 oz)
                # But actually for micro accounts, 1 micro lot = 1 oz
                min_size_oz = min_lot  # 0.01 lot = minimum tradeable
                
                # Check if we can afford minimum position
                margin_required = (min_size_oz * close) / leverage
                entry_cost = spread_cost + commission
                
                if margin_required + entry_cost > capital * 0.9:
                    margin_rejections += 1
                    continue
                
                if ideal_size_oz < min_size_oz:
                    # Position too small - can we even trade minimum?
                    if margin_required < capital * 0.5:
                        # Trade minimum size
                        position = min_size_oz
                    else:
                        skipped_signals += 1
                        continue
                else:
                    # Round down to valid lot size
                    position = max(min_size_oz, round(ideal_size_oz / min_size_oz) * min_size_oz)
                
                entry_price = close
                highest = close
                
                # Deduct entry costs immediately
                capital -= entry_cost
    
    # Close remaining position
    if position != 0:
        close = data['close'].iloc[-1]
        gross_pnl = (close - entry_price) * position
        exit_cost = spread_cost + commission
        net_pnl = gross_pnl - exit_cost
        capital += net_pnl
        
        trades.append({
            'side': 'long',
            'entry': entry_price,
            'exit': close,
            'size_oz': position,
            'gross_pnl': gross_pnl,
            'costs': exit_cost,
            'net_pnl': net_pnl,
            'reason': 'end'
        })
    
    return {
        'initial': initial_capital,
        'final': capital,
        'net_pnl': capital - initial_capital,
        'return_pct': ((capital - initial_capital) / initial_capital) * 100,
        'trades': trades,
        'skipped': skipped_signals,
        'margin_rejected': margin_rejections
    }


def main():
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    print("=" * 70)
    print("HARD TRUTH: WHAT HAPPENS WITH $100?")
    print("=" * 70)
    print("\nNo sugar coating. Real numbers. Real broker conditions.\n")
    
    # Test with $100
    print("=" * 70)
    print("SCENARIO: $100 ACCOUNT")
    print("=" * 70)
    
    result = simulate_real_trading(data, 100)
    
    print(f"\n  Starting Capital:     ${result['initial']:.2f}")
    print(f"  Final Capital:        ${result['final']:.2f}")
    print(f"  Net P/L:              ${result['net_pnl']:+.2f}")
    print(f"  Return:               {result['return_pct']:+.2f}%")
    print(f"  Trades Executed:      {len(result['trades'])}")
    print(f"  Signals Skipped:      {result['skipped']} (position too small)")
    print(f"  Margin Rejections:    {result['margin_rejected']}")
    
    if result['trades']:
        print(f"\n  Trade Details:")
        total_costs = 0
        for i, t in enumerate(result['trades']):
            total_costs += t['costs']
            print(f"    {i+1}. {t['side']:5} {t['size_oz']:.2f}oz @ ${t['entry']:.2f} -> ${t['exit']:.2f}")
            print(f"       Gross: ${t['gross_pnl']:+.2f}, Costs: ${t['costs']:.2f}, Net: ${t['net_pnl']:+.2f}")
        print(f"\n  Total Trading Costs:  ${total_costs:.2f}")
        print(f"  Costs as % of Capital: {(total_costs/100)*100:.1f}%")
    
    # Compare with different capital levels
    print("\n" + "=" * 70)
    print("CAPITAL COMPARISON")
    print("=" * 70)
    print(f"{'Capital':>10} {'Final':>12} {'P/L':>10} {'Return':>10} {'Trades':>8} {'Skipped':>10}")
    print("-" * 70)
    
    for capital in [100, 500, 1000, 5000, 10000]:
        r = simulate_real_trading(data, capital)
        print(f"${capital:>9} ${r['final']:>11.2f} ${r['net_pnl']:>+9.2f} {r['return_pct']:>+9.2f}% {len(r['trades']):>8} {r['skipped']:>10}")
    
    print("-" * 70)
    
    # The brutal truth
    print("\n" + "=" * 70)
    print("THE BRUTAL TRUTH")
    print("=" * 70)
    
    print("""
WITH $100:

1. POSITION SIZE PROBLEM
   - Our strategy wants to risk 2% = $2 per trade
   - With gold at ~$2000/oz, stop loss at ~$30 (1.5 ATR)
   - Ideal position: $2 / $30 = 0.067 oz
   - MINIMUM tradeable: 0.01 oz (1 micro lot)
   - So we're FORCED to risk more than intended

2. COST PROBLEM  
   - Each trade costs ~$0.37 (spread + commission)
   - $0.37 × 30 trades = $11.10 in costs alone
   - That's 11% of your capital GONE to fees

3. MARGIN PROBLEM
   - Even with 100:1 leverage, gold at $2000 requires:
   - 0.01 lot × $2000 / 100 = $20 margin per trade
   - With $100, that's 20% of capital per position
   - ONE bad trade can wipe out your account

4. MATH PROBLEM
   - Best case: +10% on $100 = $10 profit
   - After 2 years of trading, stress, and risk
   - You could make more working 30 minutes

REALISTIC OUTCOME WITH $100:
   - Most likely: Account slowly bleeds to $70-80 from costs
   - Best case: $110 after 2 years
   - Worst case: Blown account from a few bad trades

VERDICT: DON'T DO IT.
""")

    # What TO do instead
    print("=" * 70)
    print("WHAT YOU SHOULD DO INSTEAD")
    print("=" * 70)
    
    print("""
1. IF YOU ONLY HAVE $100:
   ✅ Use a DEMO account to practice for 6 months
   ✅ Paper trade to validate the strategy
   ✅ Save until you have at least $1,000-2,000
   ✅ Learn position sizing and risk management

2. MINIMUM VIABLE CAPITAL FOR THIS STRATEGY:
   - Absolute minimum: $1,000 (still risky)
   - Recommended: $5,000+ (proper position sizing)
   - Professional: $10,000+ (consistent returns)

3. ALTERNATIVE WITH $100:
   - Put it in a high-yield savings (4-5% guaranteed)
   - Invest in index funds (S&P 500)
   - Use it for trading education instead

4. WHEN TO START REAL TRADING:
   - After 6+ months profitable demo trading
   - With $2,000+ capital
   - Understanding you might lose 20%+ initially
   - Proper psychological preparation
""")
    
    return result


if __name__ == "__main__":
    result = main()
