# Configuration Guide - Crypto Tier Analysis

## Introduction

This guide provides a detailed explanation of all configuration options in the Crypto Tier Analysis System. Understanding these settings is crucial for optimizing the system's performance and achieving reliable market analysis results. We'll explore each configuration category, explain its purpose, and provide guidance on choosing appropriate values.

## Environment Variables

The system uses a .env file for sensitive and environment-specific configurations. Here's a complete explanation of each variable:

```bash
# API Configuration
COINGECKO_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# System Settings
MAX_TIERS=4                  # Number of market cap tiers
UPDATE_FREQUENCY=3600        # Data update interval in seconds
BACKTEST_DAYS=90            # Historical data lookback period
LOG_LEVEL=INFO              # Logging verbosity

# Storage Configuration
DATA_STORAGE_PATH=./data/processed
LOG_FILE_PATH=./logs/crypto_analysis.log

# Analysis Parameters
VOLUME_THRESHOLD=2.0        # Volume spike detection threshold
CORRELATION_THRESHOLD=0.7   # Tier correlation minimum
MIN_CONFIDENCE=0.6         # Signal confidence threshold
```

### Understanding API Keys

Your API keys provide access to essential data services. Let's examine the implications of different API tiers:

CoinGecko API:
- Free Tier: 50 calls/minute
  - Suitable for initial testing
  - May require request queuing
- Pro Tier: 500 calls/minute
  - Recommended for production
  - Enables real-time analysis

Anthropic API:
- Requests are rate-limited
- Consider implementing exponential backoff
- Cache responses when possible

## System Configuration

### Tier Settings

The MAX_TIERS setting deserves special attention. The default value of 4 tiers represents a balance between granularity and signal clarity:

```python
# Example tier distribution
tier_boundaries = {
    0: "Top Tier (>$10B market cap)",
    1: "High Cap ($1B-$10B)",
    2: "Mid Cap ($100M-$1B)",
    3: "Lower Cap ($10M-$100M)"
}
```

Adjusting tier boundaries affects:
- Capital flow detection sensitivity
- Signal generation frequency
- Trading opportunity identification

### Update Frequency

The UPDATE_FREQUENCY setting influences data freshness and API usage. Consider these factors when configuring:

```python
# Update frequency considerations
frequencies = {
    300: "5 minutes - High API usage, real-time analysis",
    3600: "1 hour - Balanced approach, suitable for most cases",
    86400: "24 hours - Conservative API usage, trend analysis"
}
```

Your choice should balance:
- Data freshness requirements
- API rate limits
- Analysis time frames

## Analysis Parameters

### Volume Analysis

The VOLUME_THRESHOLD setting determines how sensitive the system is to volume spikes:

```python
class VolumeAnalyzer:
    def __init__(self, threshold: float = 2.0):
        """
        Initialize volume analyzer
        
        Parameters:
            threshold: Number of standard deviations for spike detection
                2.0 = 95% confidence level
                2.5 = 99% confidence level
                3.0 = 99.9% confidence level
        """
        self.threshold = threshold
```

Higher thresholds result in:
- Fewer false positives
- Stronger signal confidence
- Missed opportunities

Lower thresholds provide:
- More trading signals
- Higher noise level
- Earlier pattern detection

### Correlation Analysis

The CORRELATION_THRESHOLD affects how the system identifies related market movements:

```python
class CorrelationAnalyzer:
    def __init__(self, threshold: float = 0.7):
        """
        Initialize correlation analyzer
        
        Parameters:
            threshold: Minimum correlation coefficient
                0.7 = Strong correlation
                0.5 = Moderate correlation
                0.3 = Weak correlation
        """
        self.threshold = threshold
```

Consider these correlation levels:
- Strong (>0.7): Clear market relationships
- Moderate (0.5-0.7): Potential relationships
- Weak (<0.5): Possible noise

## Performance Optimization

### Memory Management

Configure memory usage based on your hardware:

```python
# Memory optimization settings
memory_config = {
    "cache_size": 1000,      # Number of cached items
    "data_retention": 90,    # Days of historical data
    "batch_size": 1000       # Records per processing batch
}
```

Guidelines for different hardware:
- 8GB RAM: Conservative settings
- 16GB RAM: Balanced performance
- 32GB+ RAM: Aggressive caching

### Processing Optimization

Tune processing parameters for your CPU:

```python
# Processing configuration
processing_config = {
    "parallel_jobs": cpu_count() - 1,  # Leave one core free
    "chunk_size": 10000,              # Data points per chunk
    "vectorize": True                  # Use numpy vectorization
}
```

## Logging Configuration

### Log Levels

Choose appropriate logging levels for different environments:

```python
# Logging configuration
logging_config = {
    "development": {
        "level": "DEBUG",
        "format": "detailed",
        "output": "console"
    },
    "production": {
        "level": "INFO",
        "format": "compact",
        "output": "file"
    }
}
```

### Log Rotation

Configure log file management:

```python
# Log rotation settings
log_rotation = {
    "max_size": "100MB",
    "backup_count": 5,
    "compression": True
}
```

## Advanced Configuration

### Backtesting Parameters

Fine-tune backtesting behavior:

```python
# Backtesting configuration
backtest_config = {
    "initial_capital": 100000,
    "position_sizing": {
        "max_position": 0.1,     # Maximum single position
        "tier_adjustments": {
            0: 1.0,              # Top tier full size
            1: 0.85,             # High cap adjustment
            2: 0.70,             # Mid cap adjustment
            3: 0.55              # Lower cap adjustment
        }
    },
    "risk_management": {
        "stop_loss": 0.05,       # 5% stop loss
        "take_profit": 0.15      # 15% take profit
    }
}
```

### Signal Generation

Configure signal sensitivity:

```python
# Signal configuration
signal_config = {
    "min_confidence": 0.6,
    "confirmation_required": True,
    "lookback_periods": 30,
    "volume_weight": 0.4,
    "correlation_weight": 0.4,
    "pattern_weight": 0.2
}
```

## Configuration Examples

### Conservative Setup
```bash
VOLUME_THRESHOLD=2.5
CORRELATION_THRESHOLD=0.8
MIN_CONFIDENCE=0.7
UPDATE_FREQUENCY=3600
```

### Aggressive Setup
```bash
VOLUME_THRESHOLD=1.8
CORRELATION_THRESHOLD=0.6
MIN_CONFIDENCE=0.5
UPDATE_FREQUENCY=300
```

## Troubleshooting

Common configuration issues and solutions:

### Memory Issues
- Reduce cache size
- Increase data chunking
- Enable garbage collection

### Performance Issues
- Adjust batch sizes
- Optimize parallel processing
- Review logging levels

### API Issues
- Implement request queuing
- Add error retries
- Enable response caching

## Best Practices

Remember these key principles when configuring the system:

1. Start Conservative
   - Begin with default values
   - Monitor system behavior
   - Adjust gradually

2. Test Changes
   - Use backtesting
   - Validate results
   - Document impacts

3. Monitor Resources
   - Watch memory usage
   - Track API calls
   - Review log files

4. Regular Review
   - Audit configurations
   - Update parameters
   - Optimize performance

## Configuration Checklist

Before deploying changes:
1. Verify API keys
2. Test rate limits
3. Check memory usage
4. Validate log settings
5. Review performance
6. Document changes

Remember that configuration is an iterative process. Start with conservative values and adjust based on your specific needs and system performance.
