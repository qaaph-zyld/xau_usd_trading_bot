"""
PAPER TRADING MODE

Practice the strategy without risking real money.
Track your trades and see if you can be profitable.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import ta


def load_trade_journal():
    """Load or create trade journal."""
    journal_path = Path("data") / "paper_trades.json"
    if journal_path.exists():
        with open(journal_path, 'r') as f:
            return json.load(f)
    return {
        'trades': [],
        'current_position': None,
        'paper_capital': 10000,
        'start_date': datetime.now().isoformat()
    }


def save_trade_journal(journal):
    """Save trade journal."""
    journal_path = Path("data") / "paper_trades.json"
    with open(journal_path, 'w') as f:
        json.dump(journal, f, indent=2, default=str)


def get_current_signal(data):
    """Get the current trading signal."""
    # Calculate indicators
    data = data.copy()
    data['ema_5'] = ta.trend.ema_indicator(data['close'], window=5)
    data['ema_21'] = ta.trend.ema_indicator(data['close'], window=21)
    data['ema_55'] = ta.trend.ema_indicator(data['close'], window=55)
    data['atr'] = ta.volatility.average_true_range(
        data['high'], data['low'], data['close'], window=14
    )
    data['rsi'] = ta.momentum.rsi(data['close'], window=14)
    
    # Get latest values
    latest = data.iloc[-1]
    prev = data.iloc[-2]
    
    close = latest['close']
    ema_5 = latest['ema_5']
    ema_21 = latest['ema_21']
    ema_55 = latest['ema_55']
    atr = latest['atr']
    rsi = latest['rsi']
    
    prev_ema_5 = prev['ema_5']
    prev_ema_21 = prev['ema_21']
    
    # Check for crossover
    cross_up = ema_5 > ema_21 and prev_ema_5 <= prev_ema_21
    cross_down = ema_5 < ema_21 and prev_ema_5 >= prev_ema_21
    
    signal = None
    
    if cross_up and close > ema_55 and rsi < 70:
        signal = {
            'direction': 'LONG',
            'entry': close,
            'stop_loss': close - atr * 1.5,
            'take_profit': close + atr * 3.0,
            'atr': atr,
            'rsi': rsi
        }
    elif cross_down and close < ema_55 and rsi > 30:
        signal = {
            'direction': 'SHORT',
            'entry': close,
            'stop_loss': close + atr * 1.5,
            'take_profit': close - atr * 3.0,
            'atr': atr,
            'rsi': rsi
        }
    
    return signal, latest, data


def display_dashboard(journal, data, signal):
    """Display paper trading dashboard."""
    latest = data.iloc[-1]
    
    print("\n" + "=" * 70)
    print("📊 PAPER TRADING DASHBOARD")
    print("=" * 70)
    
    # Account summary
    print(f"\n💰 PAPER ACCOUNT")
    print(f"   Starting Capital:  ${10000:,.2f}")
    print(f"   Current Capital:   ${journal['paper_capital']:,.2f}")
    pnl = journal['paper_capital'] - 10000
    print(f"   Total P/L:         ${pnl:+,.2f} ({pnl/100:+.2f}%)")
    print(f"   Total Trades:      {len(journal['trades'])}")
    
    if journal['trades']:
        winners = [t for t in journal['trades'] if t['pnl'] > 0]
        print(f"   Win Rate:          {len(winners)/len(journal['trades'])*100:.1f}%")
    
    # Current position
    print(f"\n📍 CURRENT POSITION")
    if journal['current_position']:
        pos = journal['current_position']
        print(f"   Direction: {pos['direction']}")
        print(f"   Entry:     ${pos['entry']:.2f}")
        print(f"   Stop Loss: ${pos['stop_loss']:.2f}")
        print(f"   Take Profit: ${pos['take_profit']:.2f}")
        current_price = latest['close']
        if pos['direction'] == 'LONG':
            unrealized = (current_price - pos['entry']) * pos.get('size', 1)
        else:
            unrealized = (pos['entry'] - current_price) * pos.get('size', 1)
        print(f"   Unrealized P/L: ${unrealized:+.2f}")
    else:
        print("   No open position")
    
    # Market status
    print(f"\n📈 MARKET STATUS")
    print(f"   Date:    {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"   Price:   ${latest['close']:.2f}")
    print(f"   RSI:     {latest['rsi']:.1f}")
    print(f"   Trend:   {'BULLISH' if latest['close'] > latest['ema_55'] else 'BEARISH'}")
    
    # Current signal
    print(f"\n🚦 SIGNAL")
    if signal:
        print(f"   ⚡ {signal['direction']} SIGNAL!")
        print(f"   Entry:       ${signal['entry']:.2f}")
        print(f"   Stop Loss:   ${signal['stop_loss']:.2f}")
        print(f"   Take Profit: ${signal['take_profit']:.2f}")
        print(f"   Risk:        ${abs(signal['entry'] - signal['stop_loss']):.2f} per unit")
    else:
        print("   No new signal today - HOLD/WAIT")
    
    # Recent trades
    if journal['trades']:
        print(f"\n📜 RECENT TRADES")
        for t in journal['trades'][-5:]:
            print(f"   {t['date']}: {t['direction']} ${t['entry']:.2f} -> ${t['exit']:.2f} = ${t['pnl']:+.2f}")


def interactive_mode(journal, data, signal):
    """Interactive paper trading."""
    
    print("\n" + "-" * 70)
    print("ACTIONS:")
    
    if journal['current_position']:
        print("  1. Close position at current price")
        print("  2. Update stop loss")
        print("  3. Check if stopped out")
        print("  4. Skip (hold position)")
    else:
        if signal:
            print("  1. Enter trade based on signal")
        print("  4. Skip (no trade)")
    
    print("  5. View trade history")
    print("  6. Exit")
    
    choice = input("\nChoice (1-6): ").strip()
    
    if choice == '1':
        if journal['current_position']:
            # Close position
            pos = journal['current_position']
            exit_price = data.iloc[-1]['close']
            if pos['direction'] == 'LONG':
                pnl = (exit_price - pos['entry']) * pos.get('size', 1)
            else:
                pnl = (pos['entry'] - exit_price) * pos.get('size', 1)
            
            journal['trades'].append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'direction': pos['direction'],
                'entry': pos['entry'],
                'exit': exit_price,
                'pnl': pnl,
                'reason': 'manual_close'
            })
            journal['paper_capital'] += pnl
            journal['current_position'] = None
            print(f"\n✅ Position closed at ${exit_price:.2f}")
            print(f"   P/L: ${pnl:+.2f}")
        
        elif signal:
            # Enter new position
            size = (journal['paper_capital'] * 0.02) / abs(signal['entry'] - signal['stop_loss'])
            journal['current_position'] = {
                'direction': signal['direction'],
                'entry': signal['entry'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'size': size,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            print(f"\n✅ Entered {signal['direction']} position")
            print(f"   Entry: ${signal['entry']:.2f}")
            print(f"   Size: {size:.4f} units")
    
    elif choice == '3' and journal['current_position']:
        # Check if stopped
        pos = journal['current_position']
        current_price = data.iloc[-1]['close']
        
        stopped = False
        tp_hit = False
        
        if pos['direction'] == 'LONG':
            if data.iloc[-1]['low'] <= pos['stop_loss']:
                stopped = True
                exit_price = pos['stop_loss']
            elif data.iloc[-1]['high'] >= pos['take_profit']:
                tp_hit = True
                exit_price = pos['take_profit']
        else:
            if data.iloc[-1]['high'] >= pos['stop_loss']:
                stopped = True
                exit_price = pos['stop_loss']
            elif data.iloc[-1]['low'] <= pos['take_profit']:
                tp_hit = True
                exit_price = pos['take_profit']
        
        if stopped or tp_hit:
            if pos['direction'] == 'LONG':
                pnl = (exit_price - pos['entry']) * pos.get('size', 1)
            else:
                pnl = (pos['entry'] - exit_price) * pos.get('size', 1)
            
            journal['trades'].append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'direction': pos['direction'],
                'entry': pos['entry'],
                'exit': exit_price,
                'pnl': pnl,
                'reason': 'stop_loss' if stopped else 'take_profit'
            })
            journal['paper_capital'] += pnl
            journal['current_position'] = None
            print(f"\n{'🛑 STOPPED OUT' if stopped else '🎯 TAKE PROFIT HIT'}!")
            print(f"   Exit: ${exit_price:.2f}")
            print(f"   P/L: ${pnl:+.2f}")
        else:
            print("\n✅ Position still open - not stopped")
    
    elif choice == '5':
        print("\n📜 TRADE HISTORY")
        print("-" * 60)
        if journal['trades']:
            for t in journal['trades']:
                print(f"  {t['date']}: {t['direction']:5} ${t['entry']:.2f} -> ${t['exit']:.2f} "
                      f"= ${t['pnl']:+.2f} ({t['reason']})")
        else:
            print("  No trades yet")
        input("\nPress Enter to continue...")
    
    elif choice == '6':
        return False
    
    save_trade_journal(journal)
    return True


def main():
    print("=" * 70)
    print("🎮 PAPER TRADING MODE")
    print("=" * 70)
    print("\nPractice trading without risking real money!")
    
    # Load data
    data = pd.read_csv(Path("data") / "XAU_USD_1D_sample.csv", index_col=0, parse_dates=True)
    
    # Load journal
    journal = load_trade_journal()
    
    # Get signal
    signal, latest, data = get_current_signal(data)
    
    # Display dashboard
    display_dashboard(journal, data, signal)
    
    # Interactive mode
    while interactive_mode(journal, data, signal):
        display_dashboard(journal, data, signal)
    
    print("\n💾 Progress saved!")
    print("Run again tomorrow to continue paper trading.")


if __name__ == "__main__":
    main()
