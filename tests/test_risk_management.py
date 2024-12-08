import pytest
import pandas as pd
import numpy as np
from src.risk_management.position_sizer import PositionSizer
from src.risk_management.risk_manager import RiskManager
from src.risk_management.money_manager import MoneyManager, AllocationLimits
from datetime import datetime, timedelta

@pytest.fixture
def sample_data():
    """Create sample price data"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    prices = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    returns = prices.pct_change().dropna()
    return prices, returns

@pytest.fixture
def correlation_matrix():
    """Create sample correlation matrix"""
    symbols = ['XAU/USD', 'EUR/USD', 'GBP/USD']
    data = np.array([[1.0, 0.5, 0.3],
                     [0.5, 1.0, 0.6],
                     [0.3, 0.6, 1.0]])
    return pd.DataFrame(data, index=symbols, columns=symbols)

def test_position_sizer():
    sizer = PositionSizer(max_risk_per_trade=0.02)
    
    # Test position size calculation
    position = sizer.calculate_position_size(
        capital=100000,
        entry_price=1000,
        stop_loss_price=990
    )
    
    assert position.units > 0
    assert position.risk_amount == 2000  # 2% of 100000
    assert position.stop_loss_price == 990
    
    # Test stop loss calculation
    stop_loss = sizer.calculate_stop_loss(
        entry_price=1000,
        atr=5,
        side='long'
    )
    
    assert stop_loss < 1000
    
    # Test take profit calculation
    take_profit = sizer.calculate_take_profit(
        entry_price=1000,
        stop_loss_price=990,
        risk_reward_ratio=2.0
    )
    
    assert take_profit > 1000
    assert take_profit - 1000 == 2 * (1000 - 990)

def test_risk_manager(correlation_matrix):
    manager = RiskManager(
        initial_capital=100000,
        max_portfolio_risk=0.05
    )
    
    # Test position opening
    position = manager.open_position(
        symbol='XAU/USD',
        entry_price=1000,
        side='long',
        atr=5,
        correlation_matrix=correlation_matrix
    )
    
    assert position is not None
    assert manager.positions['XAU/USD'] == position
    assert manager.daily_trades == 1
    
    # Test position closing
    manager.close_position(
        symbol='XAU/USD',
        exit_price=1010
    )
    
    assert 'XAU/USD' not in manager.positions
    assert manager.current_capital > 100000  # Profitable trade
    
def test_money_manager():
    limits = AllocationLimits(
        max_single_position=0.1,
        max_daily_risk=0.05,
        max_sector_exposure=0.2,
        max_drawdown=0.15
    )
    
    manager = MoneyManager(
        initial_capital=100000,
        allocation_limits=limits
    )
    
    # Test capital allocation
    allocated = manager.allocate_capital(
        symbol='XAU/USD',
        risk_amount=1000,
        sector='Precious Metals'
    )
    
    assert allocated is not None
    assert allocated <= 10000  # Max 10% position size
    assert manager.daily_risk_used == 1000
    
    # Test allocation limits
    can_allocate, _ = manager.can_allocate(
        symbol='XAU/USD',
        risk_amount=6000,  # Would exceed daily risk limit
        sector='Precious Metals'
    )
    
    assert not can_allocate

def test_risk_metrics(sample_data):
    _, returns = sample_data
    manager = RiskManager(initial_capital=100000)
    
    metrics = manager.calculate_risk_metrics(returns)
    
    assert hasattr(metrics, 'sharpe_ratio')
    assert hasattr(metrics, 'max_drawdown')
    assert hasattr(metrics, 'var_95')
    assert metrics.max_drawdown <= 0
    assert isinstance(metrics.sharpe_ratio, float)

def test_position_correlation_adjustment(correlation_matrix):
    sizer = PositionSizer()
    
    # Test correlation adjustment
    adjusted_size = sizer.adjust_for_correlation(
        position_size=1000,
        correlation_matrix=correlation_matrix,
        current_positions={'EUR/USD': 500}
    )
    
    assert adjusted_size < 1000  # Should be reduced due to correlation

def test_money_manager_optimal_position_size():
    limits = AllocationLimits(
        max_single_position=0.1,
        max_daily_risk=0.05,
        max_sector_exposure=0.2,
        max_drawdown=0.15
    )
    
    manager = MoneyManager(
        initial_capital=100000,
        allocation_limits=limits
    )
    
    # Test optimal position sizing
    position_size = manager.calculate_optimal_position_size(
        symbol='XAU/USD',
        volatility=0.15  # 15% annualized volatility
    )
    
    assert position_size > 0
    assert position_size <= limits.max_single_position
