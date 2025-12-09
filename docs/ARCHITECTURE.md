# System Architecture

## Overview

The XAU/USD Trading Bot is a modular algorithmic trading system designed for gold/USD forex pair trading. The architecture follows clean separation of concerns with distinct modules for data handling, analysis, strategy execution, and risk management.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           XAU/USD TRADING BOT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │    DATA     │───▶│  ANALYSIS   │───▶│  STRATEGY   │───▶│  EXECUTION  │  │
│  │   MODULE    │    │   MODULE    │    │   MODULE    │    │   MODULE    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                 │                  │                  │          │
│         │                 │                  │                  │          │
│         └─────────────────┴──────────────────┴──────────────────┘          │
│                                    │                                        │
│                          ┌─────────▼─────────┐                             │
│                          │  RISK MANAGEMENT  │                             │
│                          │      MODULE       │                             │
│                          └───────────────────┘                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Details

### 1. Data Module (`src/data/`)

Responsible for data acquisition, storage, and preprocessing.

```
┌─────────────────────────────────────────┐
│            DATA MODULE                   │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │      ForexDataCollector         │    │
│  ├─────────────────────────────────┤    │
│  │ • fetch_intraday_data()         │    │
│  │ • load_latest_data()            │    │
│  │ • validate_data()               │    │
│  └─────────────────────────────────┘    │
│                 │                       │
│                 ▼                       │
│  ┌─────────────────────────────────┐    │
│  │        Data Sources             │    │
│  ├─────────────────────────────────┤    │
│  │ • Alpha Vantage API             │    │
│  │ • Sample Data Generator         │    │
│  │ • CSV File Storage              │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

**Key Features:**
- Multi-source data fetching (API, local files)
- Automatic data validation
- Multiple timeframe support (1H, 4H, 1D, 1W)
- Sample data generation for testing

### 2. Analysis Module (`src/analysis/`)

Handles technical indicator calculation and market analysis.

```
┌─────────────────────────────────────────┐
│          ANALYSIS MODULE                │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │      TechnicalAnalyzer          │    │
│  ├─────────────────────────────────┤    │
│  │                                 │    │
│  │  Trend Indicators:              │    │
│  │  • SMA (20, 50, 200)           │    │
│  │  • EMA                          │    │
│  │  • MACD                         │    │
│  │                                 │    │
│  │  Momentum Indicators:           │    │
│  │  • RSI                          │    │
│  │  • Stochastic                   │    │
│  │                                 │    │
│  │  Volatility Indicators:         │    │
│  │  • Bollinger Bands              │    │
│  │  • ATR                          │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

**Supported Indicators:**
| Category | Indicators |
|----------|------------|
| Trend | SMA, EMA, MACD |
| Momentum | RSI, Stochastic |
| Volatility | Bollinger Bands, ATR |
| Volume | Volume SMA, OBV |

### 3. Strategy Module (`src/strategy/`)

Implements trading strategies with backtesting capabilities.

```
┌─────────────────────────────────────────────────────────────┐
│                    STRATEGY MODULE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   BaseStrategy                         │  │
│  │  (Abstract Base Class)                                │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  • generate_signals()    [abstract]                   │  │
│  │  • calculate_position_size()                          │  │
│  │  • backtest()                                         │  │
│  │  • _calculate_performance_metrics()                   │  │
│  │  • plot_performance()                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▲                                  │
│            ┌─────────────┼─────────────┐                   │
│            │             │             │                   │
│  ┌─────────┴───┐  ┌──────┴──────┐  ┌───┴─────────┐        │
│  │    SMA      │  │    RSI      │  │   Custom    │        │
│  │  Crossover  │  │   Mean      │  │  Strategy   │        │
│  │  Strategy   │  │  Reversion  │  │   (User)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Backtester                          │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  • run_backtest()                                     │  │
│  │  • generate_report()                                  │  │
│  │  • get_best_strategy()                                │  │
│  │  • _generate_comparison_plots()                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Available Strategies:**

| Strategy | Description | Signals |
|----------|-------------|---------|
| SMA Crossover | Golden/Death cross of moving averages | Buy: Short SMA > Long SMA, Sell: Short SMA < Long SMA |
| RSI Mean Reversion | Overbought/oversold conditions | Buy: RSI < 30, Sell: RSI > 70 |

### 4. Risk Management Module (`src/risk_management/`)

Comprehensive risk control and position management.

```
┌─────────────────────────────────────────────────────────────┐
│                RISK MANAGEMENT MODULE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              RiskManager                             │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  Controls:                                          │    │
│  │  • Max Portfolio Risk: 5%                           │    │
│  │  • Max Drawdown: 15%                                │    │
│  │  • Max Daily Trades: 3                              │    │
│  │  • Max Correlation: 0.7                             │    │
│  │                                                     │    │
│  │  Methods:                                           │    │
│  │  • can_open_position()                              │    │
│  │  • open_position()                                  │    │
│  │  • close_position()                                 │    │
│  │  • calculate_risk_metrics()                         │    │
│  │  • update_stops()                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│          ┌───────────────┼───────────────┐                  │
│          ▼               ▼               ▼                  │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐      │
│  │PositionSizer │ │ MoneyManager  │ │ RiskMetrics   │      │
│  ├───────────────┤ ├───────────────┤ ├───────────────┤      │
│  │• ATR-based   │ │• Kelly        │ │• VaR (95%)    │      │
│  │  stops       │ │  Criterion    │ │• Sharpe Ratio │      │
│  │• Risk/Reward │ │• Max position │ │• Sortino      │      │
│  │  ratios      │ │  limits       │ │• Drawdown     │      │
│  └───────────────┘ └───────────────┘ └───────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
                                   ┌─────────────────┐
                                   │   Market Data   │
                                   │  (Alpha Vantage)│
                                   └────────┬────────┘
                                            │
                                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                              DATA PIPELINE                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐  │
│   │   Fetch    │───▶│  Validate  │───▶│  Store     │───▶│  Preprocess│  │
│   │   Data     │    │  Data      │    │  (CSV)     │    │  (Clean)   │  │
│   └────────────┘    └────────────┘    └────────────┘    └────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            ANALYSIS PIPELINE                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐  │
│   │   Load     │───▶│  Calculate │───▶│  Generate  │───▶│  Validate  │  │
│   │   OHLCV    │    │ Indicators │    │  Features  │    │  Signals   │  │
│   └────────────┘    └────────────┘    └────────────┘    └────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           TRADING PIPELINE                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐  │
│   │  Strategy  │───▶│   Risk     │───▶│  Position  │───▶│  Execute   │  │
│   │  Signal    │    │   Check    │    │   Size     │    │   Trade    │  │
│   └────────────┘    └────────────┘    └────────────┘    └────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Backtesting Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      BACKTESTING ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. INITIALIZATION                                              │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ Load historical data → Initialize strategies →        │   │
│     │ Set initial capital → Configure risk parameters       │   │
│     └──────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  2. SIMULATION LOOP                                            │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ For each timestamp:                                   │   │
│     │   • Generate signals from strategy                    │   │
│     │   • Check risk constraints                            │   │
│     │   • Calculate position size                           │   │
│     │   • Execute simulated trade                           │   │
│     │   • Update portfolio value                            │   │
│     │   • Track performance metrics                         │   │
│     └──────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  3. ANALYSIS                                                   │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ Calculate metrics → Generate reports →                │   │
│     │ Create visualizations → Compare strategies            │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.10+ | Core development |
| Data Processing | Pandas, NumPy | Data manipulation |
| Technical Analysis | TA-Lib, ta | Indicator calculation |
| Visualization | Matplotlib, Seaborn | Charts and reports |
| Machine Learning | Scikit-learn | Strategy optimization |
| Testing | Pytest | Unit and integration tests |
| API Client | Alpha Vantage | Market data |

## Directory Structure

```
xau_usd_trading_bot/
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── collector.py          # Data fetching
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── technical.py          # Technical indicators
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── base_strategy.py      # Abstract base class
│   │   ├── sma_crossover.py      # SMA crossover strategy
│   │   ├── rsi_mean_reversion.py # RSI strategy
│   │   ├── backtester.py         # Backtesting engine
│   │   └── runner.py             # Strategy runner
│   └── risk_management/
│       ├── __init__.py
│       ├── position_sizer.py     # Position sizing
│       ├── risk_manager.py       # Risk controls
│       └── money_manager.py      # Capital management
├── tests/
│   ├── test_technical.py
│   ├── test_strategies.py
│   └── test_risk_management.py
├── scripts/
│   ├── generate_sample_data.py   # Sample data generator
│   └── run_demo.py               # Demo script
├── data/                         # Data storage
├── results/                      # Backtest results
├── docs/                         # Documentation
└── config/                       # Configuration files
```

## Performance Considerations

1. **Data Efficiency**: Use chunked processing for large datasets
2. **Vectorization**: Prefer NumPy/Pandas vectorized operations
3. **Caching**: Cache computed indicators to avoid recalculation
4. **Memory**: Use appropriate data types to minimize memory footprint
