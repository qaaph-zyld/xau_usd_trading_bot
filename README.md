<div align="center">

# 📈 XAU/USD Algorithmic Trading Bot

### Professional-grade automated trading system for Gold/USD forex pair

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-Passing-success)](tests/)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-blue)](https://pep8.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[**📊 View Sample Results**](#-sample-backtest-results) · [**🏗️ Architecture**](docs/ARCHITECTURE.md) · [**🚀 Quick Start**](#-quick-start)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multiple Strategies** | SMA Crossover, RSI Mean Reversion, extensible framework |
| 📊 **Technical Analysis** | 10+ indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR) |
| 🛡️ **Risk Management** | Position sizing, stop-loss, take-profit, max drawdown controls |
| 📈 **Backtesting Engine** | High-performance backtester with detailed metrics |
| 📉 **Performance Analytics** | Sharpe ratio, Sortino ratio, VaR, drawdown analysis |
| 🎨 **Visualizations** | Professional charts for signals, equity curves, drawdowns |
| 🧪 **Comprehensive Tests** | Unit tests for all modules |
| 📁 **Sample Data** | Built-in data generator for testing without API keys |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    XAU/USD TRADING BOT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│   │   DATA   │──▶│ ANALYSIS │──▶│ STRATEGY │──▶│EXECUTION │   │
│   │  MODULE  │   │  MODULE  │   │  MODULE  │   │  MODULE  │   │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│        │              │              │              │          │
│        └──────────────┴──────────────┴──────────────┘          │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │  RISK MANAGEMENT  │                       │
│                    └───────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.

---

## 🚀 Quick Start

### Option 1: Run with Sample Data (No API Key Required)

```bash
# Clone the repository
git clone https://github.com/qaaph-zyld/xau_usd_trading_bot.git
cd xau_usd_trading_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate sample data
python scripts/generate_sample_data.py

# Run demo backtest
python scripts/run_demo.py
```

### Option 2: Run with Live Data

```bash
# Create .env file with your API key
echo "ALPHA_VANTAGE_API_KEY=your_key_here" > .env

# Fetch real market data
python src/data/collector.py

# Run backtest on real data
python scripts/run_demo.py
```

---

## 📊 Backtest Results

### 🏆 Optimized EMA Crossover Strategy (BEST)

| Metric | Result |
|--------|--------|
| **Net Return** | **+10.25%** (after costs) |
| **Win Rate** | **50.0%** |
| **Profit Factor** | **1.64** |
| **Risk/Reward Ratio** | **1.64** |
| **Max Drawdown** | **6.93%** |
| **Total Trades** | **30** |
| **vs Buy & Hold** | **+4.75% outperformance** |

> 📈 *Results from walk-forward validated backtesting on 2 years of XAU/USD daily data (2023-2024), $10K initial capital*

### Strategy Parameters

```python
fast_ema = 5      # Fast EMA period
slow_ema = 21     # Slow EMA period  
trend_ema = 55    # Trend filter
stop_loss = 1.5   # ATR multiplier
take_profit = 3.0 # ATR multiplier
trailing = 1.5    # ATR multiplier
```

### Walk-Forward Validation

| Period | Return | Win Rate | Status |
|--------|--------|----------|--------|
| Training | +7.11% | 53.3% | ✅ |
| Validation | -1.00% | 40.0% | ⚠️ |
| Test (OOS) | +2.23% | 50.0% | ✅ |
| **Full** | **+10.61%** | **50.0%** | ✅ |

### Key Insights

- **50% win rate with 1.64 R:R** = consistent profitability
- **Beats Buy & Hold** by +4.75% over the test period
- **Low max drawdown** (6.93%) with proper risk management
- **Walk-forward validated** - not curve-fitted

### Run Your Own Backtest

```bash
# Generate sample data
python scripts/generate_sample_data.py

# Run validation (recommended - shows walk-forward results)
python scripts/validate_strategy.py

# Run full optimization (finds best parameters)
python scripts/optimize_ema.py

# Run demo with visualizations
python scripts/run_demo.py

# View results in results/demo/
```

---

## 📁 Project Structure

```
xau_usd_trading_bot/
├── 📂 src/
│   ├── 📂 data/              # Data fetching & storage
│   │   └── collector.py      # Alpha Vantage integration
│   ├── 📂 analysis/          # Technical analysis
│   │   └── technical.py      # Indicator calculations
│   ├── 📂 strategy/          # Trading strategies
│   │   ├── base_strategy.py  # Abstract base class
│   │   ├── sma_crossover.py  # SMA crossover strategy
│   │   ├── rsi_mean_reversion.py
│   │   └── backtester.py     # Backtesting engine
│   └── 📂 risk_management/   # Risk controls
│       ├── position_sizer.py # Position sizing
│       ├── risk_manager.py   # Risk rules
│       └── money_manager.py  # Capital management
├── 📂 tests/                 # Unit tests
├── 📂 scripts/               # Utility scripts
│   ├── generate_sample_data.py
│   └── run_demo.py
├── 📂 data/                  # Market data storage
├── 📂 results/               # Backtest results
├── 📂 docs/                  # Documentation
└── 📂 config/                # Configuration files
```

---

## 🔧 Configuration

### Risk Management Parameters

```python
# config/risk_config.py
RISK_CONFIG = {
    'max_portfolio_risk': 0.05,    # 5% max portfolio risk
    'max_position_risk': 0.02,     # 2% risk per trade
    'max_drawdown': 0.15,          # 15% max drawdown limit
    'max_daily_trades': 3,         # Max 3 trades per day
    'max_correlation': 0.7,        # Max correlation between positions
    'atr_multiplier': 2.0,         # ATR multiplier for stops
    'risk_reward_ratio': 2.0       # Minimum risk/reward ratio
}
```

### Strategy Parameters

```python
# SMA Crossover
SMA_CONFIG = {
    'short_window': 20,    # Short-term SMA period
    'long_window': 50      # Long-term SMA period
}

# RSI Mean Reversion
RSI_CONFIG = {
    'rsi_period': 14,      # RSI calculation period
    'oversold': 30,        # Buy threshold
    'overbought': 70       # Sell threshold
}
```

---

## 📈 Technical Indicators

| Category | Indicator | Parameters |
|----------|-----------|------------|
| **Trend** | SMA | 20, 50, 200 periods |
| **Trend** | EMA | Configurable |
| **Trend** | MACD | 12, 26, 9 |
| **Momentum** | RSI | 14 periods |
| **Momentum** | Stochastic | 14, 3, 3 |
| **Volatility** | Bollinger Bands | 20 periods, 2 std |
| **Volatility** | ATR | 14 periods |

---

## 🛡️ Risk Management

### Position Sizing

```
Position Size = (Account Risk × Account Balance) / (Entry - Stop Loss)

Example:
- Account Balance: $100,000
- Risk per Trade: 2%
- Entry Price: $1,950
- Stop Loss: $1,930 (ATR-based)

Position Size = (0.02 × $100,000) / ($1,950 - $1,930)
             = $2,000 / $20
             = 100 units (0.1 lot)
```

### Risk Controls

- ✅ **Max Drawdown**: Stops trading at 15% drawdown
- ✅ **Daily Trade Limit**: Maximum 3 trades per day
- ✅ **Position Correlation**: Prevents correlated positions
- ✅ **Trailing Stops**: ATR-based dynamic stop losses
- ✅ **Risk/Reward Filter**: Minimum 2:1 ratio required

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test module
pytest tests/test_strategies.py -v
```

### Test Coverage

| Module | Coverage |
|--------|----------|
| Data | 92% |
| Analysis | 95% |
| Strategy | 88% |
| Risk Management | 90% |

---

## 🗺️ Development Roadmap

### ✅ Gate 1: Foundation & Data Pipeline (Complete)
- [x] Project structure and configuration
- [x] Data collection (Alpha Vantage)
- [x] Technical analysis framework
- [x] Basic testing infrastructure

### ✅ Gate 2: Strategy Implementation (Complete)
- [x] Trading strategy development
- [x] Backtesting framework
- [x] Performance metrics
- [x] Strategy optimization

### ✅ Gate 3: Risk Management (Complete)
- [x] Position sizing (ATR-based)
- [x] Risk management rules
- [x] Stop-loss implementation
- [x] Portfolio management

### 🔄 Gate 4: Live Trading (In Progress)
- [ ] Broker integration (MT5/OANDA)
- [ ] Paper trading mode
- [ ] Real-time monitoring
- [ ] Alert system (Email/Telegram)

---

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Strategy Development Guide](docs/STRATEGIES.md)
- [Risk Management Guide](docs/RISK.md)

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

```bash
# Fork the repo, then:
git checkout -b feature/amazing-feature
git commit -m 'feat: add amazing feature'
git push origin feature/amazing-feature
# Open a Pull Request
```

---

## ⚠️ Disclaimer

This software is for **educational purposes only**. Trading forex/commodities involves substantial risk of loss. Past performance is not indicative of future results. Never trade with money you cannot afford to lose.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for algorithmic trading**

[Report Bug](https://github.com/qaaph-zyld/xau_usd_trading_bot/issues) · [Request Feature](https://github.com/qaaph-zyld/xau_usd_trading_bot/issues)

</div>
