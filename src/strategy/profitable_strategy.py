"""
Profitable Trading Strategy

A professional-grade strategy designed for real profitability based on:
1. Market regime detection (trending vs ranging)
2. Multi-timeframe confirmation
3. Volatility-adjusted entries
4. Smart money concepts (support/resistance, order flow)
5. Adaptive position sizing
6. Dynamic trailing stops

Key principles:
- Trade WITH the trend (never counter-trend)
- Enter on pullbacks, not breakouts
- Let winners run, cut losers quickly
- Size positions based on volatility
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import ta
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeSetup:
    """Represents a high-probability trade setup."""
    direction: int  # 1 for long, -1 for short
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    position_size: float
    confidence: float  # 0-1 confidence score
    reason: str


class MarketRegimeDetector:
    """Detects market regime: trending, ranging, or volatile."""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self._calculate_regime_indicators()
    
    def _calculate_regime_indicators(self):
        """Calculate indicators for regime detection."""
        # ADX for trend strength
        self.data['adx'] = ta.trend.adx(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        
        # Bollinger Band width for volatility
        bb = ta.volatility.BollingerBands(self.data['close'], window=20, window_dev=2)
        self.data['bb_width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / self.data['close']
        
        # ATR for volatility
        self.data['atr'] = ta.volatility.average_true_range(
            self.data['high'], self.data['low'], self.data['close'], window=14
        )
        self.data['atr_pct'] = self.data['atr'] / self.data['close']
        
        # Trend direction
        self.data['ema_20'] = ta.trend.ema_indicator(self.data['close'], window=20)
        self.data['ema_50'] = ta.trend.ema_indicator(self.data['close'], window=50)
        self.data['ema_200'] = ta.trend.ema_indicator(self.data['close'], window=200)
        
        # Price momentum
        self.data['roc_10'] = ta.momentum.roc(self.data['close'], window=10)
        
    def get_regime(self, idx: int) -> str:
        """
        Get market regime at specific index.
        
        Returns:
            'strong_uptrend', 'weak_uptrend', 'strong_downtrend', 'weak_downtrend', 'ranging'
        """
        if idx < 200:
            return 'unknown'
        
        adx = self.data['adx'].iloc[idx]
        close = self.data['close'].iloc[idx]
        ema_20 = self.data['ema_20'].iloc[idx]
        ema_50 = self.data['ema_50'].iloc[idx]
        ema_200 = self.data['ema_200'].iloc[idx]
        
        # Trend direction
        bullish = close > ema_20 > ema_50 > ema_200
        bearish = close < ema_20 < ema_50 < ema_200
        
        # Trend strength
        if adx > 30:
            if bullish:
                return 'strong_uptrend'
            elif bearish:
                return 'strong_downtrend'
        elif adx > 20:
            if bullish:
                return 'weak_uptrend'
            elif bearish:
                return 'weak_downtrend'
        
        return 'ranging'
    
    def get_trend_direction(self, idx: int) -> int:
        """Get trend direction: 1 for up, -1 for down, 0 for ranging."""
        regime = self.get_regime(idx)
        if 'uptrend' in regime:
            return 1
        elif 'downtrend' in regime:
            return -1
        return 0


class SupportResistanceDetector:
    """Detect key support and resistance levels."""
    
    def __init__(self, data: pd.DataFrame, lookback: int = 50):
        self.data = data
        self.lookback = lookback
    
    def find_levels(self, idx: int) -> Dict[str, List[float]]:
        """Find support and resistance levels near current price."""
        if idx < self.lookback:
            return {'support': [], 'resistance': []}
        
        window_data = self.data.iloc[max(0, idx - self.lookback):idx]
        current_price = self.data['close'].iloc[idx]
        
        # Find swing highs and lows
        highs = window_data['high'].values
        lows = window_data['low'].values
        
        # Pivot points
        pivot_highs = []
        pivot_lows = []
        
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                pivot_highs.append(highs[i])
            
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                pivot_lows.append(lows[i])
        
        # Filter levels near current price (within 3%)
        nearby_resistance = [h for h in pivot_highs if h > current_price and h < current_price * 1.03]
        nearby_support = [l for l in pivot_lows if l < current_price and l > current_price * 0.97]
        
        return {
            'support': sorted(nearby_support, reverse=True)[:3],
            'resistance': sorted(nearby_resistance)[:3]
        }


class ProfitableStrategy:
    """
    A strategy designed for consistent profitability.
    
    Core principles:
    1. Only trade in the direction of the higher timeframe trend
    2. Enter on pullbacks to key levels, not breakouts
    3. Use multiple confirmation signals
    4. Dynamic position sizing based on volatility
    5. Trailing stops to let winners run
    """
    
    def __init__(self, 
                 data: pd.DataFrame,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.01,  # 1% risk per trade
                 min_rr_ratio: float = 2.0,  # Minimum risk:reward
                 max_positions: int = 3):
        """
        Initialize the profitable strategy.
        
        Args:
            data: OHLCV DataFrame
            initial_capital: Starting capital
            risk_per_trade: Maximum risk per trade (as fraction)
            min_rr_ratio: Minimum risk:reward ratio to take trade
            max_positions: Maximum concurrent positions
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.min_rr_ratio = min_rr_ratio
        self.max_positions = max_positions
        
        # Initialize components
        self.regime_detector = MarketRegimeDetector(self.data)
        self.sr_detector = SupportResistanceDetector(self.data)
        
        # Calculate additional indicators
        self._calculate_indicators()
        
        # Track state
        self.positions = pd.Series(index=data.index, data=0.0)
        self.capital = pd.Series(index=data.index, data=0.0)
        self.trades = []
        
    def _calculate_indicators(self):
        """Calculate all required indicators."""
        # RSI with divergence detection
        self.data['rsi'] = ta.momentum.rsi(self.data['close'], window=14)
        
        # Stochastic for oversold/overbought in pullbacks
        stoch = ta.momentum.StochasticOscillator(
            self.data['high'], self.data['low'], self.data['close'],
            window=14, smooth_window=3
        )
        self.data['stoch_k'] = stoch.stoch()
        self.data['stoch_d'] = stoch.stoch_signal()
        
        # MACD for momentum confirmation
        macd = ta.trend.MACD(self.data['close'])
        self.data['macd'] = macd.macd()
        self.data['macd_signal'] = macd.macd_signal()
        self.data['macd_hist'] = macd.macd_diff()
        
        # Volume analysis (if available)
        if 'volume' in self.data.columns:
            self.data['volume_sma'] = self.data['volume'].rolling(20).mean()
            self.data['volume_ratio'] = self.data['volume'] / self.data['volume_sma']
        else:
            self.data['volume_ratio'] = 1.0
        
        # Price action patterns
        self.data['body'] = self.data['close'] - self.data['open']
        self.data['upper_wick'] = self.data['high'] - self.data[['open', 'close']].max(axis=1)
        self.data['lower_wick'] = self.data[['open', 'close']].min(axis=1) - self.data['low']
        self.data['range'] = self.data['high'] - self.data['low']
        
        # Bullish/bearish candles
        self.data['bullish_candle'] = self.data['close'] > self.data['open']
        self.data['bearish_candle'] = self.data['close'] < self.data['open']
        
        # Hammer/shooting star patterns
        self.data['hammer'] = (
            (self.data['lower_wick'] > 2 * abs(self.data['body'])) &
            (self.data['upper_wick'] < abs(self.data['body']) * 0.5) &
            (self.data['bullish_candle'])
        )
        self.data['shooting_star'] = (
            (self.data['upper_wick'] > 2 * abs(self.data['body'])) &
            (self.data['lower_wick'] < abs(self.data['body']) * 0.5) &
            (self.data['bearish_candle'])
        )
        
        # Engulfing patterns
        self.data['bullish_engulfing'] = (
            (self.data['bearish_candle'].shift(1)) &
            (self.data['bullish_candle']) &
            (self.data['open'] < self.data['close'].shift(1)) &
            (self.data['close'] > self.data['open'].shift(1))
        )
        self.data['bearish_engulfing'] = (
            (self.data['bullish_candle'].shift(1)) &
            (self.data['bearish_candle']) &
            (self.data['open'] > self.data['close'].shift(1)) &
            (self.data['close'] < self.data['open'].shift(1))
        )
        
    def _is_pullback_to_support(self, idx: int) -> bool:
        """Check if price is pulling back to support in uptrend."""
        if idx < 20:
            return False
        
        close = self.data['close'].iloc[idx]
        ema_20 = self.data['ema_20'].iloc[idx]
        ema_50 = self.data['ema_50'].iloc[idx]
        stoch_k = self.data['stoch_k'].iloc[idx]
        
        # Price near EMA 20 or 50 in uptrend
        near_ema20 = abs(close - ema_20) / close < 0.01  # Within 1%
        near_ema50 = abs(close - ema_50) / close < 0.015  # Within 1.5%
        
        # Oversold on stochastic
        stoch_oversold = stoch_k < 30
        
        return (near_ema20 or near_ema50) and stoch_oversold
    
    def _is_pullback_to_resistance(self, idx: int) -> bool:
        """Check if price is pulling back to resistance in downtrend."""
        if idx < 20:
            return False
        
        close = self.data['close'].iloc[idx]
        ema_20 = self.data['ema_20'].iloc[idx]
        ema_50 = self.data['ema_50'].iloc[idx]
        stoch_k = self.data['stoch_k'].iloc[idx]
        
        # Price near EMA 20 or 50 in downtrend
        near_ema20 = abs(close - ema_20) / close < 0.01
        near_ema50 = abs(close - ema_50) / close < 0.015
        
        # Overbought on stochastic
        stoch_overbought = stoch_k > 70
        
        return (near_ema20 or near_ema50) and stoch_overbought
    
    def _get_entry_signal(self, idx: int) -> Optional[TradeSetup]:
        """
        Analyze current bar for entry signal.
        
        Entry criteria:
        1. Strong trend (ADX > 25)
        2. Pullback to key level (EMA or S/R)
        3. Reversal candlestick pattern
        4. Momentum confirmation (MACD, RSI)
        """
        if idx < 200:
            return None
        
        # Get market regime
        regime = self.regime_detector.get_regime(idx)
        trend_dir = self.regime_detector.get_trend_direction(idx)
        
        # Only trade in strong trends
        if 'strong' not in regime:
            return None
        
        close = self.data['close'].iloc[idx]
        high = self.data['high'].iloc[idx]
        low = self.data['low'].iloc[idx]
        atr = self.data['atr'].iloc[idx]
        rsi = self.data['rsi'].iloc[idx]
        macd_hist = self.data['macd_hist'].iloc[idx]
        
        # Long setup in uptrend
        if trend_dir == 1:
            # Check for pullback
            if not self._is_pullback_to_support(idx):
                return None
            
            # Check for bullish reversal pattern
            bullish_pattern = (
                self.data['hammer'].iloc[idx] or 
                self.data['bullish_engulfing'].iloc[idx]
            )
            
            # Momentum confirmation
            rsi_ok = 30 < rsi < 60  # Not overbought
            macd_turning = macd_hist > self.data['macd_hist'].iloc[idx-1]  # MACD improving
            
            if bullish_pattern and rsi_ok and macd_turning:
                # Calculate stop and targets
                stop_loss = low - atr * 0.5
                risk = close - stop_loss
                
                take_profit_1 = close + risk * 2  # 2:1 R:R
                take_profit_2 = close + risk * 3  # 3:1 R:R
                
                # Confidence based on confirmations
                confidence = 0.5
                if self.data['bullish_engulfing'].iloc[idx]:
                    confidence += 0.15
                if rsi < 40:
                    confidence += 0.1
                if macd_hist > 0:
                    confidence += 0.1
                
                return TradeSetup(
                    direction=1,
                    entry_price=close,
                    stop_loss=stop_loss,
                    take_profit_1=take_profit_1,
                    take_profit_2=take_profit_2,
                    position_size=0,  # Calculated later
                    confidence=min(confidence, 0.9),
                    reason=f"Long: {regime}, pullback + reversal pattern"
                )
        
        # Short setup in downtrend
        elif trend_dir == -1:
            # Check for pullback
            if not self._is_pullback_to_resistance(idx):
                return None
            
            # Check for bearish reversal pattern
            bearish_pattern = (
                self.data['shooting_star'].iloc[idx] or
                self.data['bearish_engulfing'].iloc[idx]
            )
            
            # Momentum confirmation
            rsi_ok = 40 < rsi < 70  # Not oversold
            macd_turning = macd_hist < self.data['macd_hist'].iloc[idx-1]  # MACD weakening
            
            if bearish_pattern and rsi_ok and macd_turning:
                # Calculate stop and targets
                stop_loss = high + atr * 0.5
                risk = stop_loss - close
                
                take_profit_1 = close - risk * 2
                take_profit_2 = close - risk * 3
                
                # Confidence
                confidence = 0.5
                if self.data['bearish_engulfing'].iloc[idx]:
                    confidence += 0.15
                if rsi > 60:
                    confidence += 0.1
                if macd_hist < 0:
                    confidence += 0.1
                
                return TradeSetup(
                    direction=-1,
                    entry_price=close,
                    stop_loss=stop_loss,
                    take_profit_1=take_profit_1,
                    take_profit_2=take_profit_2,
                    position_size=0,
                    confidence=min(confidence, 0.9),
                    reason=f"Short: {regime}, pullback + reversal pattern"
                )
        
        return None
    
    def _calculate_position_size(self, setup: TradeSetup, capital: float) -> float:
        """Calculate position size based on risk."""
        risk_amount = capital * self.risk_per_trade * setup.confidence
        risk_per_unit = abs(setup.entry_price - setup.stop_loss)
        
        if risk_per_unit <= 0:
            return 0
        
        position_size = risk_amount / risk_per_unit
        
        # Cap at maximum (10% of capital at entry price)
        max_size = (capital * 0.1) / setup.entry_price
        return min(position_size, max_size)
    
    def generate_signals(self) -> pd.Series:
        """Generate trading signals."""
        signals = pd.Series(index=self.data.index, data=0)
        
        for i in range(200, len(self.data)):
            setup = self._get_entry_signal(i)
            if setup is not None:
                signals.iloc[i] = setup.direction
        
        return signals
    
    def backtest(self) -> Dict[str, Any]:
        """Run backtest with proper trade management."""
        capital = self.initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit_1 = 0
        take_profit_2 = 0
        partial_exit_done = False
        highest_since_entry = 0
        lowest_since_entry = float('inf')
        trailing_stop = 0
        
        self.trades = []
        current_trade = None
        
        for i in range(len(self.data)):
            if i < 200:
                self.capital.iloc[i] = capital
                self.positions.iloc[i] = 0
                continue
            
            close = self.data['close'].iloc[i]
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            atr = self.data['atr'].iloc[i] if not pd.isna(self.data['atr'].iloc[i]) else close * 0.01
            
            # Manage existing position
            if position != 0:
                # Update trailing values
                if position > 0:
                    highest_since_entry = max(highest_since_entry, high)
                    
                    # Move stop to breakeven after 1R profit
                    if highest_since_entry >= entry_price + (entry_price - stop_loss):
                        trailing_stop = max(trailing_stop, entry_price)
                    
                    # Trail stop at 1.5 ATR below highest
                    new_trail = highest_since_entry - atr * 1.5
                    if new_trail > trailing_stop:
                        trailing_stop = new_trail
                    
                    # Check stop loss
                    if low <= max(stop_loss, trailing_stop):
                        exit_price = max(stop_loss, trailing_stop)
                        pnl = (exit_price - entry_price) * position
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = exit_price
                            current_trade['exit_reason'] = 'trailing_stop' if trailing_stop > stop_loss else 'stop_loss'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
                    
                    # Check first take profit
                    elif high >= take_profit_1 and not partial_exit_done:
                        # Exit half position
                        exit_size = position * 0.5
                        pnl = (take_profit_1 - entry_price) * exit_size
                        capital += pnl
                        position -= exit_size
                        partial_exit_done = True
                        # Move stop to breakeven
                        trailing_stop = entry_price
                    
                    # Check second take profit
                    elif high >= take_profit_2:
                        pnl = (take_profit_2 - entry_price) * position
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = take_profit_2
                            current_trade['exit_reason'] = 'take_profit'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
                
                else:  # Short position
                    lowest_since_entry = min(lowest_since_entry, low)
                    
                    # Move stop to breakeven after 1R profit
                    if lowest_since_entry <= entry_price - (stop_loss - entry_price):
                        trailing_stop = min(trailing_stop if trailing_stop > 0 else float('inf'), entry_price)
                    
                    # Trail stop at 1.5 ATR above lowest
                    new_trail = lowest_since_entry + atr * 1.5
                    if trailing_stop == 0 or new_trail < trailing_stop:
                        if new_trail < stop_loss:
                            trailing_stop = new_trail
                    
                    # Check stop loss
                    actual_stop = min(stop_loss, trailing_stop) if trailing_stop > 0 else stop_loss
                    if high >= actual_stop:
                        exit_price = actual_stop
                        pnl = (entry_price - exit_price) * abs(position)
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = exit_price
                            current_trade['exit_reason'] = 'trailing_stop' if trailing_stop > 0 and trailing_stop < stop_loss else 'stop_loss'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
                    
                    # Check take profits
                    elif low <= take_profit_1 and not partial_exit_done:
                        exit_size = abs(position) * 0.5
                        pnl = (entry_price - take_profit_1) * exit_size
                        capital += pnl
                        position += exit_size  # Reduce short
                        partial_exit_done = True
                        trailing_stop = entry_price
                    
                    elif low <= take_profit_2:
                        pnl = (entry_price - take_profit_2) * abs(position)
                        capital += pnl
                        
                        if current_trade:
                            current_trade['exit_price'] = take_profit_2
                            current_trade['exit_reason'] = 'take_profit'
                            current_trade['pnl'] = pnl
                            self.trades.append(current_trade)
                        
                        position = 0
                        current_trade = None
            
            # Check for new entry
            if position == 0:
                setup = self._get_entry_signal(i)
                
                if setup is not None:
                    position_size = self._calculate_position_size(setup, capital)
                    
                    if position_size > 0:
                        position = position_size if setup.direction > 0 else -position_size
                        entry_price = setup.entry_price
                        stop_loss = setup.stop_loss
                        take_profit_1 = setup.take_profit_1
                        take_profit_2 = setup.take_profit_2
                        partial_exit_done = False
                        trailing_stop = 0
                        highest_since_entry = close
                        lowest_since_entry = close
                        
                        current_trade = {
                            'entry_date': self.data.index[i],
                            'entry_price': entry_price,
                            'side': 'long' if setup.direction > 0 else 'short',
                            'size': abs(position),
                            'stop_loss': stop_loss,
                            'take_profit': take_profit_2,
                            'confidence': setup.confidence,
                            'reason': setup.reason
                        }
            
            self.positions.iloc[i] = position
            self.capital.iloc[i] = capital + (close - entry_price) * position if position != 0 else capital
        
        # Close any remaining position
        if position != 0:
            close = self.data['close'].iloc[-1]
            if position > 0:
                pnl = (close - entry_price) * position
            else:
                pnl = (entry_price - close) * abs(position)
            capital += pnl
            
            if current_trade:
                current_trade['exit_price'] = close
                current_trade['exit_reason'] = 'end_of_data'
                current_trade['pnl'] = pnl
                self.trades.append(current_trade)
        
        return self._calculate_metrics(capital)
    
    def _calculate_metrics(self, final_capital: float) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        if not self.trades:
            return {
                'total_return': 0,
                'total_return_pct': 0,
                'total_trades': 0,
                'win_rate': 0,
                'win_rate_pct': 0,
                'profit_factor': 0,
                'final_capital': final_capital,
                'initial_capital': self.initial_capital,
                'net_profit': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_drawdown_pct': 0,
                'sharpe_ratio': 0,
                'risk_reward_ratio': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'gross_profit': 0,
                'gross_loss': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Win/loss
        winners = trades_df[trades_df['pnl'] > 0]
        losers = trades_df[trades_df['pnl'] < 0]
        
        win_rate = len(winners) / len(trades_df)
        
        # Averages
        avg_win = winners['pnl'].mean() if len(winners) > 0 else 0
        avg_loss = abs(losers['pnl'].mean()) if len(losers) > 0 else 0
        
        # Profit factor
        gross_profit = winners['pnl'].sum() if len(winners) > 0 else 0
        gross_loss = abs(losers['pnl'].sum()) if len(losers) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Risk/reward
        risk_reward = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        # Drawdown
        equity = self.capital.dropna()
        rolling_max = equity.expanding().max()
        drawdowns = (equity - rolling_max) / rolling_max
        max_drawdown = abs(drawdowns.min()) if len(drawdowns) > 0 else 0
        
        # Sharpe
        returns = equity.pct_change().dropna()
        sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'net_profit': final_capital - self.initial_capital,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': len(self.trades),
            'winning_trades': len(winners),
            'losing_trades': len(losers),
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'risk_reward_ratio': risk_reward,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_drawdown * 100,
            'sharpe_ratio': sharpe,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }
