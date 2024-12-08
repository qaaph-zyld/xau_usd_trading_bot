import pytest
import pandas as pd
import numpy as np
from src.analysis.technical import TechnicalAnalyzer

@pytest.fixture
def sample_data():
    """Create sample OHLC data for testing"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
    data = {
        'open': np.random.randn(100).cumsum() + 1000,
        'high': np.random.randn(100).cumsum() + 1002,
        'low': np.random.randn(100).cumsum() + 998,
        'close': np.random.randn(100).cumsum() + 1001
    }
    return pd.DataFrame(data, index=dates)

def test_technical_analyzer_initialization(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    assert analyzer.data is not None
    assert len(analyzer.data) == len(sample_data)

def test_moving_averages(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    data = analyzer.add_moving_averages([20, 50])
    assert 'sma_20' in data.columns
    assert 'sma_50' in data.columns

def test_rsi(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    data = analyzer.add_rsi()
    assert 'rsi' in data.columns
    assert data['rsi'].max() <= 100
    assert data['rsi'].min() >= 0

def test_bollinger_bands(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    data = analyzer.add_bollinger_bands()
    assert 'bb_upper' in data.columns
    assert 'bb_middle' in data.columns
    assert 'bb_lower' in data.columns

def test_analyze_all(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    data = analyzer.analyze_all()
    expected_columns = [
        'sma_20', 'sma_50', 'sma_200',
        'rsi',
        'bb_upper', 'bb_middle', 'bb_lower',
        'macd', 'macd_signal', 'macd_diff',
        'atr'
    ]
    for col in expected_columns:
        assert col in data.columns
