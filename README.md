# XAU/USD Forex Trading Bot

## Project Overview
This is an automated trading system for XAU/USD (Gold/US Dollar) forex pair trading. The system uses technical analysis and algorithmic trading strategies to identify and execute trading opportunities.

## GATE Progress (MVP Development)
Our development follows the GATE (Gradual, Achievable, Testable, Evolutionary) methodology:

### Gate 1: Foundation & Data Pipeline (25% of MVP) 
- Project structure and configuration
- Data collection and storage
- Technical analysis framework
- Basic testing infrastructure

### Gate 2: Strategy Implementation (30% of MVP) 
- Trading strategy development
- Backtesting framework
- Performance metrics
- Strategy optimization

### Gate 3: Risk Management (25% of MVP) 
- Position sizing
- Risk management rules
- Stop-loss implementation
- Portfolio management

### Gate 4: Live Trading (20% of MVP) 
- Broker integration
- Live trading capabilities
- Monitoring and alerting
- Performance tracking

## Project Structure
```
├── src/
│   ├── data/          # Data handling and storage
│   ├── analysis/      # Technical analysis
│   ├── strategy/      # Trading strategies
│   └── utils/         # Utility functions
├── tests/             # Test cases
├── config/            # Configuration files
└── notebooks/         # Analysis notebooks
```

## Setup
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API credentials:
```
ALPHA_VANTAGE_API_KEY=your_key_here
```

## Current Features (Gate 1)
- Data fetching from Alpha Vantage
- Technical indicator calculation:
  - Moving Averages (SMA)
  - RSI (Relative Strength Index)
  - Bollinger Bands
  - MACD
  - ATR (Average True Range)
- Data storage and management
- Comprehensive testing suite

## Usage
1. Set up your environment variables
2. Run the data collection script:
```bash
python src/data/collector.py
```

## Testing
Run tests using pytest:
```bash
pytest tests/
```

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
