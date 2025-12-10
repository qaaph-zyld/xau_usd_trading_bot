"""
PROP FIRM CHALLENGE SIMULATOR

The BEST option for someone with $100:
- Pay $50-150 for a challenge
- Pass = Trade with $10,000-100,000 of their money
- Keep 70-90% of profits

This script simulates an FTMO-style challenge to see if our strategy can pass.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import ta


class PropFirmChallenge:
    """
    Simulates FTMO-style prop firm challenge.
    
    Rules (typical):
    - Profit target: 10% (Phase 1), 5% (Phase 2)
    - Max daily loss: 5%
    - Max total drawdown: 10%
    - Minimum trading days: 4
    - Time limit: 30 days (Phase 1), 60 days (Phase 2)
    """
    
    def __init__(self, account_size=10000, 
                 profit_target=0.10,
                 max_daily_loss=0.05,
                 max_total_drawdown=0.10,
                 min_trading_days=4,
                 time_limit_days=30):
        
        self.account_size = account_size
        self.profit_target = profit_target
        self.max_daily_loss = max_daily_loss
        self.max_total_drawdown = max_total_drawdown
        self.min_trading_days = min_trading_days
        self.time_limit_days = time_limit_days
    
    def run_challenge(self, data, risk_per_trade=0.01):
        """Run the challenge with our strategy."""
        
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
        
        # Challenge state
        capital = self.account_size
        start_capital = capital
        highest_capital = capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        highest = 0
        
        trades = []
        daily_pnl = []
        trading_days = 0
        
        # Track challenge status
        passed = False
        failed = False
        fail_reason = None
        day_count = 0
        
        for i in range(66, min(66 + self.time_limit_days, len(data))):
            day_count += 1
            close = data['close'].iloc[i]
            high = data['high'].iloc[i]
            low = data['low'].iloc[i]
            atr = data['atr'].iloc[i] if not pd.isna(data['atr'].iloc[i]) else close * 0.01
            ema_55 = data['ema_55'].iloc[i]
            rsi = data['rsi'].iloc[i]
            
            day_start_capital = capital
            
            # Manage position
            if position > 0:
                highest = max(highest, high)
                trail = highest - atr * 1.5
                eff_stop = max(stop_loss, trail)
                
                if low <= eff_stop:
                    exit_price = eff_stop
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'stop'})
                    position = 0
                    trading_days += 1
                
                elif high >= take_profit:
                    exit_price = take_profit
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'take_profit'})
                    position = 0
                    trading_days += 1
            
            elif position < 0:
                # Short management (simplified)
                if high >= stop_loss:
                    pnl = (entry_price - stop_loss) * abs(position)
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'stop'})
                    position = 0
                    trading_days += 1
                elif low <= take_profit:
                    pnl = (entry_price - take_profit) * abs(position)
                    capital += pnl
                    trades.append({'pnl': pnl, 'reason': 'take_profit'})
                    position = 0
                    trading_days += 1
            
            # New entry
            if position == 0 and not failed:
                signal = 0
                if data['cross_up'].iloc[i] and close > ema_55 and rsi < 70:
                    signal = 1
                elif data['cross_down'].iloc[i] and close < ema_55 and rsi > 30:
                    signal = -1
                
                if signal != 0:
                    if signal == 1:
                        stop_loss = close - atr * 1.5
                        take_profit = close + atr * 3.0
                        risk = close - stop_loss
                    else:
                        stop_loss = close + atr * 1.5
                        take_profit = close - atr * 3.0
                        risk = stop_loss - close
                    
                    if risk > 0:
                        size = (capital * risk_per_trade) / risk
                        position = size if signal > 0 else -size
                        entry_price = close
                        highest = close
            
            # Daily P/L
            day_pnl = capital - day_start_capital
            daily_pnl.append(day_pnl)
            
            # Check daily loss limit
            if day_pnl < -start_capital * self.max_daily_loss:
                failed = True
                fail_reason = f"Daily loss limit breached: ${day_pnl:.2f}"
                break
            
            # Update highest capital
            highest_capital = max(highest_capital, capital)
            
            # Check total drawdown
            drawdown = (highest_capital - capital) / start_capital
            if drawdown > self.max_total_drawdown:
                failed = True
                fail_reason = f"Max drawdown breached: {drawdown*100:.1f}%"
                break
            
            # Check if passed
            profit = (capital - start_capital) / start_capital
            if profit >= self.profit_target and trading_days >= self.min_trading_days:
                passed = True
                break
        
        # Close remaining position
        if position != 0:
            close = data['close'].iloc[min(66 + self.time_limit_days - 1, len(data) - 1)]
            if position > 0:
                pnl = (close - entry_price) * position
            else:
                pnl = (entry_price - close) * abs(position)
            capital += pnl
            trades.append({'pnl': pnl, 'reason': 'end'})
            trading_days += 1
        
        final_profit = (capital - start_capital) / start_capital
        max_dd = (highest_capital - min(capital, *[start_capital + sum(t['pnl'] for t in trades[:j+1]) 
                                                    for j in range(len(trades))])) / start_capital if trades else 0
        
        return {
            'passed': passed,
            'failed': failed,
            'fail_reason': fail_reason,
            'days_used': day_count,
            'trading_days': trading_days,
            'final_capital': capital,
            'profit_pct': final_profit * 100,
            'max_drawdown_pct': max_dd * 100,
            'trades': len(trades),
            'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0
        }


def run_multiple_challenges(data):
    """Run challenges on different periods to see consistency."""
    
    results = []
    
    # Need to include lookback period for indicators (66 days before challenge starts)
    # Test on different 30-day windows
    for challenge_start in range(100, len(data) - 30, 30):
        # Include lookback for indicators
        window = data.iloc[challenge_start-66:challenge_start+30]
        if len(window) < 96:
            continue
        
        challenge = PropFirmChallenge(
            account_size=10000,
            profit_target=0.10,  # 10%
            max_daily_loss=0.05,  # 5%
            max_total_drawdown=0.10,  # 10%
            time_limit_days=30
        )
        
        # Use higher risk for prop firm (3% per trade)
        result = challenge.run_challenge(window, risk_per_trade=0.03)
        result['start_date'] = data.index[challenge_start].strftime('%Y-%m-%d')
        results.append(result)
    
    return results


def main():
    print("=" * 70)
    print("🏆 PROP FIRM CHALLENGE SIMULATOR")
    print("=" * 70)
    
    print("""
    This simulates an FTMO-style prop firm challenge.
    
    Challenge Rules:
    ├─ Account Size:     $10,000
    ├─ Profit Target:    10% ($1,000)
    ├─ Max Daily Loss:   5% ($500)
    ├─ Max Drawdown:     10% ($1,000)
    ├─ Min Trading Days: 4
    └─ Time Limit:       30 days
    
    If you pass, you get to trade their $10,000 account!
    """)
    
    # Load data
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    # Run multiple challenges
    print("Running challenges on different market periods...\n")
    
    results = run_multiple_challenges(data)
    
    # Summary
    passed = [r for r in results if r['passed']]
    failed = [r for r in results if r['failed']]
    incomplete = [r for r in results if not r['passed'] and not r['failed']]
    
    print("=" * 70)
    print("CHALLENGE RESULTS")
    print("=" * 70)
    print(f"{'Start Date':<12} {'Status':<12} {'Profit%':>10} {'MaxDD%':>10} {'Trades':>8} {'Days':>6}")
    print("-" * 70)
    
    for r in results:
        status = "✅ PASSED" if r['passed'] else ("❌ FAILED" if r['failed'] else "⏳ TIME")
        print(f"{r['start_date']:<12} {status:<12} {r['profit_pct']:>+10.2f} "
              f"{r['max_drawdown_pct']:>10.2f} {r['trades']:>8} {r['days_used']:>6}")
    
    print("-" * 70)
    print(f"\n📊 SUMMARY")
    print(f"   Total Challenges:  {len(results)}")
    print(f"   Passed:            {len(passed)} ({len(passed)/len(results)*100:.1f}%)")
    print(f"   Failed:            {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"   Ran out of time:   {len(incomplete)}")
    
    # Analysis
    if passed:
        avg_profit = np.mean([r['profit_pct'] for r in passed])
        print(f"\n   Avg profit (passed): {avg_profit:.2f}%")
    
    if failed:
        print(f"\n   Failure reasons:")
        for r in failed:
            print(f"      - {r['fail_reason']}")
    
    # The verdict
    pass_rate = len(passed) / len(results) * 100 if results else 0
    
    print("\n" + "=" * 70)
    print("VERDICT FOR PROP FIRM")
    print("=" * 70)
    
    if pass_rate >= 50:
        print(f"""
    ✅ STRATEGY CAN PASS PROP FIRM CHALLENGES!
    
    Pass rate: {pass_rate:.1f}%
    
    WITH YOUR $100:
    1. Pay ~$100 for challenge fee (FTMO $10K account)
    2. Use this strategy with proper risk management
    3. ~{pass_rate:.0f}% chance of passing
    4. If passed: Trade their $10,000, keep 80% of profits
    
    EXPECTED VALUE:
    - Challenge cost: $100
    - Pass probability: {pass_rate:.0f}%
    - If win 10% on $10K: $800 profit to you
    - Expected value: ${pass_rate/100 * 800 - (1-pass_rate/100) * 100:.2f}
    """)
    elif pass_rate >= 20:
        print(f"""
    ⚠️  STRATEGY NEEDS OPTIMIZATION FOR PROP FIRM
    
    Pass rate: {pass_rate:.1f}%
    
    Current issues:
    - Not aggressive enough for 10% target in 30 days
    - Need higher risk per trade for challenges
    
    RECOMMENDATION:
    - Paper trade first
    - Increase risk to 3-5% per trade for challenges
    - Consider longer challenge periods (60 days)
    """)
    else:
        print(f"""
    ❌ STRATEGY NOT SUITABLE FOR PROP FIRM AS-IS
    
    Pass rate: {pass_rate:.1f}%
    
    The strategy is designed for steady returns, not
    the aggressive 10% monthly target prop firms require.
    
    OPTIONS:
    1. Use for personal trading with $1,000+ capital
    2. Develop a separate high-risk prop firm strategy
    3. Choose prop firms with lower profit targets
    """)


if __name__ == "__main__":
    main()
