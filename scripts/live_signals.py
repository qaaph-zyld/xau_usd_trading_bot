"""
🔴 LIVE SIGNAL GENERATOR

Fetches real-time XAU/USD data and generates trading signals.
Run this daily to get your entry signals.

Usage:
    python scripts/live_signals.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import requests
import ta


class LiveSignalGenerator:
    """Generate live trading signals for prop firm challenge."""
    
    # Strategy parameters (optimized)
    RISK_PER_TRADE = 0.08
    ATR_SL = 0.8
    ATR_TP = 1.5
    
    def __init__(self):
        self.data_path = Path("data")
        self.signal_log = self.data_path / "signal_log.json"
        self.load_signal_log()
    
    def load_signal_log(self):
        """Load signal history."""
        if self.signal_log.exists():
            with open(self.signal_log, 'r') as f:
                self.signals = json.load(f)
        else:
            self.signals = {'history': [], 'pending': None}
    
    def save_signal_log(self):
        """Save signal history."""
        with open(self.signal_log, 'w') as f:
            json.dump(self.signals, f, indent=2, default=str)
    
    def fetch_live_data(self):
        """
        Fetch live XAU/USD data from a real market source.

        Returns:
            DataFrame with OHLCV bars sourced from yfinance (gold futures GC=F).

        Raises:
            RuntimeError: if no real market data could be fetched. The script
                will NOT fall back to synthetic / simulated prices, because
                trading on fabricated data is dangerous.
        """
        print("Fetching live data from yfinance (GC=F gold futures)...")

        try:
            import yfinance as yf
            ticker = yf.Ticker("GC=F")
            data = ticker.history(period="3mo", interval="1d")
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch live XAU/USD data from yfinance: {e}. "
                "This script refuses to operate on synthetic prices; please "
                "fix your network / yfinance install and retry."
            ) from e

        if data is None or len(data) == 0:
            raise RuntimeError(
                "yfinance returned no data for GC=F. This script refuses to "
                "operate on synthetic prices; please retry later or use a "
                "different data source."
            )

        data = data.rename(columns={
            'Open': 'open', 'High': 'high',
            'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        })
        print(f"   Got {len(data)} daily bars from yfinance")
        return data
    
    def calculate_indicators(self, data):
        """Calculate all indicators."""
        df = data.copy()
        
        # EMAs
        df['ema_3'] = ta.trend.ema_indicator(df['close'], window=3)
        df['ema_8'] = ta.trend.ema_indicator(df['close'], window=8)
        df['ema_21'] = ta.trend.ema_indicator(df['close'], window=21)
        
        # RSI
        df['rsi'] = ta.momentum.rsi(df['close'], window=5)
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        # ATR
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=10)
        
        return df
    
    def get_signal(self, data):
        """Generate trading signal from data."""
        
        if len(data) < 30:
            return None
        
        i = len(data) - 1
        
        close = data['close'].iloc[i]
        atr = data['atr'].iloc[i]
        ema_3 = data['ema_3'].iloc[i]
        ema_8 = data['ema_8'].iloc[i]
        rsi = data['rsi'].iloc[i]
        macd = data['macd'].iloc[i]
        macd_sig = data['macd_signal'].iloc[i]
        
        prev_ema_3 = data['ema_3'].iloc[i-1]
        prev_ema_8 = data['ema_8'].iloc[i-1]
        prev_macd = data['macd'].iloc[i-1]
        prev_macd_sig = data['macd_signal'].iloc[i-1]
        prev_close = data['close'].iloc[i-1]
        
        signals = []
        
        # Check each signal type
        if ema_3 > ema_8 and prev_ema_3 <= prev_ema_8:
            signals.append(('EMA_CROSS', 'LONG'))
        elif ema_3 < ema_8 and prev_ema_3 >= prev_ema_8:
            signals.append(('EMA_CROSS', 'SHORT'))
        
        if macd > macd_sig and prev_macd <= prev_macd_sig:
            signals.append(('MACD_CROSS', 'LONG'))
        elif macd < macd_sig and prev_macd >= prev_macd_sig:
            signals.append(('MACD_CROSS', 'SHORT'))
        
        if rsi < 20 and close > prev_close:
            signals.append(('RSI_OVERSOLD', 'LONG'))
        elif rsi > 80 and close < prev_close:
            signals.append(('RSI_OVERBOUGHT', 'SHORT'))
        
        if not signals:
            return None
        
        # Determine direction (majority vote if conflicting)
        longs = [s for s in signals if s[1] == 'LONG']
        shorts = [s for s in signals if s[1] == 'SHORT']
        
        if len(longs) > len(shorts):
            direction = 'LONG'
            signal_types = [s[0] for s in longs]
        elif len(shorts) > len(longs):
            direction = 'SHORT'
            signal_types = [s[0] for s in shorts]
        else:
            return None  # Conflicting signals
        
        if direction == 'LONG':
            sl = close - atr * self.ATR_SL
            tp = close + atr * self.ATR_TP
        else:
            sl = close + atr * self.ATR_SL
            tp = close - atr * self.ATR_TP
        
        return {
            'date': data.index[i].isoformat(),
            'direction': direction,
            'entry': round(close, 2),
            'stop_loss': round(sl, 2),
            'take_profit': round(tp, 2),
            'atr': round(atr, 2),
            'risk_usd': round(abs(close - sl), 2),
            'reward_usd': round(abs(tp - close), 2),
            'rr_ratio': round(abs(tp - close) / abs(close - sl), 2),
            'signal_types': signal_types,
            'indicators': {
                'ema_3': round(ema_3, 2),
                'ema_8': round(ema_8, 2),
                'rsi': round(rsi, 1),
                'macd': round(macd, 4),
                'macd_signal': round(macd_sig, 4)
            }
        }
    
    def calculate_position_size(self, signal, account_size=10000):
        """Calculate position size for prop firm challenge."""
        risk_amount = account_size * self.RISK_PER_TRADE
        position_size = risk_amount / signal['risk_usd']
        
        return {
            'account_size': account_size,
            'risk_pct': self.RISK_PER_TRADE * 100,
            'risk_amount': round(risk_amount, 2),
            'position_size_oz': round(position_size, 2),
            'position_lots': round(position_size / 100, 2)  # 1 lot = 100 oz
        }
    
    def run(self):
        """Run the live signal generator."""
        
        print("\n" + "=" * 70)
        print("🔴 LIVE XAU/USD SIGNAL GENERATOR")
        print("=" * 70)
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Fetch data
        data = self.fetch_live_data()
        
        if data is None:
            print("\n❌ Could not fetch data")
            return
        
        # Calculate indicators
        data = self.calculate_indicators(data)
        
        # Get current market status
        i = len(data) - 1
        print(f"\n📊 MARKET STATUS")
        print(f"   Date:  {data.index[i].strftime('%Y-%m-%d')}")
        print(f"   Close: ${data['close'].iloc[i]:.2f}")
        print(f"   ATR:   ${data['atr'].iloc[i]:.2f}")
        print(f"   RSI:   {data['rsi'].iloc[i]:.1f}")
        
        trend = "BULLISH 📈" if data['ema_3'].iloc[i] > data['ema_21'].iloc[i] else "BEARISH 📉"
        print(f"   Trend: {trend}")
        
        # Generate signal
        signal = self.get_signal(data)
        
        print(f"\n🚦 SIGNAL")
        print("-" * 50)
        
        if signal:
            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            print(f"\n   {direction_emoji} {signal['direction']} SIGNAL DETECTED!")
            print(f"\n   Signal Types: {', '.join(signal['signal_types'])}")
            print(f"\n   Entry Price:    ${signal['entry']:.2f}")
            print(f"   Stop Loss:      ${signal['stop_loss']:.2f}")
            print(f"   Take Profit:    ${signal['take_profit']:.2f}")
            print(f"\n   Risk:           ${signal['risk_usd']:.2f} per oz")
            print(f"   Reward:         ${signal['reward_usd']:.2f} per oz")
            print(f"   R:R Ratio:      1:{signal['rr_ratio']:.1f}")
            
            # Position sizing for different account sizes
            print(f"\n📐 POSITION SIZING")
            print("-" * 50)
            
            for account in [10000, 25000, 50000, 100000]:
                pos = self.calculate_position_size(signal, account)
                print(f"   ${account:,}: {pos['position_lots']:.2f} lots ({pos['position_size_oz']:.0f} oz) | Risk ${pos['risk_amount']:.0f}")
            
            # Log signal
            signal['generated_at'] = datetime.now().isoformat()
            self.signals['history'].append(signal)
            self.signals['pending'] = signal
            self.save_signal_log()
            
            print(f"\n✅ Signal logged to {self.signal_log}")
            
            # Trading instructions
            print(f"\n" + "=" * 70)
            print("📋 TRADING INSTRUCTIONS")
            print("=" * 70)
            print(f"""
    1. Open your trading platform (MT4/MT5/TradingView)
    
    2. Set up the trade:
       - Instrument: XAU/USD (Gold)
       - Direction:  {signal['direction']}
       - Entry:      ${signal['entry']:.2f} (market or limit)
       - Stop Loss:  ${signal['stop_loss']:.2f}
       - Take Profit: ${signal['take_profit']:.2f}
    
    3. For $10,000 account:
       - Position:   {self.calculate_position_size(signal, 10000)['position_lots']:.2f} lots
       - Risk:       8% (${self.calculate_position_size(signal, 10000)['risk_amount']:.0f})
    
    4. Management:
       - Move stop to breakeven at +1 ATR (${signal['atr']:.2f})
       - Trail stop at 0.5 ATR after breakeven
       - Let winner run to take profit
    
    ⚠️  IMPORTANT: Paper trade first if this is your first time!
    """)
        else:
            print("\n   ⏸️  NO SIGNAL TODAY")
            print("\n   Wait for next trading day.")
            print("   Run this script again tomorrow.")
            
            # Show what we're watching for
            print(f"\n📊 WATCHING FOR:")
            print(f"   - EMA 3/8 crossover")
            print(f"   - MACD crossover")
            print(f"   - RSI extreme reversal")
        
        # Show recent signal history
        if self.signals['history']:
            print(f"\n" + "=" * 70)
            print("📜 RECENT SIGNALS")
            print("=" * 70)
            
            recent = self.signals['history'][-5:]
            for s in reversed(recent):
                date = s.get('date', 'Unknown')[:10]
                direction = s.get('direction', 'N/A')
                entry = s.get('entry', 0)
                print(f"   {date}: {direction} @ ${entry:.2f}")


def main():
    generator = LiveSignalGenerator()
    generator.run()


if __name__ == "__main__":
    main()
