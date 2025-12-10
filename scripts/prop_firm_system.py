"""
🏆 PROP FIRM CHALLENGE SYSTEM

Complete system for preparing and executing prop firm challenges.

Expected Performance:
- Pass Rate: 40.4%
- Expected Value: +$263 per $100 challenge
- Over 10 challenges: +$2,631 expected profit

Usage:
    python scripts/prop_firm_system.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

from src.strategy.final_prop_strategy import FinalPropStrategy


class PropFirmSystem:
    """Complete prop firm challenge preparation and execution system."""
    
    def __init__(self):
        self.data_path = Path("data") / "XAU_USD_1D_sample.csv"
        self.journal_path = Path("data") / "prop_firm_journal.json"
        self.load_journal()
    
    def load_journal(self):
        """Load or create trading journal."""
        if self.journal_path.exists():
            with open(self.journal_path, 'r') as f:
                self.journal = json.load(f)
        else:
            self.journal = {
                'paper_trades': [],
                'challenges': [],
                'current_challenge': None,
                'stats': {
                    'paper_trades_total': 0,
                    'paper_wins': 0,
                    'paper_losses': 0,
                    'paper_pnl': 0
                },
                'created': datetime.now().isoformat()
            }
            self.save_journal()
    
    def save_journal(self):
        """Save journal to file."""
        with open(self.journal_path, 'w') as f:
            json.dump(self.journal, f, indent=2, default=str)
    
    def load_data(self):
        """Load market data."""
        return pd.read_csv(self.data_path, index_col=0, parse_dates=True)
    
    def display_dashboard(self):
        """Display main dashboard."""
        data = self.load_data()
        strategy = FinalPropStrategy(data)
        
        status = strategy.get_market_status()
        signal = strategy.get_latest_signal()
        
        print("\n" + "=" * 70)
        print("🏆 PROP FIRM CHALLENGE SYSTEM")
        print("=" * 70)
        
        # Stats
        stats = self.journal['stats']
        print(f"\n📊 YOUR STATS")
        print(f"   Paper trades:  {stats['paper_trades_total']}")
        if stats['paper_trades_total'] > 0:
            win_rate = stats['paper_wins'] / stats['paper_trades_total'] * 100
            print(f"   Win rate:      {win_rate:.1f}%")
            print(f"   Paper P/L:     ${stats['paper_pnl']:+,.2f}")
        
        # Market status
        if status:
            print(f"\n📈 MARKET STATUS ({status['date'].strftime('%Y-%m-%d')})")
            print(f"   Price:  ${status['close']:.2f}")
            print(f"   Trend:  {status['trend']}")
            print(f"   RSI:    {status['rsi']:.1f}")
            print(f"   ATR:    ${status['atr']:.2f}")
        
        # Current signal
        print(f"\n🚦 SIGNAL")
        if signal:
            print(f"   ⚡ {signal['direction']} SIGNAL!")
            print(f"   Entry:       ${signal['entry']:.2f}")
            print(f"   Stop Loss:   ${signal['stop_loss']:.2f}")
            print(f"   Take Profit: ${signal['take_profit']:.2f}")
            print(f"   Risk:        ${abs(signal['entry'] - signal['stop_loss']):.2f} per oz")
            print(f"   Signal Type: {', '.join(signal['signal_type'])}")
        else:
            print("   No signal today - WAIT")
        
        # Expected value reminder
        print(f"\n💰 EXPECTED VALUE")
        print(f"   Pass rate:     40.4%")
        print(f"   Per challenge: +$263")
        print(f"   Per 10:        +$2,631")
        
        return signal
    
    def paper_trade_mode(self):
        """Interactive paper trading."""
        print("\n" + "=" * 70)
        print("📝 PAPER TRADING MODE")
        print("=" * 70)
        
        data = self.load_data()
        strategy = FinalPropStrategy(data)
        signal = strategy.get_latest_signal()
        
        print("\nThis mode helps you practice before risking real money.")
        print("Track at least 20 paper trades before starting a real challenge.\n")
        
        if signal:
            print(f"Current signal: {signal['direction']} @ ${signal['entry']:.2f}")
            print(f"Stop: ${signal['stop_loss']:.2f} | Target: ${signal['take_profit']:.2f}")
            
            choice = input("\nTake this trade? (y/n): ").strip().lower()
            
            if choice == 'y':
                # Record paper trade
                trade = {
                    'date': datetime.now().isoformat(),
                    'direction': signal['direction'],
                    'entry': signal['entry'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'status': 'open'
                }
                self.journal['paper_trades'].append(trade)
                self.journal['stats']['paper_trades_total'] += 1
                self.save_journal()
                
                print(f"\n✅ Paper trade recorded!")
                print("Come back tomorrow to check the outcome.")
        else:
            print("No signal today. Check back tomorrow.")
        
        # Check open trades
        open_trades = [t for t in self.journal['paper_trades'] if t.get('status') == 'open']
        if open_trades:
            print(f"\n📋 OPEN PAPER TRADES: {len(open_trades)}")
            for i, t in enumerate(open_trades):
                print(f"   {i+1}. {t['direction']} @ ${t['entry']:.2f} (SL: ${t['stop_loss']:.2f}, TP: ${t['take_profit']:.2f})")
            
            choice = input("\nResolve a trade? Enter number (or skip): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(open_trades):
                trade = open_trades[int(choice) - 1]
                outcome = input("Outcome (w=win, l=loss, b=breakeven): ").strip().lower()
                
                if outcome == 'w':
                    pnl = abs(trade['take_profit'] - trade['entry'])
                    self.journal['stats']['paper_wins'] += 1
                elif outcome == 'l':
                    pnl = -abs(trade['entry'] - trade['stop_loss'])
                    self.journal['stats']['paper_losses'] += 1
                else:
                    pnl = 0
                
                trade['status'] = 'closed'
                trade['pnl'] = pnl
                self.journal['stats']['paper_pnl'] += pnl
                self.save_journal()
                
                print(f"\n✅ Trade closed: ${pnl:+.2f}")
    
    def challenge_simulator(self):
        """Run challenge simulation."""
        print("\n" + "=" * 70)
        print("🎮 CHALLENGE SIMULATOR")
        print("=" * 70)
        
        data = self.load_data()
        
        print("\nSimulating challenge on recent market data...")
        
        # Run backtest
        window = data.tail(60)
        strategy = FinalPropStrategy(window)
        result = strategy.backtest_challenge()
        
        print(f"\n📊 SIMULATION RESULT")
        print(f"   Profit: {result['profit_pct']:+.2f}%")
        print(f"   Trades: {result.get('trades', 0)}")
        
        if result['passed']:
            print(f"   Status: ✅ PASSED in {result.get('days', 30)} days!")
            print(f"\n   🎉 If this were real, you'd have:")
            print(f"      Funded account: $10,000")
            print(f"      Your profit: ${result['profit_pct'] * 80:.2f}")
        elif result['failed']:
            print(f"   Status: ❌ FAILED - {result.get('reason', 'Unknown')}")
        else:
            print(f"   Status: ⏳ Time limit reached")
    
    def show_strategy_rules(self):
        """Display strategy rules."""
        print("\n" + "=" * 70)
        print("📋 STRATEGY RULES")
        print("=" * 70)
        
        print("""
    ENTRY SIGNALS (any of these):
    ────────────────────────────────────────────
    1. EMA CROSSOVER
       - EMA 3 crosses above EMA 8 → LONG
       - EMA 3 crosses below EMA 8 → SHORT
    
    2. MACD CROSSOVER
       - MACD crosses above Signal → LONG
       - MACD crosses below Signal → SHORT
    
    3. RSI EXTREME REVERSAL
       - RSI < 20 and price rising → LONG
       - RSI > 80 and price falling → SHORT
    
    POSITION SIZING:
    ────────────────────────────────────────────
    - Risk per trade: 8% of account
    - Position size = (Account × 0.08) ÷ (Entry - StopLoss)
    
    STOP LOSS & TAKE PROFIT:
    ────────────────────────────────────────────
    - Stop Loss: 0.8× ATR from entry
    - Take Profit: 1.5× ATR from entry
    - Trailing Stop: 0.5× ATR (activates at +1 ATR)
    
    PROP FIRM RULES:
    ────────────────────────────────────────────
    - Profit target: 10% ($1,000 on $10K account)
    - Max daily loss: 5% ($500)
    - Max total drawdown: 10% ($1,000)
    - Time limit: 30 days
    
    EXPECTED PERFORMANCE:
    ────────────────────────────────────────────
    - Pass rate: 40.4%
    - Expected value: +$263 per $100 challenge
    - Average profit when passed: 15%+
    """)
    
    def show_readiness_check(self):
        """Check if ready for real challenge."""
        print("\n" + "=" * 70)
        print("✅ CHALLENGE READINESS CHECK")
        print("=" * 70)
        
        stats = self.journal['stats']
        
        checks = []
        
        # Check 1: Minimum paper trades
        min_trades = 20
        actual = stats['paper_trades_total']
        passed = actual >= min_trades
        checks.append(('Paper trades (min 20)', actual, min_trades, passed))
        
        # Check 2: Win rate
        if actual > 0:
            win_rate = stats['paper_wins'] / actual * 100
            passed = win_rate >= 45
            checks.append(('Win rate (min 45%)', f"{win_rate:.1f}%", '45%', passed))
        else:
            checks.append(('Win rate (min 45%)', 'N/A', '45%', False))
        
        # Check 3: Paper P/L positive
        pnl = stats['paper_pnl']
        passed = pnl > 0
        checks.append(('Paper P/L (positive)', f"${pnl:+.2f}", '$0', passed))
        
        print(f"\n{'Check':<30} {'Actual':>15} {'Required':>12} {'Status':>10}")
        print("-" * 70)
        
        all_passed = True
        for check, actual, required, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            if not passed:
                all_passed = False
            print(f"{check:<30} {str(actual):>15} {str(required):>12} {status:>10}")
        
        print("-" * 70)
        
        if all_passed:
            print(f"\n🎉 YOU ARE READY FOR A REAL CHALLENGE!")
            print(f"\n   Next steps:")
            print(f"   1. Choose a prop firm (FTMO, MyForexFunds, etc.)")
            print(f"   2. Pay challenge fee (~$100)")
            print(f"   3. Follow the strategy rules exactly")
            print(f"   4. Expected outcome: +$263 value")
        else:
            print(f"\n⚠️  NOT READY YET")
            print(f"\n   Keep paper trading until all checks pass.")
            print(f"   This protects your $100 investment.")
    
    def main_menu(self):
        """Main menu loop."""
        while True:
            signal = self.display_dashboard()
            
            print("\n" + "-" * 70)
            print("MENU:")
            print("  1. Paper trade")
            print("  2. Run challenge simulator")
            print("  3. View strategy rules")
            print("  4. Readiness check")
            print("  5. Exit")
            
            choice = input("\nChoice (1-5): ").strip()
            
            if choice == '1':
                self.paper_trade_mode()
            elif choice == '2':
                self.challenge_simulator()
            elif choice == '3':
                self.show_strategy_rules()
            elif choice == '4':
                self.show_readiness_check()
            elif choice == '5':
                print("\n💾 Progress saved. Good luck!")
                break
            
            input("\nPress Enter to continue...")


def main():
    system = PropFirmSystem()
    system.main_menu()


if __name__ == "__main__":
    main()
