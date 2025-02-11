# API Documentation - Crypto Tier Analysis

## Overview

This documentation covers the integration with external APIs (CoinGecko, Claude) and internal system APIs.

## Table of Contents
1. [External APIs](#external-apis)
2. [Internal APIs](#internal-apis)
3. [Rate Limits](#rate-limits)
4. [Authentication](#authentication)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

## External APIs

### CoinGecko API

#### Authentication
```python
headers = {
    'X-Cg-Pro-Api-Key': 'your_api_key',
    'Accept': 'application/json'
}
```

#### Endpoints

1. **Market Data**
```python
GET /coins/markets
Parameters:
- vs_currency: str (default: 'usd')
- order: str (default: 'market_cap_desc')
- per_page: int (default: 200)
- page: int (default: 1)
- sparkline: bool (default: True)
```

2. **Historical Data**
```python
GET /coins/{id}/market_chart
Parameters:
- vs_currency: str (default: 'usd')
- days: int (required)
- interval: str (optional)
```

3. **Global Data**
```python
GET /global
Response:
{
    "active_cryptocurrencies": int,
    "total_market_cap": dict,
    "total_volume": dict,
    "market_cap_percentage": dict
}
```

#### Rate Limits
- Free Tier: 50 calls/minute
- Pro Tier: 500 calls/minute

### Claude API

#### Authentication
```python
headers = {
    'x-api-key': 'your_anthropic_key',
    'content-type': 'application/json'
}
```

#### Usage
```python
from anthropic import Anthropic

client = Anthropic(api_key='your_key')
response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    temperature=0,
    system="Crypto market analysis context",
    messages=[{"role": "user", "content": "Analysis prompt"}]
)
```

## Internal APIs

### Data Collection API

#### Market Data Collection
```python
async def get_market_data(
    days: int = 90,
    top_n: int = 200
) -> pd.DataFrame:
    """
    Fetch market data for top N cryptocurrencies
    
    Parameters:
        days (int): Historical data days
        top_n (int): Number of top cryptocurrencies
        
    Returns:
        pd.DataFrame: Market data
    """
```

#### Volume Profile Analysis
```python
async def analyze_volume_profile(
    coin_id: str,
    timeframe: str = '1d'
) -> Dict:
    """
    Analyze trading volume patterns
    
    Parameters:
        coin_id (str): Cryptocurrency identifier
        timeframe (str): Analysis timeframe
        
    Returns:
        Dict: Volume analysis metrics
    """
```

### Analysis API

#### Tier Classification
```python
def classify_tiers(
    market_data: pd.DataFrame,
    num_tiers: int = 4
) -> pd.DataFrame:
    """
    Classify cryptocurrencies into market tiers
    
    Parameters:
        market_data (pd.DataFrame): Market data
        num_tiers (int): Number of tiers
        
    Returns:
        pd.DataFrame: Data with tier assignments
    """
```

#### Rotation Detection
```python
async def detect_rotations(
    tiered_data: pd.DataFrame,
    lookback_periods: int = 30
) -> List[RotationSignal]:
    """
    Detect capital rotation between tiers
    
    Parameters:
        tiered_data (pd.DataFrame): Tiered market data
        lookback_periods (int): Analysis lookback
        
    Returns:
        List[RotationSignal]: Detected rotation signals
    """
```

### Backtesting API

#### Strategy Testing
```python
async def backtest_strategy(
    market_data: pd.DataFrame,
    signals: List[RotationSignal],
    initial_capital: float = 100000.0
) -> Dict:
    """
    Backtest trading strategy
    
    Parameters:
        market_data (pd.DataFrame): Historical data
        signals (List[RotationSignal]): Trading signals
        initial_capital (float): Starting capital
        
    Returns:
        Dict: Backtest results and metrics
    """
```

## Rate Limits

### Internal Rate Limiting
```python
class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        
    async def acquire(self):
        now = time.time()
        # Clean old requests
        self.requests = [req for req in self.requests 
                        if now - req < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.time_window - now
            await asyncio.sleep(sleep_time)
            
        self.requests.append(now)
```

## Authentication

### API Key Management
```python
class APIKeyManager:
    def __init__(self):
        self.keys = {
            'coingecko': os.getenv('COINGECKO_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }
        
    def get_headers(self, api: str) -> Dict:
        """Get headers for specified API"""
        if api == 'coingecko':
            return {
                'X-Cg-Pro-Api-Key': self.keys['coingecko'],
                'Accept': 'application/json'
            }
        elif api == 'anthropic':
            return {
                'x-api-key': self.keys['anthropic'],
                'content-type': 'application/json'
            }
```

## Error Handling

### Error Types
```python
class APIError(Exception):
    """Base API Error"""
    pass

class RateLimitError(APIError):
    """Rate Limit Exceeded"""
    pass

class AuthenticationError(APIError):
    """Authentication Failed"""
    pass

class DataValidationError(APIError):
    """Data Validation Failed"""
    pass
```

### Error Handling Implementation
```python
async def handle_api_error(error: Exception) -> None:
    """Handle API errors with appropriate responses"""
    if isinstance(error, RateLimitError):
        await asyncio.sleep(60)  # Wait for rate limit reset
    elif isinstance(error, AuthenticationError):
        # Refresh authentication
        await refresh_auth()
    elif isinstance(error, DataValidationError):
        # Log error and use fallback data
        logger.error(f"Data validation failed: {str(error)}")
        return get_fallback_data()
```

## Examples

### Complete Data Collection Example
```python
async def collect_market_data():
    try:
        api = CoinGeckoAPI()
        rate_limiter = RateLimiter(max_requests=45, time_window=60)
        
        # Fetch market data
        await rate_limiter.acquire()
        market_data = await api.get_historical_data(days=90)
        
        # Process data
        processed_data = process_market_data(market_data)
        
        return processed_data
        
    except APIError as e:
        await handle_api_error(e)
```

### Analysis Pipeline Example
```python
async def run_analysis_pipeline(market_data: pd.DataFrame):
    try:
        # Initialize components
        detector = RotationDetector()
        analyzer = SmartMoneyAnalyzer()
        
        # Run analysis
        tiered_data = detector.identify_tiers(market_data)
        signals = await detector.generate_rotation_signals(tiered_data)
        smart_money = await analyzer.detect_patterns(tiered_data)
        
        return {
            'tiered_data': tiered_data,
            'signals': signals,
            'smart_money': smart_money
        }
        
    except Exception as e:
        logger.error(f"Analysis pipeline error: {str(e)}")
        raise
```

## Best Practices

1. **Rate Limiting**
   - Implement exponential backoff
   - Use request queuing
   - Cache responses

2. **Error Handling**
   - Implement retries
   - Log all errors
   - Use fallback data

3. **Data Validation**
   - Validate all responses
   - Check data types
   - Handle missing data

4. **Authentication**
   - Rotate API keys
   - Secure key storage
   - Monitor usage

## Support

For API support and questions:
1. Check the error logs
2. Review rate limits
3. Validate API keys
4. Contact support team

Remember to always handle API calls with proper error handling and rate limiting to ensure stable system operation.
