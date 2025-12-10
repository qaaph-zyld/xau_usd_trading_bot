"""
Trend-Momentum Strategy: A more sophisticated approach combining
multiple indicators for higher probability trades.

Key improvements over basic strategies:
1. Multi-indicator confirmation (trend + momentum + volatility)
2. Trend filter to avoid counter-trend trades
3. Volatility-based position sizing
4. Dynamic stop-loss and take-profit
5. Trade management with trailing stops
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from .base_strategy import BaseStrategy
import ta
import logging

logger = logging.getLogger(__name__)


class TrendMomentumStrategy(BaseStrategy):
    """
    A sophisticated strategy that combines:
    - Trend identification (EMA crossover + ADX)
    - Momentum confirmation (RSI + MACD)
    - Volatility filter (ATR-based)
    - Dynamic risk management
    """
    
    def __init__(self, 
                 data: pd.DataFrame,
                 # Trend parameters
                 fast_ema: int = 12,
                 slow_ema: int = 26,
                 trend_ema: int = 50,
                 adx_period: int = 14,
                 adx_threshold: float = 25.0,
                 # Momentum parameters
                 rsi_period: int = 14,
                 rsi_oversold: float = 35,
                 rsi_overbought: float = 65,
                 # Risk parameters
                 atr_period: int = 14,
                 atr_sl_multiplier: float = 1.5,
                 atr_tp_multiplier: float = 3.0,
                 risk_per_trade: float = 0.02,
                 # Capital
                 initial_capital: float = 100000):
        """
        Initialize the Trend-Momentum Strategy.
        
        Args:
            data: OHLCV DataFrame
            fast_ema: Fast EMA period for trend
            slow_ema: Slow EMA period for trend
            trend_ema: Long-term trend filter
            adx_period: ADX period for trend strength
            adx_threshold: Minimum ADX for trending market
            rsi_period: RSI calculation period
            rsi_oversold: RSI oversold level (for longs)
            rsi_overbought: RSI overbought level (for shorts)
            atr_period: ATR period for volatility
            atr_sl_multiplier: ATR multiplier for stop-loss
            atr_tp_multiplier: ATR multiplier for take-profit
            risk_per_trade: Risk per trade as fraction of capital
            initial_capital: Starting capital
        """
        super().__init__(data, initial_capital)
        
        # Store parameters
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.trend_ema = trend_ema
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.atr_period = atr_period
        self.atr_sl_multiplier = atr_sl_multiplier
        self.atr_tp_multiplier = atr_tp_multiplier
        self.risk_per_trade = risk_per_trade
        
        # Calculate indicators
        self._calculate_indicators()
        
    def _calculate_indicators(self):
        """Calculate all required technical indicators."""
        try:
            # Trend indicators
            self.data['ema_fast'] = ta.trend.ema_indicator(
                self.data['close'], window=self.fast_ema
            )
            self.data['ema_slow'] = ta.trend.ema_indicator(
                self.data['close'], window=self.slow_ema
            )
            self.data['ema_trend'] = ta.trend.ema_indicator(
                self.data['close'], window=self.trend_ema
            )
            
            # ADX for trend strength
            self.data['adx'] = ta.trend.adx(
                self.data['high'], self.data['low'], self.data['close'],
                window=self.adx_period
            )
            
            # Momentum indicators
            self.data['rsi'] = ta.momentum.rsi(
                self.data['close'], window=self.rsi_period
            )
            
            # MACD
            macd = ta.trend.MACD(self.data['close'])
            self.data['macd'] = macd.macd()
            self.data['macd_signal'] = macd.macd_signal()
            self.data['macd_hist'] = macd.macd_diff()
            
            # Volatility
            self.data['atr'] = ta.volatility.average_true_range(
                self.data['high'], self.data['low'], self.data['close'],
                window=self.atr_period
            )
            
            # Bollinger Bands for volatility context
            bb = ta.volatility.BollingerBands(self.data['close'])
            self.data['bb_upper'] = bb.bollinger_hband()
            self.data['bb_lower'] = bb.bollinger_lband()
            self.data['bb_width'] = (self.data['bb_upper'] - self.data['bb_lower']) / self.data['close']
            
            logger.info("Calculated all indicators for Trend-Momentum Strategy")
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise
    
    def generate_signals(self) -> pd.Series:
        """
        Generate trading signals based on multi-indicator confirmation.
        
        Signal Logic (Relaxed for more trades):
        LONG when:
        - Price above trend EMA (uptrend) OR Fast EMA > Slow EMA
        - RSI crosses above oversold OR RSI < 50 and rising
        - MACD histogram positive or turning positive
        
        SHORT when:
        - Price below trend EMA (downtrend) OR Fast EMA < Slow EMA
        - RSI crosses below overbought OR RSI > 50 and falling
        - MACD histogram negative or turning negative
        
        Returns:
            Series with signals: 1 (long), -1 (short), 0 (no signal)
        """
        signals = pd.Series(index=self.data.index, data=0)
        
        # Trend conditions (more relaxed)
        uptrend = (self.data['close'] > self.data['ema_trend']) | \
                  (self.data['ema_fast'] > self.data['ema_slow'])
        downtrend = (self.data['close'] < self.data['ema_trend']) | \
                    (self.data['ema_fast'] < self.data['ema_slow'])
        
        # EMA crossover
        ema_cross_up = (self.data['ema_fast'] > self.data['ema_slow']) & \
                       (self.data['ema_fast'].shift(1) <= self.data['ema_slow'].shift(1))
        ema_cross_down = (self.data['ema_fast'] < self.data['ema_slow']) & \
                         (self.data['ema_fast'].shift(1) >= self.data['ema_slow'].shift(1))
        
        # RSI conditions (more signals)
        rsi_buy = (self.data['rsi'] > self.rsi_oversold) & \
                  (self.data['rsi'].shift(1) <= self.rsi_oversold)
        rsi_sell = (self.data['rsi'] < self.rsi_overbought) & \
                   (self.data['rsi'].shift(1) >= self.rsi_overbought)
        
        # MACD conditions
        macd_cross_up = (self.data['macd_hist'] > 0) & (self.data['macd_hist'].shift(1) <= 0)
        macd_cross_down = (self.data['macd_hist'] < 0) & (self.data['macd_hist'].shift(1) >= 0)
        
        # Combined signals - need 2 of 3 confirmations
        # Long: (EMA crossover OR RSI buy) AND (uptrend OR MACD bullish)
        long_signal = ((ema_cross_up | rsi_buy | macd_cross_up) & uptrend)
        short_signal = ((ema_cross_down | rsi_sell | macd_cross_down) & downtrend)
        
        signals[long_signal] = 1
        signals[short_signal] = -1
        
        return signals
    
    def calculate_position_size(self, signal: float, current_price: float, 
                                current_capital: float = None, atr: float = None) -> float:
        """
        Calculate position size based on ATR-adjusted risk.
        
        Uses volatility-adjusted position sizing:
        Position Size = (Capital × Risk%) / (ATR × SL Multiplier)
        """
        if signal == 0:
            return 0
        
        capital = current_capital if current_capital is not None else self.initial_capital
        
        # Get current ATR for volatility-adjusted sizing
        if atr is None or pd.isna(atr):
            atr = current_price * 0.01  # Default to 1% if ATR not available
        
        # Calculate stop distance
        stop_distance = atr * self.atr_sl_multiplier
        
        # Risk amount
        risk_amount = capital * self.risk_per_trade
        
        # Position size based on risk
        position_size = risk_amount / stop_distance
        
        # Cap at maximum position size (10% of capital at current price)
        max_position = (capital * 0.10) / current_price
        position_size = min(position_size, max_position)
        
        return position_size if signal > 0 else -position_size
    
    def backtest(self) -> Dict[str, Any]:
        """
        Enhanced backtest with proper stop-loss, take-profit, and trailing stops.
        """
        try:
            signals = self.generate_signals()
            
            current_position = 0
            entry_price = 0
            stop_loss = 0
            take_profit = 0
            highest_since_entry = 0
            lowest_since_entry = float('inf')
            
            trades = []
            current_trade = None
            
            for i in range(len(self.data)):
                if i == 0:
                    self.positions.iloc[i] = 0
                    self.capital.iloc[i] = self.initial_capital
                    continue
                
                current_price = self.data['close'].iloc[i]
                high_price = self.data['high'].iloc[i]
                low_price = self.data['low'].iloc[i]
                current_signal = signals.iloc[i]
                current_atr = self.data['atr'].iloc[i]
                prev_capital = self.capital.iloc[i-1]
                
                if pd.isna(prev_capital):
                    prev_capital = self.initial_capital
                
                # Check for stop-loss or take-profit hit
                if current_position != 0:
                    # Update trailing values
                    if current_position > 0:  # Long
                        highest_since_entry = max(highest_since_entry, high_price)
                        
                        # Trailing stop: move stop up as price rises
                        trailing_stop = highest_since_entry - (current_atr * self.atr_sl_multiplier)
                        if trailing_stop > stop_loss:
                            stop_loss = trailing_stop
                        
                        # Check if stopped out
                        if low_price <= stop_loss:
                            exit_price = stop_loss
                            pnl = (exit_price - entry_price) * abs(current_position)
                            prev_capital += pnl
                            if current_trade:
                                current_trade['exit_price'] = exit_price
                                current_trade['exit_reason'] = 'stop_loss'
                                current_trade['pnl'] = pnl
                                trades.append(current_trade)
                            current_position = 0
                            current_trade = None
                        
                        # Check if take-profit hit
                        elif high_price >= take_profit:
                            exit_price = take_profit
                            pnl = (exit_price - entry_price) * abs(current_position)
                            prev_capital += pnl
                            if current_trade:
                                current_trade['exit_price'] = exit_price
                                current_trade['exit_reason'] = 'take_profit'
                                current_trade['pnl'] = pnl
                                trades.append(current_trade)
                            current_position = 0
                            current_trade = None
                    
                    else:  # Short
                        lowest_since_entry = min(lowest_since_entry, low_price)
                        
                        # Trailing stop for shorts
                        trailing_stop = lowest_since_entry + (current_atr * self.atr_sl_multiplier)
                        if trailing_stop < stop_loss:
                            stop_loss = trailing_stop
                        
                        # Check if stopped out
                        if high_price >= stop_loss:
                            exit_price = stop_loss
                            pnl = (entry_price - exit_price) * abs(current_position)
                            prev_capital += pnl
                            if current_trade:
                                current_trade['exit_price'] = exit_price
                                current_trade['exit_reason'] = 'stop_loss'
                                current_trade['pnl'] = pnl
                                trades.append(current_trade)
                            current_position = 0
                            current_trade = None
                        
                        # Check if take-profit hit
                        elif low_price <= take_profit:
                            exit_price = take_profit
                            pnl = (entry_price - exit_price) * abs(current_position)
                            prev_capital += pnl
                            if current_trade:
                                current_trade['exit_price'] = exit_price
                                current_trade['exit_reason'] = 'take_profit'
                                current_trade['pnl'] = pnl
                                trades.append(current_trade)
                            current_position = 0
                            current_trade = None
                
                # New signal processing
                if current_signal != 0 and current_position == 0:
                    # Enter new position
                    current_position = self.calculate_position_size(
                        current_signal, current_price, prev_capital, current_atr
                    )
                    entry_price = current_price
                    
                    if current_signal > 0:  # Long
                        stop_loss = entry_price - (current_atr * self.atr_sl_multiplier)
                        take_profit = entry_price + (current_atr * self.atr_tp_multiplier)
                        highest_since_entry = current_price
                    else:  # Short
                        stop_loss = entry_price + (current_atr * self.atr_sl_multiplier)
                        take_profit = entry_price - (current_atr * self.atr_tp_multiplier)
                        lowest_since_entry = current_price
                    
                    current_trade = {
                        'entry_date': self.data.index[i],
                        'entry_price': entry_price,
                        'side': 'long' if current_signal > 0 else 'short',
                        'size': abs(current_position),
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
                
                # Handle opposite signal (reverse position)
                elif current_signal != 0 and np.sign(current_signal) != np.sign(current_position):
                    # Close current position
                    if current_position > 0:
                        pnl = (current_price - entry_price) * abs(current_position)
                    else:
                        pnl = (entry_price - current_price) * abs(current_position)
                    
                    prev_capital += pnl
                    if current_trade:
                        current_trade['exit_price'] = current_price
                        current_trade['exit_reason'] = 'signal_reversal'
                        current_trade['pnl'] = pnl
                        trades.append(current_trade)
                    
                    # Enter new position
                    current_position = self.calculate_position_size(
                        current_signal, current_price, prev_capital, current_atr
                    )
                    entry_price = current_price
                    
                    if current_signal > 0:
                        stop_loss = entry_price - (current_atr * self.atr_sl_multiplier)
                        take_profit = entry_price + (current_atr * self.atr_tp_multiplier)
                        highest_since_entry = current_price
                    else:
                        stop_loss = entry_price + (current_atr * self.atr_sl_multiplier)
                        take_profit = entry_price - (current_atr * self.atr_tp_multiplier)
                        lowest_since_entry = current_price
                    
                    current_trade = {
                        'entry_date': self.data.index[i],
                        'entry_price': entry_price,
                        'side': 'long' if current_signal > 0 else 'short',
                        'size': abs(current_position),
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
                
                self.positions.iloc[i] = current_position
                self.capital.iloc[i] = prev_capital
            
            # Store trades for analysis
            self.trades = trades
            
            return self._calculate_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error during backtesting: {str(e)}")
            raise
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics including trade-based stats."""
        # Get base metrics
        metrics = super()._calculate_performance_metrics()
        
        # Add trade-based metrics
        if hasattr(self, 'trades') and self.trades:
            trades_df = pd.DataFrame(self.trades)
            
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] < 0]
            
            metrics['total_trades'] = len(self.trades)
            metrics['winning_trades'] = len(winning_trades)
            metrics['losing_trades'] = len(losing_trades)
            metrics['win_rate'] = len(winning_trades) / len(self.trades) if self.trades else 0
            
            # Average win/loss
            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = abs(losing_trades['pnl'].mean()) if len(losing_trades) > 0 else 0
            metrics['avg_win'] = avg_win
            metrics['avg_loss'] = avg_loss
            metrics['risk_reward_ratio'] = avg_win / avg_loss if avg_loss > 0 else float('inf')
            
            # Profit factor
            gross_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
            gross_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0
            metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Exit reason breakdown
            if 'exit_reason' in trades_df.columns:
                exit_counts = trades_df['exit_reason'].value_counts().to_dict()
                metrics['exits_by_stop_loss'] = exit_counts.get('stop_loss', 0)
                metrics['exits_by_take_profit'] = exit_counts.get('take_profit', 0)
                metrics['exits_by_signal'] = exit_counts.get('signal_reversal', 0)
        
        return metrics
