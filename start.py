"""
🚀 XAU/USD PROP FIRM TRADING BOT - QUICK START

One command to rule them all.
"""

import os
import sys
from pathlib import Path


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║          🏆 XAU/USD PROP FIRM TRADING BOT                           ║
║                                                                      ║
║     Turn $100 into a funded trading account                         ║
║     Expected Value: +$263 per challenge                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("Select an option:\n")
    print("  1. 📊 Get Today's Signal          (Daily use)")
    print("  2. 📋 Trading Dashboard           (Manage challenge)")
    print("  3. 🎮 Prop Firm System            (Complete system)")
    print("  4. 🔬 Run Validation              (Test strategy)")
    print("  5. 📖 View Guide                  (How to use)")
    print("  6. ❌ Exit")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == '1':
        print("\n" + "=" * 60)
        os.system('python scripts/live_signals.py')
    
    elif choice == '2':
        os.system('python scripts/trading_dashboard.py')
    
    elif choice == '3':
        os.system('python scripts/prop_firm_system.py')
    
    elif choice == '4':
        os.system('python scripts/final_validation.py')
    
    elif choice == '5':
        guide_path = Path("docs/PROP_FIRM_GUIDE.md")
        if guide_path.exists():
            with open(guide_path, 'r') as f:
                content = f.read()
            print("\n" + content)
        else:
            print("Guide not found. Check docs/PROP_FIRM_GUIDE.md")
    
    elif choice == '6':
        print("\nGood luck with your trading! 🏆")
        return
    
    else:
        print("\nInvalid choice. Please try again.")
    
    # Ask to continue
    input("\n\nPress Enter to return to menu...")
    main()


if __name__ == "__main__":
    main()
