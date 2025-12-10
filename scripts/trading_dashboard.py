"""
📊 COMPREHENSIVE TRADING DASHBOARD

Real-time monitoring, performance tracking, and challenge management.

Usage:
    python scripts/trading_dashboard.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import ta


class TradingDashboard:
    """Complete trading dashboard for prop firm challenge."""
    
    def __init__(self):
        self.data_path = Path("data")
        self.journal_path = self.data_path / "trading_journal.json"
        self.challenge_path = self.data_path / "active_challenge.json"
        self.load_data()
    
    def load_data(self):
        """Load all data files."""
        # Trading journal
        if self.journal_path.exists():
            with open(self.journal_path, 'r') as f:
                self.journal = json.load(f)
        else:
            self.journal = {
                'trades': [],
                'daily_balance': [],
                'notes': []
            }
        
        # Active challenge
        if self.challenge_path.exists():
            with open(self.challenge_path, 'r') as f:
                self.challenge = json.load(f)
        else:
            self.challenge = None
    
    def save_data(self):
        """Save all data files."""
        with open(self.journal_path, 'w') as f:
            json.dump(self.journal, f, indent=2, default=str)
        
        if self.challenge:
            with open(self.challenge_path, 'w') as f:
                json.dump(self.challenge, f, indent=2, default=str)
    
    def start_challenge(self):
        """Start a new prop firm challenge."""
        print("\n" + "=" * 70)
        print("🏁 START NEW PROP FIRM CHALLENGE")
        print("=" * 70)
        
        if self.challenge and self.challenge.get('status') == 'active':
            print(f"\n⚠️  You have an active challenge!")
            print(f"   Started: {self.challenge['start_date']}")
            print(f"   Current: ${self.challenge['current_balance']:,.2f}")
            choice = input("\nEnd current challenge? (y/n): ").strip().lower()
            if choice != 'y':
                return
            self.challenge['status'] = 'abandoned'
            self.challenge['end_date'] = datetime.now().isoformat()
        
        print("\nChallenge configuration:")
        
        # Default to FTMO-style challenge
        self.challenge = {
            'start_date': datetime.now().isoformat(),
            'end_date': None,
            'status': 'active',
            'starting_balance': 10000,
            'current_balance': 10000,
            'highest_balance': 10000,
            'profit_target': 0.10,  # 10%
            'max_daily_loss': 0.05,  # 5%
            'max_drawdown': 0.10,  # 10%
            'time_limit_days': 30,
            'trades': [],
            'daily_pnl': {},
            'prop_firm': 'FTMO-style'
        }
        
        print(f"""
    Prop Firm:        {self.challenge['prop_firm']}
    Account Size:     ${self.challenge['starting_balance']:,}
    Profit Target:    {self.challenge['profit_target']*100:.0f}% (${self.challenge['starting_balance'] * self.challenge['profit_target']:,.0f})
    Max Daily Loss:   {self.challenge['max_daily_loss']*100:.0f}% (${self.challenge['starting_balance'] * self.challenge['max_daily_loss']:,.0f})
    Max Drawdown:     {self.challenge['max_drawdown']*100:.0f}% (${self.challenge['starting_balance'] * self.challenge['max_drawdown']:,.0f})
    Time Limit:       {self.challenge['time_limit_days']} days
        """)
        
        self.save_data()
        print("✅ Challenge started! Good luck!")
    
    def record_trade(self):
        """Record a new trade."""
        if not self.challenge or self.challenge.get('status') != 'active':
            print("\n⚠️  No active challenge. Start one first.")
            return
        
        print("\n" + "=" * 70)
        print("📝 RECORD TRADE")
        print("=" * 70)
        
        print("\nTrade direction:")
        print("  1. LONG (buy)")
        print("  2. SHORT (sell)")
        direction = input("Choice (1/2): ").strip()
        direction = 'LONG' if direction == '1' else 'SHORT'
        
        entry = float(input("Entry price: $").strip())
        exit_price = float(input("Exit price: $").strip())
        lots = float(input("Position size (lots): ").strip())
        
        # Calculate P&L
        oz = lots * 100  # 1 lot = 100 oz
        if direction == 'LONG':
            pnl = (exit_price - entry) * oz
        else:
            pnl = (entry - exit_price) * oz
        
        trade = {
            'date': datetime.now().isoformat(),
            'direction': direction,
            'entry': entry,
            'exit': exit_price,
            'lots': lots,
            'pnl': round(pnl, 2),
            'balance_after': round(self.challenge['current_balance'] + pnl, 2)
        }
        
        self.challenge['trades'].append(trade)
        self.challenge['current_balance'] += pnl
        self.challenge['highest_balance'] = max(
            self.challenge['highest_balance'], 
            self.challenge['current_balance']
        )
        
        # Track daily P&L
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.challenge['daily_pnl']:
            self.challenge['daily_pnl'][today] = 0
        self.challenge['daily_pnl'][today] += pnl
        
        self.save_data()
        
        result = "WIN ✅" if pnl > 0 else "LOSS ❌"
        print(f"\n{result}: ${pnl:+,.2f}")
        print(f"New balance: ${self.challenge['current_balance']:,.2f}")
        
        # Check challenge status
        self._check_challenge_status()
    
    def _check_challenge_status(self):
        """Check if challenge passed or failed."""
        if not self.challenge:
            return
        
        start = self.challenge['starting_balance']
        current = self.challenge['current_balance']
        highest = self.challenge['highest_balance']
        
        # Check profit target
        profit_pct = (current - start) / start
        if profit_pct >= self.challenge['profit_target']:
            self.challenge['status'] = 'passed'
            self.challenge['end_date'] = datetime.now().isoformat()
            print("\n" + "🎉" * 20)
            print("   CONGRATULATIONS! YOU PASSED THE CHALLENGE!")
            print("🎉" * 20)
            self.save_data()
            return
        
        # Check max drawdown
        drawdown = (highest - current) / start
        if drawdown >= self.challenge['max_drawdown']:
            self.challenge['status'] = 'failed'
            self.challenge['end_date'] = datetime.now().isoformat()
            self.challenge['fail_reason'] = 'Max drawdown exceeded'
            print("\n❌ CHALLENGE FAILED: Max drawdown exceeded")
            self.save_data()
            return
        
        # Check daily loss
        today = datetime.now().strftime('%Y-%m-%d')
        daily_pnl = self.challenge['daily_pnl'].get(today, 0)
        daily_loss_limit = start * self.challenge['max_daily_loss']
        
        if daily_pnl <= -daily_loss_limit:
            self.challenge['status'] = 'failed'
            self.challenge['end_date'] = datetime.now().isoformat()
            self.challenge['fail_reason'] = 'Daily loss limit exceeded'
            print("\n❌ CHALLENGE FAILED: Daily loss limit exceeded")
            self.save_data()
            return
        
        # Check time limit
        start_date = datetime.fromisoformat(self.challenge['start_date'])
        days_elapsed = (datetime.now() - start_date).days
        
        if days_elapsed >= self.challenge['time_limit_days']:
            if profit_pct >= self.challenge['profit_target']:
                self.challenge['status'] = 'passed'
            else:
                self.challenge['status'] = 'failed'
                self.challenge['fail_reason'] = 'Time limit reached'
            self.challenge['end_date'] = datetime.now().isoformat()
            self.save_data()
    
    def show_challenge_status(self):
        """Display current challenge status."""
        print("\n" + "=" * 70)
        print("📊 CHALLENGE STATUS")
        print("=" * 70)
        
        if not self.challenge:
            print("\n   No challenge data. Start a new challenge!")
            return
        
        start = self.challenge['starting_balance']
        current = self.challenge['current_balance']
        highest = self.challenge['highest_balance']
        
        profit = current - start
        profit_pct = profit / start * 100
        drawdown = (highest - current) / start * 100
        target = self.challenge['profit_target'] * 100
        max_dd = self.challenge['max_drawdown'] * 100
        
        start_date = datetime.fromisoformat(self.challenge['start_date'])
        days_elapsed = (datetime.now() - start_date).days
        days_left = self.challenge['time_limit_days'] - days_elapsed
        
        status_emoji = {
            'active': '🟢',
            'passed': '🏆',
            'failed': '❌',
            'abandoned': '⚫'
        }.get(self.challenge['status'], '❓')
        
        print(f"""
    Status:           {status_emoji} {self.challenge['status'].upper()}
    Prop Firm:        {self.challenge['prop_firm']}
    
    💰 BALANCE
    ─────────────────────────────────
    Starting:         ${start:,.2f}
    Current:          ${current:,.2f}
    P&L:              ${profit:+,.2f} ({profit_pct:+.2f}%)
    Peak:             ${highest:,.2f}
    
    📈 PROGRESS TO TARGET
    ─────────────────────────────────
    Target:           {target:.0f}% (${start * self.challenge['profit_target']:,.0f})
    Current:          {profit_pct:.2f}%
    Remaining:        {target - profit_pct:.2f}%
    """)
        
        # Progress bar
        progress = min(profit_pct / target * 100, 100)
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"    [{bar}] {progress:.1f}%")
        
        print(f"""
    🛡️ RISK LIMITS
    ─────────────────────────────────
    Max Drawdown:     {max_dd:.0f}% limit
    Current DD:       {drawdown:.2f}%
    DD Remaining:     {max_dd - drawdown:.2f}%
    
    ⏱️ TIME
    ─────────────────────────────────
    Started:          {start_date.strftime('%Y-%m-%d')}
    Days Elapsed:     {days_elapsed}
    Days Remaining:   {max(0, days_left)}
    
    📊 TRADES
    ─────────────────────────────────
    Total Trades:     {len(self.challenge['trades'])}
    """)
        
        if self.challenge['trades']:
            wins = len([t for t in self.challenge['trades'] if t['pnl'] > 0])
            total = len(self.challenge['trades'])
            win_rate = wins / total * 100
            
            total_profit = sum(t['pnl'] for t in self.challenge['trades'] if t['pnl'] > 0)
            total_loss = sum(t['pnl'] for t in self.challenge['trades'] if t['pnl'] < 0)
            
            print(f"    Wins:             {wins}")
            print(f"    Losses:           {total - wins}")
            print(f"    Win Rate:         {win_rate:.1f}%")
            print(f"    Total Profit:     ${total_profit:,.2f}")
            print(f"    Total Loss:       ${total_loss:,.2f}")
            
            if total_loss != 0:
                pf = abs(total_profit / total_loss)
                print(f"    Profit Factor:    {pf:.2f}")
        
        # Recent trades
        if self.challenge['trades']:
            print(f"\n    Recent Trades:")
            for t in self.challenge['trades'][-5:]:
                date = t['date'][:10]
                result = "✅" if t['pnl'] > 0 else "❌"
                print(f"      {date}: {t['direction']:5} ${t['pnl']:+,.2f} {result}")
    
    def show_daily_checklist(self):
        """Show daily trading checklist."""
        print("\n" + "=" * 70)
        print("✅ DAILY TRADING CHECKLIST")
        print("=" * 70)
        
        checklist = [
            ("Check economic calendar for high-impact news", "news.investing.com"),
            ("Run live signal generator", "python scripts/live_signals.py"),
            ("Review yesterday's trades", "What went right/wrong?"),
            ("Check current challenge status", "Am I on track?"),
            ("Set daily loss limit reminder", "5% of starting balance"),
            ("Prepare mentally", "Follow the plan, no revenge trading"),
        ]
        
        print("\n   Pre-Market:")
        for i, (task, note) in enumerate(checklist, 1):
            print(f"   [ ] {i}. {task}")
            print(f"        → {note}")
        
        print("\n   During Trading:")
        trading_rules = [
            "Only take signals from the strategy",
            "Never move stop loss further away",
            "Trail stop after +1 ATR",
            "Max 2 trades per day",
            "Stop after 2 consecutive losses",
        ]
        
        for i, rule in enumerate(trading_rules, 1):
            print(f"   [ ] {i}. {rule}")
        
        print("\n   Post-Market:")
        post_tasks = [
            "Record all trades in journal",
            "Screenshot trade setups",
            "Note what you learned",
            "Update challenge status",
        ]
        
        for i, task in enumerate(post_tasks, 1):
            print(f"   [ ] {i}. {task}")
    
    def main_menu(self):
        """Main dashboard menu."""
        while True:
            print("\n" + "=" * 70)
            print("📊 TRADING DASHBOARD")
            print("=" * 70)
            
            # Quick status
            if self.challenge and self.challenge.get('status') == 'active':
                current = self.challenge['current_balance']
                start = self.challenge['starting_balance']
                pnl = current - start
                print(f"\n   🟢 Active Challenge: ${current:,.2f} ({pnl:+,.2f})")
            else:
                print("\n   ⚫ No active challenge")
            
            print(f"\n   Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            print("\n" + "-" * 70)
            print("MENU:")
            print("  1. Challenge status")
            print("  2. Start new challenge")
            print("  3. Record trade")
            print("  4. Daily checklist")
            print("  5. Get live signals")
            print("  6. Exit")
            
            choice = input("\nChoice (1-6): ").strip()
            
            if choice == '1':
                self.show_challenge_status()
            elif choice == '2':
                self.start_challenge()
            elif choice == '3':
                self.record_trade()
            elif choice == '4':
                self.show_daily_checklist()
            elif choice == '5':
                print("\nRunning live signals...")
                os.system('python scripts/live_signals.py')
            elif choice == '6':
                print("\n💾 Data saved. Good trading!")
                break
            
            input("\nPress Enter to continue...")


def main():
    dashboard = TradingDashboard()
    dashboard.main_menu()


if __name__ == "__main__":
    main()
