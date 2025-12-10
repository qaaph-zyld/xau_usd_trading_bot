import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PositionSize:
    units: float
    risk_amount: float
    stop_loss_price: float
    take_profit_price: Optional[float] = None
    entry_price: Optional[float] = None

class PositionSizer:
    def __init__(self, 
                 max_risk_per_trade: float = 0.02,
                 max_position_size: float = 0.1,
                 atr_multiplier: float = 2.0):
        """
        Position Sizer for risk management
        
        Args:
            max_risk_per_trade: Maximum risk per trade as fraction of capital
            max_position_size: Maximum position size as fraction of capital
            atr_multiplier: Multiplier for ATR to set stop loss
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_position_size = max_position_size
        self.atr_multiplier = atr_multiplier
        
    def calculate_position_size(self,
                              capital: float,
                              entry_price: float,
                              stop_loss_price: float,
                              take_profit_price: Optional[float] = None) -> PositionSize:
        """
        Calculate position size based on risk parameters
        
        Args:
            capital: Current capital
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price (optional)
            
        Returns:
            PositionSize object with position details
        """
        try:
            # Calculate risk amount
            risk_amount = capital * self.max_risk_per_trade
            
            # Calculate position size based on stop loss
            price_risk = abs(entry_price - stop_loss_price)
            units = risk_amount / price_risk
            
            # Check against maximum position size
            max_units = (capital * self.max_position_size) / entry_price
            units = min(units, max_units)
            
            return PositionSize(
                units=units,
                risk_amount=risk_amount,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                entry_price=entry_price
            )
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            raise
            
    def calculate_stop_loss(self,
                          entry_price: float,
                          atr: float,
                          side: str = 'long') -> float:
        """
        Calculate stop loss price based on ATR
        
        Args:
            entry_price: Entry price for the trade
            atr: Average True Range value
            side: Trade direction ('long' or 'short')
            
        Returns:
            Stop loss price
        """
        stop_distance = atr * self.atr_multiplier
        
        if side.lower() == 'long':
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
            
    def calculate_take_profit(self,
                            entry_price: float,
                            stop_loss_price: float,
                            risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit price based on risk-reward ratio
        
        Args:
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            risk_reward_ratio: Desired risk-reward ratio
            
        Returns:
            Take profit price
        """
        risk_distance = abs(entry_price - stop_loss_price)
        reward_distance = risk_distance * risk_reward_ratio
        
        if entry_price > stop_loss_price:  # Long position
            return entry_price + reward_distance
        else:  # Short position
            return entry_price - reward_distance
            
    def adjust_for_correlation(self,
                             position_size: float,
                             correlation_matrix: pd.DataFrame,
                             current_positions: Dict[str, float]) -> float:
        """
        Adjust position size based on correlation with existing positions
        
        Args:
            position_size: Initial position size
            correlation_matrix: Correlation matrix of assets
            current_positions: Dictionary of current positions
            
        Returns:
            Adjusted position size
        """
        try:
            if not current_positions:
                return position_size
                
            # Calculate total correlation impact
            # Get the new asset (first column not in current positions)
            new_asset = [c for c in correlation_matrix.columns if c not in current_positions]
            if not new_asset:
                return position_size
            new_asset = new_asset[0]
            
            total_correlation = sum(
                abs(correlation_matrix.loc[new_asset, asset]) * abs(size)
                for asset, size in current_positions.items()
                if asset in correlation_matrix.columns and new_asset in correlation_matrix.index
            )
            
            # Adjust position size based on correlation
            correlation_factor = 1 / (1 + total_correlation)
            adjusted_size = position_size * correlation_factor
            
            return adjusted_size
            
        except Exception as e:
            logger.error(f"Error adjusting for correlation: {str(e)}")
            return position_size  # Return original size if adjustment fails
            
    def calculate_portfolio_risk(self,
                               positions: Dict[str, PositionSize],
                               correlation_matrix: pd.DataFrame) -> float:
        """
        Calculate total portfolio risk considering correlations
        
        Args:
            positions: Dictionary of current positions
            correlation_matrix: Correlation matrix of assets
            
        Returns:
            Total portfolio risk as percentage of capital
        """
        try:
            if not positions:
                return 0.0
                
            # Create risk vector
            risk_vector = np.array([pos.risk_amount for pos in positions.values()])
            
            # Create correlation matrix for current positions
            assets = list(positions.keys())
            corr_matrix = correlation_matrix.loc[assets, assets].values
            
            # Calculate portfolio risk
            portfolio_risk = np.sqrt(
                risk_vector.T @ corr_matrix @ risk_vector
            )
            
            return portfolio_risk
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {str(e)}")
            return sum(pos.risk_amount for pos in positions.values())  # Fallback to sum of individual risks
