# Crypto Tier Analysis System

## Overview
This system analyzes cryptocurrency market data to identify and track capital flow between different market cap tiers. It implements a theory that capital moves through the crypto market in identifiable patterns across 3-5 tiers of projects, which can be used to optimize trading strategies.

## Key Features
- Market tier classification
- Capital flow tracking
- Smart money movement detection
- Automated backtesting
- Parameter optimization
- Tableau visualization exports

## Project Structure
```
crypto_tier_analyzer/
├── .env                          # Environment variables
├── requirements.txt              # Project dependencies
├── README.md                     # Project documentation
├── src/
│   ├── config/                  # Configuration settings
│   ├── data/                    # Data handling
│   ├── analysis/                # Analysis modules
│   ├── backtesting/            # Backtesting engine
│   └── visualization/          # Tableau exports
└── tests/                      # Unit tests
```

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd crypto_tier_analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.template` to `.env` and fill in your API keys:
```bash
cp .env.template .env
```

## Configuration
Edit `.env` file with your settings:
```
COINGECKO_API_KEY=your_coingecko_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
MAX_TIERS=4
BACKTEST_DAYS=90
```

## Core Components

### 1. Data Collection (`data/coingecko_api.py`)
- Fetches market data from CoinGecko API
- Handles rate limiting and error handling
- Processes raw data into analyzable format

### 2. Tier Analysis (`analysis/rotation_detector.py`)
- Classifies cryptocurrencies into market cap tiers
- Detects capital movement between tiers
- Generates rotation signals

### 3. Smart Money Detection (`analysis/smart_money.py`)
- Identifies institutional trading patterns
- Analyzes volume profiles
- Detects accumulation/distribution patterns

### 4. Backtesting (`backtesting/backtest_engine.py`)
- Simulates trading strategies
- Tracks performance metrics
- Handles position sizing and risk management

### 5. Parameter Optimization (`backtesting/parameter_optimizer.py`)
- Optimizes strategy parameters
- Tier-specific adjustments
- Performance scoring

### 6. Visualization (`visualization/tableau_export.py`)
- Prepares data for Tableau
- Creates visualization-ready datasets
- Generates Tableau instructions

## Usage Example

```python
from src.data.coingecko_api import CoinGeckoAPI
from src.analysis.rotation_detector import RotationDetector
from src.backtesting.backtest_engine import BacktestEngine
from src.visualization.tableau_export import TableauExporter

# Initialize components
api = CoinGeckoAPI()
detector = RotationDetector()
backtest = BacktestEngine()
exporter = TableauExporter()

# Fetch and analyze data
market_data = await api.get_historical_data(days=90)
signals = detector.generate_rotation_signals(market_data)

# Run backtest
results = backtest.run_backtest(market_data, signals)

# Export for visualization
exported_files = exporter.export_for_tableau(market_data, signals, results)
```

## Analysis Process

1. **Tier Classification**
   - Market cap-based tier assignment
   - Volume profile analysis
   - Volatility considerations

2. **Capital Flow Detection**
   - Inter-tier volume analysis
   - Price correlation tracking
   - Smart money movement patterns

3. **Signal Generation**
   - Confidence scoring
   - Multi-factor validation
   - Tier-specific thresholds

4. **Trading Strategy**
   - Position sizing by tier
   - Risk management rules
   - Performance tracking

## Visualization Guidelines

The Tableau export creates four main views:

1. **Tier Overview Dashboard**
   - Market cap distribution
   - Volume profiles
   - Tier correlations

2. **Capital Flow Dashboard**
   - Inter-tier movements
   - Flow strength indicators
   - Rotation patterns

3. **Smart Money Dashboard**
   - Institutional patterns
   - Accumulation/distribution
   - Volume analysis

4. **Performance Dashboard**
   - Strategy results
   - Risk metrics
   - Tier-specific performance

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details

## Acknowledgments
- CoinGecko API for market data
- Tableau for visualization capabilities

## Support
For support and questions, please create an issue in the repository.
