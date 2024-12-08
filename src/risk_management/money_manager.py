import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class AllocationLimits:
    max_single_position: float
    max_daily_risk: float
    max_sector_exposure: float
    max_drawdown: float

class MoneyManager:
    def __init__(self,
                 initial_capital: float,
                 allocation_limits: AllocationLimits,
                 risk_free_rate: float = 0.02):
        """
        Money Manager for capital allocation and risk management
        
        Args:
            initial_capital: Initial trading capital
            allocation_limits: AllocationLimits object with exposure limits
            risk_free_rate: Annual risk-free rate
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.limits = allocation_limits
        self.risk_free_rate = risk_free_rate
        
        self.daily_risk_used = 0.0
        self.positions: Dict[str, float] = {}
        self.sector_exposure: Dict[str, float] = {}
        self.last_reset = datetime.now().date()
        
    def reset_daily_risk(self):
        """Reset daily risk if new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset:
            self.daily_risk_used = 0.0
            self.last_reset = current_date
    
    def can_allocate(self,
                    symbol: str,
                    risk_amount: float,
                    sector: Optional[str] = None) -> tuple[bool, str]:
        """
        Check if capital can be allocated to a new position
        
        Args:
            symbol: Trading symbol
            risk_amount: Amount of risk for the trade
            sector: Market sector (optional)
            
        Returns:
            Tuple of (can_allocate, reason)
        """
        try:
            self.reset_daily_risk()
            
            # Check position size limit
            position_size = risk_amount / self.current_capital
            if position_size > self.limits.max_single_position:
                return False, "Position size exceeds limit"
            
            # Check daily risk limit
            if self.daily_risk_used + risk_amount > (self.current_capital * self.limits.max_daily_risk):
                return False, "Daily risk limit exceeded"
            
            # Check sector exposure
            if sector:
                current_sector_exposure = self.sector_exposure.get(sector, 0.0)
                new_sector_exposure = current_sector_exposure + position_size
                if new_sector_exposure > self.limits.max_sector_exposure:
                    return False, f"Sector exposure limit exceeded for {sector}"
            
            # Check drawdown limit
            current_drawdown = (self.initial_capital - self.current_capital) / self.initial_capital
            if current_drawdown > self.limits.max_drawdown:
                return False, "Maximum drawdown reached"
            
            return True, "Allocation allowed"
            
        except Exception as e:
            logger.error(f"Error checking allocation: {str(e)}")
            return False, str(e)
    
    def allocate_capital(self,
                        symbol: str,
                        risk_amount: float,
                        sector: Optional[str] = None) -> Optional[float]:
        """
        Allocate capital to a new position
        
        Args:
            symbol: Trading symbol
            risk_amount: Amount of risk for the trade
            sector: Market sector (optional)
            
        Returns:
            Allocated capital amount or None if allocation not possible
        """
        try:
            can_allocate, reason = self.can_allocate(symbol, risk_amount, sector)
            if not can_allocate:
                logger.warning(f"Cannot allocate capital: {reason}")
                return None
            
            # Calculate position size based on risk
            position_size = risk_amount / self.current_capital
            allocated_amount = self.current_capital * position_size
            
            # Update tracking
            self.positions[symbol] = allocated_amount
            self.daily_risk_used += risk_amount
            if sector:
                self.sector_exposure[sector] = self.sector_exposure.get(sector, 0.0) + position_size
            
            return allocated_amount
            
        except Exception as e:
            logger.error(f"Error allocating capital: {str(e)}")
            return None
    
    def deallocate_capital(self,
                          symbol: str,
                          pnl: float,
                          sector: Optional[str] = None):
        """
        Deallocate capital after closing a position
        
        Args:
            symbol: Trading symbol
            pnl: Profit/Loss from the trade
            sector: Market sector (optional)
        """
        try:
            if symbol not in self.positions:
                logger.warning(f"Position {symbol} not found")
                return
            
            # Update capital
            self.current_capital += pnl
            
            # Update sector exposure
            if sector and sector in self.sector_exposure:
                position_size = self.positions[symbol] / self.current_capital
                self.sector_exposure[sector] -= position_size
                if self.sector_exposure[sector] <= 0:
                    del self.sector_exposure[sector]
            
            # Remove position
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"Error deallocating capital: {str(e)}")
    
    def calculate_optimal_position_size(self,
                                     symbol: str,
                                     volatility: float,
                                     correlation_matrix: Optional[pd.DataFrame] = None) -> float:
        """
        Calculate optimal position size using modern portfolio theory
        
        Args:
            symbol: Trading symbol
            volatility: Asset volatility
            correlation_matrix: Correlation matrix with other positions
            
        Returns:
            Optimal position size as fraction of capital
        """
        try:
            # Base position size using volatility targeting
            target_portfolio_volatility = 0.15  # 15% annual volatility target
            base_position_size = target_portfolio_volatility / (volatility * np.sqrt(252))
            
            # Adjust for correlations if available
            if correlation_matrix is not None and not correlation_matrix.empty:
                portfolio_symbols = list(self.positions.keys())
                if symbol in correlation_matrix.columns and portfolio_symbols:
                    correlations = correlation_matrix.loc[symbol, portfolio_symbols]
                    avg_correlation = correlations.mean()
                    # Reduce position size for high correlations
                    correlation_adjustment = 1 - avg_correlation
                    base_position_size *= correlation_adjustment
            
            # Apply position limits
            return min(base_position_size, self.limits.max_single_position)
            
        except Exception as e:
            logger.error(f"Error calculating optimal position size: {str(e)}")
            return self.limits.max_single_position
    
    def get_allocation_status(self) -> Dict:
        """
        Get current allocation status
        """
        return {
            'current_capital': self.current_capital,
            'daily_risk_used': self.daily_risk_used,
            'open_positions': len(self.positions),
            'sector_exposure': self.sector_exposure,
            'available_capital': self.current_capital - sum(self.positions.values()),
            'drawdown': (self.initial_capital - self.current_capital) / self.initial_capital
        }
