# Crypto Tier Analysis - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Trading Strategies](#trading-strategies)
5. [Optimization Guide](#optimization-guide)
6. [Visualization](#visualization)

## Getting Started

### Initial Setup
1. **Configure API Keys**
```bash
# In your .env file
COINGECKO_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

2. **Basic Data Collection**
```python
from src.data.coingecko_api import CoinGeckoAPI

api = CoinGeckoAPI()
market_data = await api.get_historical_data(days=90)
```

## Basic Usage

### 1. Market Tier Analysis
```python
from src.analysis.rotation_detector import RotationDetector

# Initialize detector
detector = RotationDetector()

# Analyze market tiers
tiered_data = detector.identify_tiers(market_data)

# Get current tier distribution
print(tiered_data.groupby('tier')['market_cap'].describe())
```

### 2. Detecting Capital Flow
```python
# Generate rotation signals
signals = detector.generate_rotation_signals(tiered_data)

# View recent signals
for signal in signals[-5:]:
    print(f"Capital moving from Tier {signal.from_tier} to Tier {signal.to_tier}")
    print(f"Confidence: {signal.confidence:.2f}")
```

### 3. Smart Money Analysis
```python
from src.analysis.smart_money import SmartMoneyAnalyzer
analyzer = SmartMoneyAnalyzer()

# Detect institutional patterns
patterns = analyzer.detect_accumulation_distribution_patterns(market_data)
```

## Advanced Features

### 1. Custom Parameter Tuning
```python
# Adjust sensitivity parameters
detector.volume_threshold = 2.0  # More sensitive to volume
detector.correlation_threshold = 0.7  # Correlation requirement
detector.min_confidence = 0.6  # Signal confidence threshold
```

### 2. Backtesting Strategies
```python
from src.backtesting.backtest_engine import BacktestEngine

# Initialize backtester
backtest = BacktestEngine(initial_capital=100000.0)

# Run backtest
results = backtest.run_backtest(market_data, signals)

# View performance
print(f"Total Return: {results['metrics']['total_return']:.2%}")
print(f"Win Rate: {results['metrics']['win_rate']:.2%}")
```

## Trading Strategies

### 1. Basic Tier Rotation Strategy
This strategy follows capital as it moves between tiers:

1. **Entry Conditions:**
   - Strong rotation signal (confidence > 0.7)
   - Increasing volume in target tier
   - Positive correlation confirmation

```python
def check_entry_conditions(signal, market_data):
    if signal.confidence > 0.7:
        tier_volume = market_data[market_data['tier'] == signal.to_tier]['volume']
        if tier_volume.pct_change().mean() > 0:
            return True
    return False
```

### 2. Smart Money Following Strategy
This strategy aligns with institutional movement patterns:

1. **Entry Conditions:**
   - Large transaction detection
   - Accumulation pattern confirmation
   - Tier rotation support

```python
def smart_money_strategy(analyzer, market_data):
    patterns = analyzer.detect_accumulation_distribution_patterns(market_data)
    signals = [p for p in patterns if p.strength > 0.8]
    return signals
```

## Optimization Guide

### 1. Parameter Optimization
```python
from src.backtesting.parameter_optimizer import ParameterOptimizer

# Initialize optimizer
optimizer = ParameterOptimizer(backtest_engine)

# Run optimization
optimal_params = optimizer.optimize_tier_parameters(
    historical_data=market_data,
    detector=detector
)

# Apply optimized parameters
optimizer.apply_optimization_results(
    optimization_result=optimal_params,
    detector=detector,
    backtest_engine=backtest
)
```

### 2. Performance Monitoring
Track these key metrics:
- Win rate by tier
- Average return per trade
- Maximum drawdown
- Sharpe ratio

```python
def monitor_performance(results):
    metrics = results['metrics']
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    
    # Monitor by tier
    for tier in range(4):
        tier_return = metrics[f'tier_{tier}_return']
        print(f"Tier {tier} Return: {tier_return:.2%}")
```

## Visualization

### 1. Preparing Data for Tableau
```python
from src.visualization.tableau_export import TableauExporter

exporter = TableauExporter()

# Export analysis data
exported_files = exporter.export_for_tableau(
    market_data=market_data,
    signals=signals,
    backtest_results=results
)
```

### 2. Key Visualizations to Create

#### Tier Overview Dashboard
- Market cap distribution by tier
- Volume profile comparison
- Performance metrics by tier

#### Flow Analysis Dashboard
- Inter-tier movement heatmap
- Signal confidence timeline
- Capital flow Sankey diagram

#### Performance Dashboard
- PnL by tier
- Trade distribution
- Risk metrics visualization

## Best Practices

1. **Risk Management**
   - Use appropriate position sizing
   - Set tier-specific stop losses
   - Monitor portfolio exposure

2. **Signal Validation**
   - Confirm signals across multiple timeframes
   - Check correlation with broader market
   - Validate with volume analysis

3. **Performance Tracking**
   - Keep detailed trade logs
   - Monitor tier-specific metrics
   - Regular strategy optimization

## Troubleshooting Common Issues

1. **Low Signal Quality**
   - Increase confidence threshold
   - Add additional validation metrics
   - Check for market volatility

2. **Poor Backtest Performance**
   - Adjust position sizing
   - Review stop loss levels
   - Optimize entry/exit timing

3. **Data Issues**
   - Verify API connectivity
   - Check for missing data
   - Validate data quality

## Next Steps

1. Start with paper trading
2. Monitor system performance
3. Gradually optimize parameters
4. Scale position sizes carefully
5. Maintain detailed logs

Remember to always start with small position sizes and validate the system's performance before scaling up.
