"""
🔗 MT5 BROKER INTEGRATION

Ready-to-use MetaTrader 5 integration for live trading.

Requirements:
    pip install MetaTrader5

Usage:
    from src.broker.mt5_integration import MT5Broker
    broker = MT5Broker()
    broker.connect()
"""

import sys
import os
from datetime import datetime
from pathlib import Path


class MT5Broker:
    """
    MetaTrader 5 broker integration.
    
    Features:
    - Connect to MT5 terminal
    - Fetch live XAU/USD prices
    - Execute trades with SL/TP
    - Track open positions
    - Get account info
    """
    
    SYMBOL = "XAUUSD"  # May vary by broker (GOLD, XAUUSD, etc.)
    
    def __init__(self):
        self.connected = False
        self.mt5 = None
        
    def connect(self, login=None, password=None, server=None):
        """
        Connect to MT5 terminal.
        
        If credentials not provided, uses the logged-in account.
        """
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
        except ImportError:
            print("❌ MetaTrader5 not installed!")
            print("   Run: pip install MetaTrader5")
            print("   Note: Only works on Windows with MT5 installed")
            return False
        
        # Initialize
        if not self.mt5.initialize():
            print(f"❌ MT5 initialization failed: {self.mt5.last_error()}")
            return False
        
        # Login if credentials provided
        if login and password and server:
            authorized = self.mt5.login(login, password=password, server=server)
            if not authorized:
                print(f"❌ Login failed: {self.mt5.last_error()}")
                self.mt5.shutdown()
                return False
        
        self.connected = True
        print("✅ Connected to MT5")
        
        # Print account info
        account = self.mt5.account_info()
        if account:
            print(f"   Account: {account.login}")
            print(f"   Balance: ${account.balance:,.2f}")
            print(f"   Equity:  ${account.equity:,.2f}")
            print(f"   Server:  {account.server}")
        
        return True
    
    def disconnect(self):
        """Disconnect from MT5."""
        if self.mt5:
            self.mt5.shutdown()
            self.connected = False
            print("✅ Disconnected from MT5")
    
    def get_price(self):
        """Get current XAU/USD price."""
        if not self.connected:
            return None
        
        tick = self.mt5.symbol_info_tick(self.SYMBOL)
        if tick is None:
            # Try alternative symbols
            for sym in ["GOLD", "XAUUSD", "XAUUSDm", "GOLD.a"]:
                tick = self.mt5.symbol_info_tick(sym)
                if tick:
                    self.SYMBOL = sym
                    break
        
        if tick:
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': round((tick.ask - tick.bid), 2),
                'time': datetime.fromtimestamp(tick.time)
            }
        return None
    
    def get_account_info(self):
        """Get account information."""
        if not self.connected:
            return None
        
        account = self.mt5.account_info()
        if account:
            return {
                'login': account.login,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free,
                'profit': account.profit,
                'leverage': account.leverage,
                'currency': account.currency
            }
        return None
    
    def place_order(self, direction, lots, sl=None, tp=None, comment="PropFirmBot"):
        """
        Place a market order.
        
        Args:
            direction: 'LONG' or 'SHORT'
            lots: Position size in lots
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
        
        Returns:
            Order result dict or None on failure
        """
        if not self.connected:
            print("❌ Not connected to MT5")
            return None
        
        symbol_info = self.mt5.symbol_info(self.SYMBOL)
        if symbol_info is None:
            print(f"❌ Symbol {self.SYMBOL} not found")
            return None
        
        if not symbol_info.visible:
            if not self.mt5.symbol_select(self.SYMBOL, True):
                print(f"❌ Failed to select {self.SYMBOL}")
                return None
        
        price = self.mt5.symbol_info_tick(self.SYMBOL)
        
        if direction == 'LONG':
            order_type = self.mt5.ORDER_TYPE_BUY
            entry_price = price.ask
        else:
            order_type = self.mt5.ORDER_TYPE_SELL
            entry_price = price.bid
        
        # Prepare request
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": self.SYMBOL,
            "volume": lots,
            "type": order_type,
            "price": entry_price,
            "deviation": 20,  # Max slippage in points
            "magic": 123456,  # Magic number to identify our trades
            "comment": comment,
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        
        if sl:
            request["sl"] = sl
        if tp:
            request["tp"] = tp
        
        # Execute
        result = self.mt5.order_send(request)
        
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            print(f"❌ Order failed: {result.comment}")
            return None
        
        print(f"✅ Order executed!")
        print(f"   Direction: {direction}")
        print(f"   Lots: {lots}")
        print(f"   Entry: ${entry_price:.2f}")
        if sl:
            print(f"   SL: ${sl:.2f}")
        if tp:
            print(f"   TP: ${tp:.2f}")
        
        return {
            'ticket': result.order,
            'direction': direction,
            'lots': lots,
            'entry': entry_price,
            'sl': sl,
            'tp': tp
        }
    
    def close_position(self, ticket):
        """Close a position by ticket number."""
        if not self.connected:
            return False
        
        position = self.mt5.positions_get(ticket=ticket)
        if not position:
            print(f"❌ Position {ticket} not found")
            return False
        
        pos = position[0]
        
        # Determine close direction
        if pos.type == self.mt5.ORDER_TYPE_BUY:
            order_type = self.mt5.ORDER_TYPE_SELL
            price = self.mt5.symbol_info_tick(pos.symbol).bid
        else:
            order_type = self.mt5.ORDER_TYPE_BUY
            price = self.mt5.symbol_info_tick(pos.symbol).ask
        
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "Close by bot",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        
        result = self.mt5.order_send(request)
        
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            print(f"❌ Close failed: {result.comment}")
            return False
        
        print(f"✅ Position {ticket} closed")
        return True
    
    def get_positions(self):
        """Get all open positions."""
        if not self.connected:
            return []
        
        positions = self.mt5.positions_get(symbol=self.SYMBOL)
        if positions is None:
            return []
        
        result = []
        for pos in positions:
            result.append({
                'ticket': pos.ticket,
                'direction': 'LONG' if pos.type == 0 else 'SHORT',
                'lots': pos.volume,
                'entry': pos.price_open,
                'current': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'time': datetime.fromtimestamp(pos.time)
            })
        
        return result
    
    def modify_sl_tp(self, ticket, sl=None, tp=None):
        """Modify stop loss or take profit of a position."""
        if not self.connected:
            return False
        
        position = self.mt5.positions_get(ticket=ticket)
        if not position:
            return False
        
        pos = position[0]
        
        request = {
            "action": self.mt5.TRADE_ACTION_SLTP,
            "symbol": pos.symbol,
            "position": ticket,
            "sl": sl if sl else pos.sl,
            "tp": tp if tp else pos.tp,
        }
        
        result = self.mt5.order_send(request)
        
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            print(f"❌ Modify failed: {result.comment}")
            return False
        
        print(f"✅ Position {ticket} modified")
        return True


def test_connection():
    """Test MT5 connection."""
    broker = MT5Broker()
    
    if broker.connect():
        # Get price
        price = broker.get_price()
        if price:
            print(f"\nXAU/USD Price:")
            print(f"   Bid: ${price['bid']:.2f}")
            print(f"   Ask: ${price['ask']:.2f}")
            print(f"   Spread: ${price['spread']:.2f}")
        
        # Get positions
        positions = broker.get_positions()
        print(f"\nOpen positions: {len(positions)}")
        for pos in positions:
            print(f"   {pos['direction']} {pos['lots']} lots @ ${pos['entry']:.2f} | P/L: ${pos['profit']:.2f}")
        
        broker.disconnect()
    else:
        print("\n⚠️  MT5 Connection not available")
        print("   This is normal if:")
        print("   - MT5 is not installed")
        print("   - Running on Mac/Linux")
        print("   - No broker account configured")
        print("\n   The bot will work in paper trading mode instead.")


if __name__ == "__main__":
    test_connection()
