"""
Realistic Backtester with transaction costs, slippage, and proper simulation.

This module provides honest backtesting that accounts for:
1. Spread costs (bid-ask spread)
2. Commission fees
3. Slippage
4. Minimum position sizes
5. Margin requirements
6. Realistic order execution
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
    entry_date: datetime
    exit_date: datetime
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    position_size: float
    gross_pnl: float
    spread_cost: float
    commission: float
    slippage: float
    net_pnl: float
    exit_reason: str


class RealisticBacktester:
    """
    Backtester that simulates real trading conditions.
    """
    
    def __init__(self,
                 # Cost parameters (realistic for XAU/USD)
                 spread_pips: float = 30,  # 30 pips = $0.30 spread
                 commission_per_lot: float = 7.0,  # $7 per standard lot
                 slippage_pips: float = 5,  # 5 pips average slippage
                 # Account parameters
                 initial_capital: float = 10000,
                 leverage: int = 100,  # 100:1 leverage
                 min_lot_size: float = 0.01,  # Micro lot
                 lot_size_units: float = 100,  # 1 lot = 100 oz for gold
                 # Risk parameters
                 margin_call_level: float = 0.50,  # 50% margin level
                 stop_out_level: float = 0.20):  # 20% stop out
        """
        Initialize realistic backtester.
        
        Args:
            spread_pips: Spread in pips (1 pip = $0.01 for gold)
            commission_per_lot: Commission per standard lot roundtrip
            slippage_pips: Average slippage in pips
            initial_capital: Starting account balance
            leverage: Account leverage
            min_lot_size: Minimum tradeable lot size
            lot_size_units: Units per lot (100 oz for gold)
            margin_call_level: Margin level for margin call
            stop_out_level: Margin level for stop out
        """
        self.spread_pips = spread_pips
        self.spread_dollars = spread_pips * 0.01  # Convert pips to dollars
        self.commission_per_lot = commission_per_lot
        self.slippage_pips = slippage_pips
        self.slippage_dollars = slippage_pips * 0.01
        
        self.initial_capital = initial_capital
        self.leverage = leverage
        self.min_lot_size = min_lot_size
        self.lot_size_units = lot_size_units
        self.margin_call_level = margin_call_level
        self.stop_out_level = stop_out_level
        
        self.trades: List[TradeResult] = []
        self.equity_curve: List[float] = []
    
    def calculate_required_margin(self, position_size: float, price: float) -> float:
        """Calculate required margin for a position."""
        notional_value = abs(position_size) * price
        return notional_value / self.leverage
    
    def calculate_lot_size(self, units: float) -> float:
        """Convert units to lot size."""
        return units / self.lot_size_units
    
    def calculate_transaction_costs(self, position_size: float, 
                                   is_entry: bool = True) -> Dict[str, float]:
        """
        Calculate all transaction costs for a trade.
        
        Returns:
            Dictionary with spread_cost, commission, slippage
        """
        lot_size = self.calculate_lot_size(abs(position_size))
        
        # Spread cost (paid on entry)
        spread_cost = abs(position_size) * self.spread_dollars if is_entry else 0
        
        # Commission (paid on entry and exit)
        commission = lot_size * (self.commission_per_lot / 2)  # Half on each side
        
        # Slippage (random, but on average this amount)
        slippage = abs(position_size) * self.slippage_dollars * np.random.uniform(0.5, 1.5)
        
        return {
            'spread_cost': spread_cost,
            'commission': commission,
            'slippage': slippage,
            'total': spread_cost + commission + slippage
        }
    
    def run_backtest(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run realistic backtest on a strategy.
        
        Args:
            strategy: Strategy instance with generate_signals method
            data: OHLCV DataFrame
            
        Returns:
            Dictionary with performance metrics and trade log
        """
        try:
            signals = strategy.generate_signals()
            
            capital = self.initial_capital
            position = 0
            entry_price = 0
            entry_date = None
            stop_loss = 0
            take_profit = 0
            
            self.equity_curve = [capital]
            self.trades = []
            
            for i in range(1, len(data)):
                current_price = data['close'].iloc[i]
                high_price = data['high'].iloc[i]
                low_price = data['low'].iloc[i]
                current_date = data.index[i]
                signal = signals.iloc[i]
                
                # Get ATR for stop/take profit
                atr = data['atr'].iloc[i] if 'atr' in data.columns else current_price * 0.01
                
                # Check margin level
                if position != 0:
                    unrealized_pnl = (current_price - entry_price) * position
                    equity = capital + unrealized_pnl
                    margin_used = self.calculate_required_margin(position, current_price)
                    margin_level = equity / margin_used if margin_used > 0 else float('inf')
                    
                    # Stop out check
                    if margin_level < self.stop_out_level:
                        # Forced liquidation
                        exit_costs = self.calculate_transaction_costs(position, is_entry=False)
                        gross_pnl = unrealized_pnl
                        net_pnl = gross_pnl - exit_costs['total']
                        capital += net_pnl
                        
                        self.trades.append(TradeResult(
                            entry_date=entry_date,
                            exit_date=current_date,
                            side='long' if position > 0 else 'short',
                            entry_price=entry_price,
                            exit_price=current_price,
                            position_size=abs(position),
                            gross_pnl=gross_pnl,
                            spread_cost=0,
                            commission=exit_costs['commission'],
                            slippage=exit_costs['slippage'],
                            net_pnl=net_pnl,
                            exit_reason='stop_out'
                        ))
                        
                        position = 0
                        logger.warning(f"Stop out triggered at {current_date}")
                        continue
                
                # Check stop-loss and take-profit
                if position > 0:  # Long position
                    if low_price <= stop_loss:
                        # Stop loss hit
                        exit_price = stop_loss
                        exit_costs = self.calculate_transaction_costs(position, is_entry=False)
                        gross_pnl = (exit_price - entry_price) * position
                        net_pnl = gross_pnl - exit_costs['total']
                        capital += net_pnl
                        
                        self.trades.append(TradeResult(
                            entry_date=entry_date,
                            exit_date=current_date,
                            side='long',
                            entry_price=entry_price,
                            exit_price=exit_price,
                            position_size=position,
                            gross_pnl=gross_pnl,
                            spread_cost=0,
                            commission=exit_costs['commission'],
                            slippage=exit_costs['slippage'],
                            net_pnl=net_pnl,
                            exit_reason='stop_loss'
                        ))
                        position = 0
                    
                    elif high_price >= take_profit:
                        # Take profit hit
                        exit_price = take_profit
                        exit_costs = self.calculate_transaction_costs(position, is_entry=False)
                        gross_pnl = (exit_price - entry_price) * position
                        net_pnl = gross_pnl - exit_costs['total']
                        capital += net_pnl
                        
                        self.trades.append(TradeResult(
                            entry_date=entry_date,
                            exit_date=current_date,
                            side='long',
                            entry_price=entry_price,
                            exit_price=exit_price,
                            position_size=position,
                            gross_pnl=gross_pnl,
                            spread_cost=0,
                            commission=exit_costs['commission'],
                            slippage=exit_costs['slippage'],
                            net_pnl=net_pnl,
                            exit_reason='take_profit'
                        ))
                        position = 0
                
                elif position < 0:  # Short position
                    if high_price >= stop_loss:
                        # Stop loss hit
                        exit_price = stop_loss
                        exit_costs = self.calculate_transaction_costs(abs(position), is_entry=False)
                        gross_pnl = (entry_price - exit_price) * abs(position)
                        net_pnl = gross_pnl - exit_costs['total']
                        capital += net_pnl
                        
                        self.trades.append(TradeResult(
                            entry_date=entry_date,
                            exit_date=current_date,
                            side='short',
                            entry_price=entry_price,
                            exit_price=exit_price,
                            position_size=abs(position),
                            gross_pnl=gross_pnl,
                            spread_cost=0,
                            commission=exit_costs['commission'],
                            slippage=exit_costs['slippage'],
                            net_pnl=net_pnl,
                            exit_reason='stop_loss'
                        ))
                        position = 0
                    
                    elif low_price <= take_profit:
                        # Take profit hit
                        exit_price = take_profit
                        exit_costs = self.calculate_transaction_costs(abs(position), is_entry=False)
                        gross_pnl = (entry_price - exit_price) * abs(position)
                        net_pnl = gross_pnl - exit_costs['total']
                        capital += net_pnl
                        
                        self.trades.append(TradeResult(
                            entry_date=entry_date,
                            exit_date=current_date,
                            side='short',
                            entry_price=entry_price,
                            exit_price=exit_price,
                            position_size=abs(position),
                            gross_pnl=gross_pnl,
                            spread_cost=0,
                            commission=exit_costs['commission'],
                            slippage=exit_costs['slippage'],
                            net_pnl=net_pnl,
                            exit_reason='take_profit'
                        ))
                        position = 0
                
                # Process new signals
                if signal != 0 and position == 0:
                    # Calculate position size based on risk
                    risk_amount = capital * 0.02  # 2% risk
                    stop_distance = atr * 1.5
                    
                    # Position size in units
                    raw_size = risk_amount / stop_distance
                    
                    # Check minimum lot size
                    lot_size = self.calculate_lot_size(raw_size)
                    if lot_size < self.min_lot_size:
                        logger.debug(f"Position too small: {lot_size:.4f} lots < {self.min_lot_size}")
                        self.equity_curve.append(capital)
                        continue
                    
                    # Round to valid lot size
                    lot_size = max(self.min_lot_size, round(lot_size / self.min_lot_size) * self.min_lot_size)
                    position_size = lot_size * self.lot_size_units
                    
                    # Check margin
                    required_margin = self.calculate_required_margin(position_size, current_price)
                    if required_margin > capital * 0.9:  # Max 90% margin usage
                        logger.debug(f"Insufficient margin: need ${required_margin:.2f}, have ${capital:.2f}")
                        self.equity_curve.append(capital)
                        continue
                    
                    # Entry costs
                    entry_costs = self.calculate_transaction_costs(position_size, is_entry=True)
                    
                    # Apply slippage to entry
                    slippage_adj = self.slippage_dollars * (1 if signal > 0 else -1)
                    actual_entry = current_price + slippage_adj
                    
                    # Set position
                    position = position_size if signal > 0 else -position_size
                    entry_price = actual_entry
                    entry_date = current_date
                    
                    # Set stops
                    if signal > 0:
                        stop_loss = entry_price - (atr * 1.5)
                        take_profit = entry_price + (atr * 3.0)
                    else:
                        stop_loss = entry_price + (atr * 1.5)
                        take_profit = entry_price - (atr * 3.0)
                    
                    # Deduct entry costs
                    capital -= entry_costs['total']
                
                self.equity_curve.append(capital + (current_price - entry_price) * position if position != 0 else capital)
            
            # Close any remaining position
            if position != 0:
                exit_price = data['close'].iloc[-1]
                exit_costs = self.calculate_transaction_costs(abs(position), is_entry=False)
                if position > 0:
                    gross_pnl = (exit_price - entry_price) * position
                else:
                    gross_pnl = (entry_price - exit_price) * abs(position)
                net_pnl = gross_pnl - exit_costs['total']
                capital += net_pnl
                
                self.trades.append(TradeResult(
                    entry_date=entry_date,
                    exit_date=data.index[-1],
                    side='long' if position > 0 else 'short',
                    entry_price=entry_price,
                    exit_price=exit_price,
                    position_size=abs(position),
                    gross_pnl=gross_pnl,
                    spread_cost=0,
                    commission=exit_costs['commission'],
                    slippage=exit_costs['slippage'],
                    net_pnl=net_pnl,
                    exit_reason='end_of_data'
                ))
            
            return self._calculate_metrics(capital)
            
        except Exception as e:
            logger.error(f"Error in realistic backtest: {str(e)}")
            raise
    
    def _calculate_metrics(self, final_capital: float) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        
        if not self.trades:
            return {
                'total_return': 0,
                'total_return_pct': 0,
                'total_trades': 0,
                'final_capital': final_capital,
                'net_profit': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'win_rate_pct': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'risk_reward_ratio': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'volatility': 0,
                'total_costs': 0,
                'total_spread_cost': 0,
                'total_commission': 0,
                'total_slippage': 0,
                'cost_pct_of_capital': 0,
                'initial_capital': self.initial_capital,
                'exits_by_stop_loss': 0,
                'exits_by_take_profit': 0,
                'gross_profit': 0,
                'gross_loss': 0,
                'message': 'No trades executed - positions too small or no signals'
            }
        
        # Convert trades to DataFrame
        trades_df = pd.DataFrame([vars(t) for t in self.trades])
        
        # Basic metrics
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Trade statistics
        winning_trades = trades_df[trades_df['net_pnl'] > 0]
        losing_trades = trades_df[trades_df['net_pnl'] < 0]
        
        win_rate = len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0
        
        # Profit factor
        gross_profit = winning_trades['net_pnl'].sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average metrics
        avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = abs(losing_trades['net_pnl'].mean()) if len(losing_trades) > 0 else 0
        
        # Risk/reward
        risk_reward = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        # Equity curve analysis
        equity_series = pd.Series(self.equity_curve)
        returns = equity_series.pct_change().dropna()
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        excess_returns = returns.mean() * 252 - 0.02
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
        
        # Max drawdown
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # Cost analysis
        total_spread_cost = trades_df['spread_cost'].sum()
        total_commission = trades_df['commission'].sum()
        total_slippage = trades_df['slippage'].sum()
        total_costs = total_spread_cost + total_commission + total_slippage
        
        # Exit reason breakdown
        exit_reasons = trades_df['exit_reason'].value_counts().to_dict()
        
        return {
            # Returns
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'net_profit': final_capital - self.initial_capital,
            
            # Trade stats
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            
            # Profit metrics
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'risk_reward_ratio': risk_reward,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            
            # Risk metrics
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'volatility': volatility,
            
            # Cost breakdown
            'total_costs': total_costs,
            'total_spread_cost': total_spread_cost,
            'total_commission': total_commission,
            'total_slippage': total_slippage,
            'cost_pct_of_capital': (total_costs / self.initial_capital) * 100,
            
            # Exit analysis
            'exits_by_stop_loss': exit_reasons.get('stop_loss', 0),
            'exits_by_take_profit': exit_reasons.get('take_profit', 0),
            'exits_by_signal': exit_reasons.get('signal_reversal', 0),
            'exits_by_stop_out': exit_reasons.get('stop_out', 0),
        }
    
    def print_report(self, metrics: Dict[str, Any]):
        """Print a formatted performance report."""
        print("\n" + "=" * 70)
        print("REALISTIC BACKTEST REPORT")
        print("=" * 70)
        
        print(f"\n{'CAPITAL':=^70}")
        print(f"  Initial Capital:     ${metrics['initial_capital']:>12,.2f}")
        print(f"  Final Capital:       ${metrics['final_capital']:>12,.2f}")
        print(f"  Net Profit/Loss:     ${metrics['net_profit']:>12,.2f}")
        print(f"  Total Return:        {metrics['total_return_pct']:>12.2f}%")
        
        print(f"\n{'TRADE STATISTICS':=^70}")
        print(f"  Total Trades:        {metrics['total_trades']:>12}")
        print(f"  Winning Trades:      {metrics['winning_trades']:>12}")
        print(f"  Losing Trades:       {metrics['losing_trades']:>12}")
        print(f"  Win Rate:            {metrics['win_rate_pct']:>12.2f}%")
        
        print(f"\n{'PROFITABILITY':=^70}")
        print(f"  Profit Factor:       {metrics['profit_factor']:>12.2f}")
        print(f"  Avg Win:             ${metrics['avg_win']:>12,.2f}")
        print(f"  Avg Loss:            ${metrics['avg_loss']:>12,.2f}")
        print(f"  Risk/Reward:         {metrics['risk_reward_ratio']:>12.2f}")
        
        print(f"\n{'RISK METRICS':=^70}")
        print(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:>12.2f}")
        print(f"  Max Drawdown:        {metrics['max_drawdown_pct']:>12.2f}%")
        print(f"  Volatility (Ann.):   {metrics['volatility']*100:>12.2f}%")
        
        print(f"\n{'TRANSACTION COSTS':=^70}")
        print(f"  Total Costs:         ${metrics['total_costs']:>12,.2f}")
        print(f"  Spread Costs:        ${metrics['total_spread_cost']:>12,.2f}")
        print(f"  Commissions:         ${metrics['total_commission']:>12,.2f}")
        print(f"  Slippage:            ${metrics['total_slippage']:>12,.2f}")
        print(f"  Costs (% of Cap):    {metrics['cost_pct_of_capital']:>12.2f}%")
        
        print(f"\n{'EXIT ANALYSIS':=^70}")
        print(f"  By Stop Loss:        {metrics['exits_by_stop_loss']:>12}")
        print(f"  By Take Profit:      {metrics['exits_by_take_profit']:>12}")
        print(f"  By Signal:           {metrics.get('exits_by_signal', 0):>12}")
        print(f"  By Stop Out:         {metrics.get('exits_by_stop_out', 0):>12}")
        
        print("\n" + "=" * 70)
