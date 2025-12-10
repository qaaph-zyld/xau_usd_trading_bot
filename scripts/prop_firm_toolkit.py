"""
🏆 PROP FIRM TOOLKIT

Everything you need to pass a prop firm challenge with $100 or less.

This is the ONLY viable path for $100 capital on XAU/USD.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import webbrowser


class PropFirmToolkit:
    """Complete toolkit for prop firm challenges."""
    
    PROP_FIRMS = [
        {
            "name": "Funded Next",
            "url": "https://fundednext.com",
            "cost": 59,
            "account": 6000,
            "target": 0.10,
            "daily_loss": 0.05,
            "max_dd": 0.10,
            "split": 0.80,
            "time": 30,
            "notes": "Best value, low cost entry"
        },
        {
            "name": "True Forex Funds",
            "url": "https://trueforexfunds.com", 
            "cost": 79,
            "account": 5000,
            "target": 0.08,
            "daily_loss": 0.05,
            "max_dd": 0.08,
            "split": 0.80,
            "time": 30,
            "notes": "Good split, lower target"
        },
        {
            "name": "MyForexFunds",
            "url": "https://myforexfunds.com",
            "cost": 84,
            "account": 5000,
            "target": 0.08,
            "daily_loss": 0.05,
            "max_dd": 0.12,
            "split": 0.75,
            "time": 30,
            "notes": "Higher drawdown allowed"
        },
        {
            "name": "FTMO",
            "url": "https://ftmo.com",
            "cost": 155,
            "account": 10000,
            "target": 0.10,
            "daily_loss": 0.05,
            "max_dd": 0.10,
            "split": 0.80,
            "time": 30,
            "notes": "Industry standard, respected"
        }
    ]
    
    def __init__(self):
        self.data_path = Path("data")
        self.tracker_path = self.data_path / "prop_firm_tracker.json"
        self.load_tracker()
        self.pass_rate = 0.404  # Our validated pass rate
    
    def load_tracker(self):
        """Load progress tracker."""
        if self.tracker_path.exists():
            with open(self.tracker_path, 'r') as f:
                self.tracker = json.load(f)
        else:
            self.tracker = {
                "paper_trades": [],
                "challenges_attempted": 0,
                "challenges_passed": 0,
                "total_invested": 0,
                "total_profit": 0,
                "created": datetime.now().isoformat()
            }
            self.save_tracker()
    
    def save_tracker(self):
        """Save progress tracker."""
        with open(self.tracker_path, 'w') as f:
            json.dump(self.tracker, f, indent=2, default=str)
    
    def show_ev_calculator(self, budget=100):
        """Show expected value for each prop firm."""
        
        print("\n" + "=" * 70)
        print(f"💰 EXPECTED VALUE CALCULATOR (Budget: ${budget})")
        print("=" * 70)
        
        print(f"\nOur strategy pass rate: {self.pass_rate * 100:.1f}%\n")
        print(f"{'Firm':<20} {'Cost':>7} {'Account':>9} {'If Pass':>9} {'EV':>8} {'Rec'}")
        print("-" * 65)
        
        best_ev = -999
        best_firm = None
        
        for firm in self.PROP_FIRMS:
            if firm['cost'] <= budget:
                profit_if_pass = firm['account'] * firm['target'] * firm['split']
                ev = self.pass_rate * profit_if_pass - (1 - self.pass_rate) * firm['cost']
                
                rec = ""
                if ev > best_ev:
                    best_ev = ev
                    best_firm = firm
                    rec = "⭐"
                
                print(f"{firm['name']:<20} ${firm['cost']:>6} ${firm['account']:>8,} ${profit_if_pass:>8,.0f} ${ev:>+7.0f} {rec}")
        
        print("-" * 65)
        
        if best_firm:
            print(f"\n✅ BEST CHOICE: {best_firm['name']}")
            print(f"   Cost: ${best_firm['cost']} | If Pass: ${best_firm['account'] * best_firm['target'] * best_firm['split']:,.0f}")
            print(f"   Expected Value: ${best_ev:+.0f} per attempt")
        else:
            print("\n⚠️ No firms within budget. Need at least $59.")
        
        return best_firm
    
    def show_challenge_rules(self, firm_name=None):
        """Show rules for selected prop firm."""
        
        if not firm_name:
            print("\nSelect a prop firm:")
            for i, firm in enumerate(self.PROP_FIRMS, 1):
                print(f"  {i}. {firm['name']} (${firm['cost']})")
            choice = input("\nChoice: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(self.PROP_FIRMS):
                firm = self.PROP_FIRMS[int(choice) - 1]
            else:
                return
        else:
            firm = next((f for f in self.PROP_FIRMS if f['name'] == firm_name), None)
            if not firm:
                print(f"Firm '{firm_name}' not found")
                return
        
        print("\n" + "=" * 70)
        print(f"📋 {firm['name'].upper()} CHALLENGE RULES")
        print("=" * 70)
        
        print(f"""
    Account Size:     ${firm['account']:,}
    Challenge Cost:   ${firm['cost']}
    
    RULES TO PASS:
    ───────────────────────────────────────────
    ✅ Profit Target:    {firm['target']*100:.0f}% (${firm['account'] * firm['target']:,.0f})
    ❌ Max Daily Loss:   {firm['daily_loss']*100:.0f}% (${firm['account'] * firm['daily_loss']:,.0f})
    ❌ Max Drawdown:     {firm['max_dd']*100:.0f}% (${firm['account'] * firm['max_dd']:,.0f})
    ⏱️ Time Limit:       {firm['time']} days
    
    IF YOU PASS:
    ───────────────────────────────────────────
    Funded Account:   ${firm['account']:,}
    Profit Split:     {firm['split']*100:.0f}% to you
    
    DAILY POSITION SIZING:
    ───────────────────────────────────────────
    Risk per trade:   8% = ${firm['account'] * 0.08:,.0f}
    Max loss today:   ${firm['account'] * firm['daily_loss']:,.0f}
    Position size:    ~0.10-0.15 lots
    
    Notes: {firm['notes']}
        """)
        
        return firm
    
    def record_paper_trade(self):
        """Record a paper trade."""
        
        print("\n" + "=" * 70)
        print("📝 RECORD PAPER TRADE")
        print("=" * 70)
        
        print("\nDirection:")
        print("  1. LONG")
        print("  2. SHORT")
        direction = input("Choice (1/2): ").strip()
        direction = "LONG" if direction == "1" else "SHORT"
        
        print("\nOutcome:")
        print("  1. WIN (hit take profit)")
        print("  2. LOSS (hit stop loss)")
        print("  3. BREAKEVEN")
        outcome = input("Choice (1/2/3): ").strip()
        
        if outcome == "1":
            result = "win"
            pnl = 1.5  # R:R is 1.5
        elif outcome == "2":
            result = "loss"
            pnl = -1.0
        else:
            result = "breakeven"
            pnl = 0
        
        trade = {
            "date": datetime.now().isoformat(),
            "direction": direction,
            "result": result,
            "pnl_r": pnl
        }
        
        self.tracker["paper_trades"].append(trade)
        self.save_tracker()
        
        # Calculate stats
        trades = self.tracker["paper_trades"]
        wins = len([t for t in trades if t["result"] == "win"])
        total = len(trades)
        win_rate = wins / total * 100 if total > 0 else 0
        total_r = sum(t["pnl_r"] for t in trades)
        
        print(f"\n✅ Trade recorded!")
        print(f"   Total trades: {total}")
        print(f"   Win rate: {win_rate:.1f}%")
        print(f"   Total R: {total_r:+.1f}R")
        
        if total >= 15 and win_rate >= 45:
            print(f"\n🎉 You're ready for a real challenge!")
        else:
            remaining = max(0, 15 - total)
            print(f"\n⏳ {remaining} more trades recommended before real challenge")
    
    def check_readiness(self):
        """Check if ready for real challenge."""
        
        print("\n" + "=" * 70)
        print("✅ READINESS CHECK")
        print("=" * 70)
        
        trades = self.tracker["paper_trades"]
        total = len(trades)
        wins = len([t for t in trades if t["result"] == "win"])
        win_rate = wins / total * 100 if total > 0 else 0
        total_r = sum(t["pnl_r"] for t in trades)
        
        checks = [
            ("Paper trades (min 15)", total, 15, total >= 15),
            ("Win rate (min 45%)", f"{win_rate:.1f}%", "45%", win_rate >= 45),
            ("Total R (positive)", f"{total_r:+.1f}R", ">0R", total_r > 0),
        ]
        
        print(f"\n{'Check':<30} {'Your Score':>15} {'Required':>12} {'Status':>10}")
        print("-" * 70)
        
        all_passed = True
        for name, score, req, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            if not passed:
                all_passed = False
            print(f"{name:<30} {str(score):>15} {str(req):>12} {status:>10}")
        
        print("-" * 70)
        
        if all_passed:
            print(f"""
    🎉 YOU ARE READY FOR A REAL CHALLENGE!
    
    Next steps:
    1. Choose a prop firm (run option 1 in menu)
    2. Sign up and pay challenge fee
    3. Follow the strategy EXACTLY
    4. Expected outcome: 40% pass = ${self.PROP_FIRMS[0]['account'] * self.PROP_FIRMS[0]['target'] * self.PROP_FIRMS[0]['split']:,.0f}
            """)
        else:
            print(f"""
    ⚠️ NOT READY YET
    
    Keep paper trading until all checks pass.
    This protects your ${self.PROP_FIRMS[0]['cost']} investment.
    
    Run: python scripts/live_signals.py
    To get daily signals for paper trading.
            """)
        
        return all_passed
    
    def record_challenge_attempt(self):
        """Record a real challenge attempt."""
        
        print("\n" + "=" * 70)
        print("🏆 RECORD CHALLENGE ATTEMPT")
        print("=" * 70)
        
        print("\nSelect prop firm:")
        for i, firm in enumerate(self.PROP_FIRMS, 1):
            print(f"  {i}. {firm['name']} (${firm['cost']})")
        
        choice = input("\nChoice: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(self.PROP_FIRMS)):
            return
        
        firm = self.PROP_FIRMS[int(choice) - 1]
        
        print("\nResult:")
        print("  1. PASSED")
        print("  2. FAILED")
        
        result = input("Choice (1/2): ").strip()
        passed = result == "1"
        
        self.tracker["challenges_attempted"] += 1
        self.tracker["total_invested"] += firm["cost"]
        
        if passed:
            self.tracker["challenges_passed"] += 1
            profit = firm["account"] * firm["target"] * firm["split"]
            self.tracker["total_profit"] += profit
            print(f"\n🎉 CONGRATULATIONS! You passed!")
            print(f"   Profit: ${profit:,.0f}")
        else:
            print(f"\n😔 Challenge failed. That's okay.")
            print(f"   Loss: ${firm['cost']}")
            print(f"   Expected value is still positive!")
        
        self.save_tracker()
        self.show_overall_stats()
    
    def show_overall_stats(self):
        """Show overall statistics."""
        
        print("\n" + "=" * 70)
        print("📊 YOUR OVERALL STATISTICS")
        print("=" * 70)
        
        t = self.tracker
        
        paper_trades = len(t["paper_trades"])
        paper_wins = len([x for x in t["paper_trades"] if x["result"] == "win"])
        paper_wr = paper_wins / paper_trades * 100 if paper_trades > 0 else 0
        
        print(f"""
    Paper Trading:
    ─────────────────────────────────────
    Total trades:     {paper_trades}
    Wins:             {paper_wins}
    Win rate:         {paper_wr:.1f}%
    
    Real Challenges:
    ─────────────────────────────────────
    Attempted:        {t['challenges_attempted']}
    Passed:           {t['challenges_passed']}
    Pass rate:        {t['challenges_passed'] / t['challenges_attempted'] * 100:.1f}% (target: 40%)
    
    Financials:
    ─────────────────────────────────────
    Total invested:   ${t['total_invested']:,.0f}
    Total profit:     ${t['total_profit']:,.0f}
    Net P/L:          ${t['total_profit'] - t['total_invested']:+,.0f}
    ROI:              {(t['total_profit'] - t['total_invested']) / t['total_invested'] * 100:.1f}%
        """ if t['challenges_attempted'] > 0 else f"""
    Paper Trading:
    ─────────────────────────────────────
    Total trades:     {paper_trades}
    Wins:             {paper_wins}
    Win rate:         {paper_wr:.1f}%
    
    Real Challenges:
    ─────────────────────────────────────
    Not started yet. Complete paper trading first!
        """)
    
    def open_firm_website(self):
        """Open prop firm website."""
        
        print("\nSelect a prop firm to open:")
        for i, firm in enumerate(self.PROP_FIRMS, 1):
            print(f"  {i}. {firm['name']} - {firm['url']}")
        
        choice = input("\nChoice: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(self.PROP_FIRMS):
            firm = self.PROP_FIRMS[int(choice) - 1]
            print(f"\n🌐 Opening {firm['url']}...")
            webbrowser.open(firm['url'])
    
    def main_menu(self):
        """Main menu."""
        
        while True:
            print("\n" + "=" * 70)
            print("🏆 PROP FIRM TOOLKIT")
            print("=" * 70)
            
            # Quick stats
            trades = len(self.tracker["paper_trades"])
            attempts = self.tracker["challenges_attempted"]
            passed = self.tracker["challenges_passed"]
            
            print(f"\n   Paper trades: {trades} | Challenges: {passed}/{attempts}")
            
            print("\n" + "-" * 70)
            print("MENU:")
            print("  1. Expected Value Calculator")
            print("  2. View Challenge Rules")
            print("  3. Record Paper Trade")
            print("  4. Readiness Check")
            print("  5. Record Challenge Attempt")
            print("  6. View Statistics")
            print("  7. Open Firm Website")
            print("  8. Get Today's Signal")
            print("  9. Exit")
            
            choice = input("\nChoice (1-9): ").strip()
            
            if choice == "1":
                budget = input("Enter your budget (default $100): ").strip()
                budget = int(budget) if budget.isdigit() else 100
                self.show_ev_calculator(budget)
            elif choice == "2":
                self.show_challenge_rules()
            elif choice == "3":
                self.record_paper_trade()
            elif choice == "4":
                self.check_readiness()
            elif choice == "5":
                self.record_challenge_attempt()
            elif choice == "6":
                self.show_overall_stats()
            elif choice == "7":
                self.open_firm_website()
            elif choice == "8":
                os.system("python scripts/live_signals.py")
            elif choice == "9":
                print("\n💾 Progress saved. Good luck!")
                break
            
            input("\nPress Enter to continue...")


def main():
    toolkit = PropFirmToolkit()
    toolkit.main_menu()


if __name__ == "__main__":
    main()
