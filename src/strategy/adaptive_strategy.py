"""
Adaptive Trading Strategy

A practical strategy that adapts to market conditions and generates
consistent signals while maintaining profitability.

Key differences from previous attempts:
1. Uses simpler, more reliable signals
2. Adapts parameters based on volatility
3. Trend-following with momentum confirmation
4. Proper position sizing and risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import ta
import logging

logger = logging.getLogger(__name__)


class AdaptiveStrategy:
    """
    An adaptive trend-following strategy with:
    - Dynamic parameter adjustment based on volatility
    - Multiple timeframe trend confirmation
    - Smart entry on pullbacks
    - Trailing stop exits
    """
    
    def __init__(self,
                 data: pd.DataFrame,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.02,
                 atr_multiplier_sl: float = 2.0,
                 atr_multiplier_tp: float = 4.0):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.atr_multiplier_sl = atr_multiplier_sl
        self.atr_multiplier_tp = atr_multiplier_tp
        
        self.positions = pd.Series(index=data.index, data=0.0)
        self.capital = pd.Series(index=data.index, data=0.0)
        self.trades = []
        
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate all technical indicators."""
        
        # Trend indicators
        self.data['ema_8'] = ta.trend.ema_indicator(self.data['close'], window=8)
        self.data['ema_21'] = ta.trend.ema_indicator(self.data['close'], window=21)
        self.data['ema_55'] = ta.trend.ema_indicator(self.data['close'], window=55)
        self.data['sma_200'] = ta.trend.sma_indicator(self.data['close'], window=200)
        
        # ADX for trend strength
        self.data['adx'] = ta.trend.adx(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        self.data['di_plus'] = ta.trend.adx_pos(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        self.data['di_minus'] = ta.trend.adx_neg(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        
        # Momentum
        self.data['rsi'] = ta.momentum.rsi(self.data['close'], window=14)
        
        # MACD
        macd = ta.trend.MACD(self.data['close'], window_slow=26, window_fast=12, window_sign=9)
        self.data['macd'] = macd.macd()
        self.data['macd_signal'] = macd.macd_signal()
        self.data['macd_hist'] = macd.macd_diff()
        
        # Volatility
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(self.data['close'], window=20, window_dev=2)
        self.data['bb_upper'] = bb.bollinger_hband()
        self.data['bb_lower'] = bb.bollinger_lband()
        self.data['bb_mid'] = bb.bollinger_mavg()
        self.data['bb_pct'] = bb.bollinger_pband()
        
        # Price position relative to bands
        self.data['close_vs_bb'] = (self.data['close'] - self.data['bb_lower']) / \
                                   (self.data['bb_upper'] - self.data['bb_lower'])
        
        # Candle patterns
        self.data['body'] = abs(self.data['close'] - self.data['open'])
        self.data['range'] = self.data['high'] - self.data['low']
        self.data['body_ratio'] = self.data['body'] / self.data['range'].replace(0, np.nan)
        
        # Higher highs / lower lows
        self.data['hh'] = self.data['high'] > self.data['high'].shift(1)
        self.data['ll'] = self.data['low'] < self.data['low'].shift(1)
        self.data['hl'] = self.data['low'] > self.data['low'].shift(1)
        self.data['lh'] = self.data['high'] < self.data['high'].shift(1)
        
    def _get_trend(self, idx: int) -> int:
        """
        Determine trend direction.
        Returns: 1 (bullish), -1 (bearish), 0 (neutral)
        """
        if idx < 55:
            return 0
        
        close = self.data['close'].iloc[idx]
        ema_8 = self.data['ema_8'].iloc[idx]
        ema_21 = self.data['ema_21'].iloc[idx]
        ema_55 = self.data['ema_55'].iloc[idx]
        adx = self.data['adx'].iloc[idx]
        di_plus = self.data['di_plus'].iloc[idx]
        di_minus = self.data['di_minus'].iloc[idx]
        
        # Strong uptrend: EMAs aligned, ADX showing strength
        if ema_8 > ema_21 > ema_55 and adx > 20 and di_plus > di_minus:
            return 1
        
        # Strong downtrend
        if ema_8 < ema_21 < ema_55 and adx > 20 and di_minus > di_plus:
            return -1
        
        return 0
    
    def _get_momentum(self, idx: int) -> int:
        """Check momentum confirmation."""
        if idx < 2:
            return 0
        
        macd_hist = self.data['macd_hist'].iloc[idx]
        macd_hist_prev = self.data['macd_hist'].iloc[idx-1]
        rsi = self.data['rsi'].iloc[idx]
        
        # Bullish momentum: MACD histogram rising, RSI not overbought
        if macd_hist > macd_hist_prev and macd_hist > -0.5 and rsi < 70:
            return 1
        
        # Bearish momentum
        if macd_hist < macd_hist_prev and macd_hist < 0.5 and rsi > 30:
            return -1
        
        return 0
    
    def _is_pullback_entry(self, idx: int, direction: int) -> bool:
        """Check if current bar is a pullback entry opportunity."""
        if idx < 5:
            return False
        
        close = self.data['close'].iloc[idx]
        ema_21 = self.data['ema_21'].iloc[idx]
        bb_pct = self.data['bb_pct'].iloc[idx]
        rsi = self.data['rsi'].iloc[idx]
        
        if direction == 1:  # Looking for long entry
            # Price pulled back to EMA or lower BB
            near_ema = (close - ema_21) / close < 0.01  # Within 1% of EMA
            near_lower_bb = bb_pct < 0.3  # In lower 30% of BB
            rsi_oversold = rsi < 45  # RSI pulling back
            
            # Higher low forming
            hl = self.data['hl'].iloc[idx]
            
            return (near_ema or near_lower_bb) and rsi_oversold
        
        elif direction == -1:  # Looking for short entry
            near_ema = (ema_21 - close) / close < 0.01
            near_upper_bb = bb_pct > 0.7
            rsi_overbought = rsi > 55
            
            lh = self.data['lh'].iloc[idx]
            
            return (near_ema or near_upper_bb) and rsi_overbought
        
        return False
    
    def _check_entry(self, idx: int) -> Optional[Dict]:
        """Check for entry signal."""
        if idx < 60:
            return None
        
        trend = self._get_trend(idx)
        if trend == 0:
            return None
        
        momentum = self._get_momentum(idx)
        if momentum != trend:
            return None
        
        if not self._is_pullback_entry(idx, trend):
            return None
        
        # Entry confirmed
        close = self.data['close'].iloc[idx]
        atr = self.data['atr'].iloc[idx]
        
        if pd.isna(atr) or atr <= 0:
            atr = close * 0.01
        
        if trend == 1:  # Long
            stop_loss = close - atr * self.atr_multiplier_sl
            take_profit = close + atr * self.atr_multiplier_tp
        else:  # Short
            stop_loss = close + atr * self.atr_multiplier_sl
            take_profit = close - atr * self.atr_multiplier_tp
        
        return {
            'direction': trend,
            'entry_price': close,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'atr': atr
        }
    
    def generate_signals(self) -> pd.Series:
        """Generate trading signals."""
        signals = pd.Series(index=self.data.index, data=0)
        
        for i in range(60, len(self.data)):
            entry = self._check_entry(i)
            if entry:
                signals.iloc[i] = entry['direction']
        
        return signals
    
    def backtest(self) -> Dict[str, Any]:
        """Run backtest with proper risk management."""
        
        capital = self.initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        trailing_stop = 0
        entry_atr = 0
        
        self.trades = []
        current_trade = None
        
        for i in range(len(self.data)):
            if i < 60:
                self.capital.iloc[i] = capital
                self.positions.iloc[i] = 0
                continue
            
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            atr = self.data['atr'].iloc[i] if not pd.isna(self.data['atr'].iloc[i]) else close * 0.01
            
            # Manage existing position
            if position != 0:
                if position > 0:  # Long
                    # Update trailing stop
                    new_trail = high - atr * 1.5
                    if new_trail > trailing_stop:
                        trailing_stop = new_trail
                    
                    # Check exits
                    effective_stop = max(stop_loss, trailing_stop)
                    
                    if low <= effective_stop:
                        # Stop hit
                        exit_price = effective_stop
                        pnl = (exit_price - entry_price) * position
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = exit_price
                            current_trade['exit_reason'] = 'stop_loss'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
                    
                    elif high >= take_profit:
                        # Take profit hit
                        exit_price = take_profit
                        pnl = (exit_price - entry_price) * position
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = exit_price
                            current_trade['exit_reason'] = 'take_profit'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
                
                else:  # Short
                    # Update trailing stop
                    new_trail = low + atr * 1.5
                    if trailing_stop == 0 or new_trail < trailing_stop:
                        trailing_stop = new_trail
                    
                    effective_stop = min(stop_loss, trailing_stop) if trailing_stop > 0 else stop_loss
                    
                    if high >= effective_stop:
                        exit_price = effective_stop
                        pnl = (entry_price - exit_price) * abs(position)
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = exit_price
                            current_trade['exit_reason'] = 'stop_loss'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
                    
                    elif low <= take_profit:
                        exit_price = take_profit
                        pnl = (entry_price - exit_price) * abs(position)
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = exit_price
                            current_trade['exit_reason'] = 'take_profit'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
            
            # Check for new entry
            if position == 0:
                entry = self._check_entry(i)
                
                if entry:
                    # Calculate position size
                    risk_amount = capital * self.risk_per_trade
                    risk_per_unit = abs(entry['entry_price'] - entry['stop_loss'])
                    
                    if risk_per_unit > 0:
                        position_size = risk_amount / risk_per_unit
                        max_size = (capital * 0.1) / entry['entry_price']
                        position_size = min(position_size, max_size)
                        
                        position = position_size if entry['direction'] > 0 else -position_size
                        entry_price = entry['entry_price']
                        stop_loss = entry['stop_loss']
                        take_profit = entry['take_profit']
                        trailing_stop = stop_loss if entry['direction'] > 0 else stop_loss
                        entry_atr = entry['atr']
                        
                        current_trade = {
                            'entry_date': self.data.index[i],
                            'entry_price': entry_price,
                            'side': 'long' if entry['direction'] > 0 else 'short',
                            'size': abs(position),
                            'stop_loss': stop_loss,
                            'take_profit': take_profit
                        }
            
            self.positions.iloc[i] = position
            unrealized_pnl = (close - entry_price) * position if position != 0 else 0
            self.capital.iloc[i] = capital + unrealized_pnl
        
        # Close remaining position
        if position != 0:
            close = self.data['close'].iloc[-1]
            pnl = (close - entry_price) * position if position > 0 else (entry_price - close) * abs(position)
            capital += pnl
            
            if current_trade:
                current_trade['exit_price'] = close
                current_trade['exit_reason'] = 'end_of_data'
                current_trade['pnl'] = pnl
                self.trades.append(current_trade)
        
        return self._calculate_metrics(capital)
    
    def _calculate_metrics(self, final_capital: float) -> Dict[str, Any]:
        """Calculate performance metrics."""
        
        base_metrics = {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'net_profit': final_capital - self.initial_capital,
            'total_return': (final_capital - self.initial_capital) / self.initial_capital,
            'total_return_pct': ((final_capital - self.initial_capital) / self.initial_capital) * 100,
            'total_trades': len(self.trades),
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'win_rate_pct': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'risk_reward_ratio': 0,
            'profit_factor': 0,
            'max_drawdown_pct': 0,
            'sharpe_ratio': 0,
            'gross_profit': 0,
            'gross_loss': 0
        }
        
        if not self.trades:
            return base_metrics
        
        trades_df = pd.DataFrame(self.trades)
        
        winners = trades_df[trades_df['pnl'] > 0]
        losers = trades_df[trades_df['pnl'] < 0]
        
        base_metrics['winning_trades'] = len(winners)
        base_metrics['losing_trades'] = len(losers)
        base_metrics['win_rate'] = len(winners) / len(trades_df)
        base_metrics['win_rate_pct'] = base_metrics['win_rate'] * 100
        
        base_metrics['avg_win'] = winners['pnl'].mean() if len(winners) > 0 else 0
        base_metrics['avg_loss'] = abs(losers['pnl'].mean()) if len(losers) > 0 else 0
        
        if base_metrics['avg_loss'] > 0:
            base_metrics['risk_reward_ratio'] = base_metrics['avg_win'] / base_metrics['avg_loss']
        
        base_metrics['gross_profit'] = winners['pnl'].sum() if len(winners) > 0 else 0
        base_metrics['gross_loss'] = abs(losers['pnl'].sum()) if len(losers) > 0 else 0
        
        if base_metrics['gross_loss'] > 0:
            base_metrics['profit_factor'] = base_metrics['gross_profit'] / base_metrics['gross_loss']
        
        # Drawdown
        equity = self.capital.dropna()
        if len(equity) > 0:
            rolling_max = equity.expanding().max()
            drawdown = (equity - rolling_max) / rolling_max
            base_metrics['max_drawdown_pct'] = abs(drawdown.min()) * 100
        
        # Sharpe
        returns = equity.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            base_metrics['sharpe_ratio'] = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        
        return base_metrics
