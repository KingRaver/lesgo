import pytest
import pandas as pd
import numpy as np
import aiohttp
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.data.coingecko_api import CoinGeckoAPI

class AsyncContextManagerMock:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_session_initialization():
    """Test API session initialization"""
    api = CoinGeckoAPI()
    assert api.session is None
    await api._init_session()
    assert isinstance(api.session, aiohttp.ClientSession)
    assert 'Accept' in api.headers
    assert 'Content-Type' in api.headers
    await api.close()

@pytest.mark.asyncio
async def test_session_closure():
    """Test API session closure"""
    api = CoinGeckoAPI()
    await api._init_session()
    assert api.session is not None
    await api.close()
    assert api.session is None

@pytest.mark.asyncio
async def test_get_historical_data_success():
    """Test successful historical data retrieval"""
    mock_data = [{
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "market_cap": float(1000000000000),
        "current_price": float(50000),
        "total_volume": float(30000000000),
        "price_change_percentage_24h": 5.5,
        "sparkline_in_7d": {"price": [49000, 50000, 51000]},
        "price_change_percentage_7d_in_currency": 7.2,
        "price_change_percentage_30d_in_currency": 15.3
    }]

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_data

    async_cm = AsyncContextManagerMock(mock_response)
    mock_session = MagicMock()
    mock_session.get.return_value = async_cm

    api = CoinGeckoAPI()
    api.session = mock_session
    df = await api.get_historical_data(days=90, top_n=1)
    
    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'timestamp' in df.columns
    assert 'volume_to_mcap' in df.columns
    assert 'volatility' in df.columns
    
    # Verify data types (allow for numpy number types)
    assert isinstance(df['market_cap'].iloc[0], (int, float, np.integer, np.floating))
    assert isinstance(df['timestamp'].iloc[0], datetime)
    
    # Verify calculated metrics (convert to float for comparison)
    np.testing.assert_almost_equal(
        float(df['volume_to_mcap'].iloc[0]), 
        float(df['total_volume'].iloc[0]) / float(df['market_cap'].iloc[0])
    )

@pytest.mark.asyncio
async def test_get_historical_data_error():
    """Test error handling in historical data retrieval"""
    mock_response = AsyncMock()
    mock_response.status = 429
    mock_response.text.return_value = "Rate limit exceeded"

    async_cm = AsyncContextManagerMock(mock_response)
    mock_session = MagicMock()
    mock_session.get.return_value = async_cm

    api = CoinGeckoAPI()
    api.session = mock_session
    
    with pytest.raises(Exception) as exc_info:
        await api.get_historical_data()
    assert "429" in str(exc_info.value)
    assert "Rate limit" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_market_chart_success():
    """Test successful market chart data retrieval"""
    mock_chart_data = {
        "prices": [[1609459200000, 50000], [1609545600000, 51000]],
        "market_caps": [[1609459200000, 1000000000000], [1609545600000, 1020000000000]],
        "total_volumes": [[1609459200000, 30000000000], [1609545600000, 31000000000]]
    }

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_chart_data

    async_cm = AsyncContextManagerMock(mock_response)
    mock_session = MagicMock()
    mock_session.get.return_value = async_cm

    api = CoinGeckoAPI()
    api.session = mock_session
    df = await api.get_market_chart("bitcoin", days=1)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert all(col in df.columns for col in ['timestamp', 'price', 'market_cap', 'volume'])
    assert len(df) == 2  # Two data points in our mock data

@pytest.mark.asyncio
async def test_get_global_data_success():
    """Test successful global data retrieval"""
    mock_global_data = {
        "data": {
            "active_cryptocurrencies": 10000,
            "total_market_cap": {"usd": 2000000000000},
            "total_volume": {"usd": 100000000000},
            "market_cap_percentage": {"btc": 45, "eth": 20}
        }
    }

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_global_data

    async_cm = AsyncContextManagerMock(mock_response)
    mock_session = MagicMock()
    mock_session.get.return_value = async_cm

    api = CoinGeckoAPI()
    api.session = mock_session
    data = await api.get_global_data()
    assert isinstance(data, dict)
    assert "data" in data
    assert "active_cryptocurrencies" in data["data"]

@pytest.mark.asyncio
async def test_context_manager():
    """Test API context manager functionality"""
    async with CoinGeckoAPI() as api:
        assert isinstance(api.session, aiohttp.ClientSession)
    assert api.session is None

@pytest.mark.asyncio
async def test_api_headers():
    """Test API headers configuration"""
    with patch('src.data.coingecko_api.COINGECKO_API_KEY', 'test_key'):
        api = CoinGeckoAPI()
        assert 'X-Cg-Pro-Api-Key' in api.headers
        assert api.headers['X-Cg-Pro-Api-Key'] == 'test_key'

@pytest.mark.asyncio
async def test_rate_limit_handling():
    """Test handling of rate limit responses"""
    mock_response = AsyncMock()
    mock_response.status = 429
    mock_response.text.return_value = "Too many requests"

    async_cm = AsyncContextManagerMock(mock_response)
    mock_session = MagicMock()
    mock_session.get.return_value = async_cm

    api = CoinGeckoAPI()
    api.session = mock_session
    
    with pytest.raises(Exception) as exc_info:
        await api.get_market_chart("bitcoin")
    assert "429" in str(exc_info.value)
    assert "Rate limit" in str(exc_info.value)
