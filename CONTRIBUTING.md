# Contributing to XAU/USD Trading Bot

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title describing the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Relevant logs or screenshots

### Suggesting Features

1. Check if the feature has been suggested
2. Create an issue with:
   - Clear description of the feature
   - Use case and benefits
   - Potential implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following our style guide
4. Write/update tests
5. Run tests locally:
   ```bash
   pytest tests/ -v
   ```
6. Commit with clear messages:
   ```bash
   git commit -m "feat: add new indicator"
   ```
7. Push and open a PR

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/xau_usd_trading_bot.git
cd xau_usd_trading_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/ -v
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes

### Example

```python
def calculate_position_size(
    capital: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float
) -> float:
    """
    Calculate position size based on risk parameters.
    
    Args:
        capital: Available trading capital
        risk_percent: Percentage of capital to risk (0.02 = 2%)
        entry_price: Entry price for the trade
        stop_loss: Stop loss price
    
    Returns:
        Position size in units
    
    Raises:
        ValueError: If stop_loss equals entry_price
    """
    if entry_price == stop_loss:
        raise ValueError("Stop loss cannot equal entry price")
    
    risk_amount = capital * risk_percent
    price_risk = abs(entry_price - stop_loss)
    
    return risk_amount / price_risk
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Adding tests
- `refactor:` - Code restructuring
- `perf:` - Performance improvement

Examples:
```
feat: add Bollinger Band squeeze indicator
fix: correct RSI calculation for edge cases
docs: update API documentation
test: add tests for position sizing
```

## Testing

### Writing Tests

```python
import pytest
from src.analysis.technical import TechnicalAnalyzer

class TestTechnicalAnalyzer:
    def test_sma_calculation(self, sample_data):
        """Test SMA calculation accuracy."""
        analyzer = TechnicalAnalyzer(sample_data)
        result = analyzer.add_moving_averages([20])
        
        assert 'sma_20' in result.columns
        assert result['sma_20'].iloc[19] is not None
    
    def test_invalid_data_raises_error(self):
        """Test that invalid data raises ValueError."""
        with pytest.raises(ValueError):
            TechnicalAnalyzer(pd.DataFrame())
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific module
pytest tests/test_strategies.py -v

# Specific test
pytest tests/test_strategies.py::TestSMACrossover -v
```

## Adding New Strategies

1. Create a new file in `src/strategy/`:
   ```python
   # src/strategy/my_strategy.py
   from .base_strategy import BaseStrategy
   
   class MyStrategy(BaseStrategy):
       def __init__(self, data, **params):
           super().__init__(data)
           # Initialize parameters
       
       def generate_signals(self):
           # Implement signal generation
           pass
   ```

2. Add tests in `tests/test_strategies.py`

3. Update documentation

4. Add to strategy runner if applicable

## Adding New Indicators

1. Add to `src/analysis/technical.py`:
   ```python
   def add_my_indicator(self, param: int = 14):
       """
       Add My Indicator to the data.
       
       Args:
           param: Indicator parameter
       """
       self.data['my_indicator'] = # calculation
       return self.data
   ```

2. Add tests in `tests/test_technical.py`

3. Update documentation

## Questions?

Open an issue with the "question" label or reach out via discussions.

## Recognition

Contributors will be acknowledged in our README. Thank you for helping improve this project!
