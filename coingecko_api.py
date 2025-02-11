import aiohttp
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..config.settings import COINGECKO_BASE_URL, COINGECKO_API_KEY

logger = logging.getLogger(__name__)

class CoinGeckoAPI:
    def __init__(self):
        self.base_url = COINGECKO_BASE_URL
        self.session = None
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if COINGECKO_API_KEY:
            self.headers['X-Cg-Pro-Api-Key'] = COINGECKO_API_KEY

    async def _init_session(self):
        """Initialize aiohttp session if not exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_historical_data(self, days: int = 90, top_n: int = 200) -> pd.DataFrame:
        """
        Fetch historical data for top N cryptocurrencies
        
        Parameters:
            days (int): Number of days of historical data
            top_n (int): Number of top cryptocurrencies to fetch
            
        Returns:
            pd.DataFrame: Historical market data
        """
        await self._init_session()
        
        try:
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': top_n,
                'sparkline': True,
                'price_change_percentage': '24h,7d,30d'
            }

            async with self.session.get(f"{self.base_url}/coins/markets", params=params) as response:
                if response.status != 200:
                    logger.error(f"Error fetching data: {await response.text()}")
                    return pd.DataFrame()
                    
                data = await response.json()
            
            df = pd.DataFrame(data)
            
            # Add timestamp and calculate metrics
            df['timestamp'] = datetime.now()
            df['volume_to_mcap'] = df['total_volume'] / df['market_cap']
            df['volatility'] = df['price_change_percentage_24h'].abs()
            
            return df
            
        except Exception as e:
            logger.error(f"Error in get_historical_data: {str(e)}")
            raise

    async def get_market_chart(self, coin_id: str, days: int = 90) -> pd.DataFrame:
        """
        Fetch detailed market chart data for a specific coin
        
        Parameters:
            coin_id (str): CoinGecko coin ID
            days (int): Number of days of historical data
            
        Returns:
            pd.DataFrame: Detailed market data for the coin
        """
        await self._init_session()
        
        try:
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }

            async with self.session.get(f"{self.base_url}/coins/{coin_id}/market_chart", 
                                      params=params) as response:
                if response.status != 200:
                    logger.error(f"Error fetching market chart: {await response.text()}")
                    return pd.DataFrame()
                    
                data = await response.json()
            
            # Process timestamps and create DataFrame
            prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            market_caps = pd.DataFrame(data['market_caps'], columns=['timestamp', 'market_cap'])
            volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
            
            # Merge all data and convert timestamps
            df = prices.merge(market_caps, on='timestamp').merge(volumes, on='timestamp')
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logger.error(f"Error in get_market_chart: {str(e)}")
            raise

    async def get_global_data(self) -> Dict:
        """
        Fetch global crypto market data
        
        Returns:
            Dict: Global market metrics
        """
        await self._init_session()
        
        try:
            async with self.session.get(f"{self.base_url}/global") as response:
                if response.status != 200:
                    logger.error(f"Error fetching global data: {await response.text()}")
                    return {}
                    
                return await response.json()
                
        except Exception as e:
            logger.error(f"Error in get_global_data: {str(e)}")
            raise

    async def __aenter__(self):
        """Context manager entry"""
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
