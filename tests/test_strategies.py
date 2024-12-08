import pytest
import pandas as pd
import numpy as np
from src.strategy.sma_crossover import SMACrossoverStrategy
from src.strategy.rsi_mean_reversion import RSIMeanReversionStrategy
from src.strategy.backtester import Backtester
from datetime import datetime, timedelta

@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start='2023-01-01', periods=500, freq='H')
    data = {
        'open': np.random.randn(500).cumsum() + 1000,
        'high': np.random.randn(500).cumsum() + 1002,
        'low': np.random.randn(500).cumsum() + 998,
        'close': np.random.randn(500).cumsum() + 1001,
        'volume': np.random.randint(1000, 10000, 500)
    }
    return pd.DataFrame(data, index=dates)

def test_sma_crossover_strategy(sample_data):
    strategy = SMACrossoverStrategy(sample_data, short_window=20, long_window=50)
    results = strategy.backtest()
    
    assert isinstance(results, dict)
    assert 'total_return' in results
    assert 'sharpe_ratio' in results
    assert 'max_drawdown' in results
    
def test_rsi_mean_reversion_strategy(sample_data):
    strategy = RSIMeanReversionStrategy(sample_data)
    results = strategy.backtest()
    
    assert isinstance(results, dict)
    assert 'total_return' in results
    assert 'sharpe_ratio' in results
    assert 'max_drawdown' in results
    
def test_strategy_optimization(sample_data):
    strategy = SMACrossoverStrategy(sample_data)
    optimal_params = strategy.optimize_parameters(
        short_range=(10, 30),
        long_range=(40, 60)
    )
    
    assert isinstance(optimal_params, dict)
    assert 'short_window' in optimal_params
    assert 'long_window' in optimal_params
    assert 'performance' in optimal_params
    
def test_backtester(sample_data):
    strategies = [SMACrossoverStrategy, RSIMeanReversionStrategy]
    backtester = Backtester(sample_data, strategies)
    
    results = backtester.run_backtest()
    assert len(results) == len(strategies)
    
    best_strategy = backtester.get_best_strategy()
    assert best_strategy in [strategy.__name__ for strategy in strategies]
    
def test_strategy_signals(sample_data):
    sma_strategy = SMACrossoverStrategy(sample_data)
    rsi_strategy = RSIMeanReversionStrategy(sample_data)
    
    sma_signals = sma_strategy.generate_signals()
    rsi_signals = rsi_strategy.generate_signals()
    
    assert isinstance(sma_signals, pd.Series)
    assert isinstance(rsi_signals, pd.Series)
    assert set(sma_signals.unique()).issubset({-1, 0, 1})
    assert set(rsi_signals.unique()).issubset({-1, 0, 1})
