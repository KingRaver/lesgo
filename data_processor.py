import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging
from scipy import stats
from ..config.settings import ANALYSIS_PARAMS

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Handles all data processing operations for cryptocurrency market data.
    This class implements methods for cleaning, transforming, and enriching
    raw market data with additional metrics and indicators.
    """
    
    def __init__(self):
        self.required_columns = [
            'id', 'symbol', 'name', 'market_cap', 'current_price',
            'total_volume', 'price_change_percentage_24h'
        ]

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validates the input DataFrame for required columns and data quality.
        
        Parameters:
            df (pd.DataFrame): Raw market data
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        # Check for required columns
        missing_columns = [col for col in self.required_columns 
                         if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
            
        # Check for null values in critical columns
        null_counts = df[self.required_columns].isnull().sum()
        if null_counts.any():
            logger.warning(f"Null values found in columns: \n{null_counts[null_counts > 0]}")
            
        return True

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the input data by handling missing values and removing duplicates.
        
        Parameters:
            df (pd.DataFrame): Raw market data
            
        Returns:
            pd.DataFrame: Cleaned market data
        """
        cleaned = df.copy()
        
        # Remove duplicates
        initial_rows = len(cleaned)
        cleaned = cleaned.drop_duplicates(subset=['id', 'timestamp'])
        if len(cleaned) < initial_rows:
            logger.info(f"Removed {initial_rows - len(cleaned)} duplicate rows")
            
        # Handle missing values
        for col in self.required_columns:
            if cleaned[col].isnull().any():
                if col in ['market_cap', 'total_volume', 'current_price']:
                    # For numerical columns, use ffill then bfill
                    cleaned[col] = cleaned[col].ffill().bfill()
                else:
                    # For categorical columns, use mode
                    cleaned[col] = cleaned[col].fillna(cleaned[col].mode()[0])
                    
        return cleaned

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates additional market metrics and indicators.
        
        Parameters:
            df (pd.DataFrame): Cleaned market data
            
        Returns:
            pd.DataFrame: Enhanced market data with additional metrics
        """
        enhanced = df.copy()
        
        # Calculate volume-based metrics
        enhanced['volume_to_mcap'] = enhanced['total_volume'] / enhanced['market_cap']
        enhanced['volume_zscore'] = stats.zscore(enhanced['total_volume'])
        
        # Calculate volatility metrics
        enhanced['volatility'] = enhanced.groupby('id')['current_price'].pct_change().rolling(
            window=24).std() * np.sqrt(365)
            
        # Calculate relative strength
        enhanced['relative_strength'] = enhanced.groupby('id')['current_price'].pct_change(
        ).div(enhanced['price_change_percentage_24h'].mean())
        
        # Calculate market dominance per timestamp
        enhanced['market_dominance'] = enhanced.groupby('timestamp').apply(
            lambda x: x['market_cap'] / x['market_cap'].sum() * 100
        ).reset_index(level=0, drop=True)
        
        return enhanced

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detects anomalies in market data using statistical methods.
        
        Parameters:
            df (pd.DataFrame): Market data with calculated metrics
            
        Returns:
            pd.DataFrame: Data with anomaly flags
        """
        data = df.copy()
        
        # Volume anomalies (using modified z-score for robustness)
        median_volume = data['total_volume'].median()
        mad_volume = stats.median_abs_deviation(data['total_volume'])
        
        data['volume_anomaly'] = np.abs(
            0.6745 * (data['total_volume'] - median_volume) / mad_volume
        ) > 3.5
        
        # Price movement anomalies
        data['price_anomaly'] = np.abs(
            data['price_change_percentage_24h']
        ) > data['price_change_percentage_24h'].std() * 3
        
        # Market cap anomalies
        data['mcap_anomaly'] = np.abs(
            data.groupby('id')['market_cap'].pct_change()
        ) > 0.2  # 20% market cap change
        
        return data

    def prepare_for_analysis(self, 
                           df: pd.DataFrame,
                           lookback_periods: int = 30) -> pd.DataFrame:
        """
        Prepares data for tier analysis by calculating necessary metrics
        and ensuring data quality.
        
        Parameters:
            df (pd.DataFrame): Raw market data
            lookback_periods (int): Number of periods for rolling calculations
            
        Returns:
            pd.DataFrame: Processed data ready for analysis
        """
        # Validate input data
        if not self.validate_data(df):
            raise ValueError("Invalid input data structure")
            
        # Process data sequentially
        processed = self.clean_data(df)
        processed = self.calculate_metrics(processed)
        processed = self.detect_anomalies(processed)
        
        # Add timestamp if not present
        if 'timestamp' not in processed.columns:
            processed['timestamp'] = datetime.now()
            
        # Sort data
        processed = processed.sort_values(['timestamp', 'market_cap'], 
                                       ascending=[True, False])
        
        return processed

    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Generates summary statistics for the processed data.
        
        Parameters:
            df (pd.DataFrame): Processed market data
            
        Returns:
            Dict: Summary statistics
        """
        summary = {
            'total_market_cap': df['market_cap'].sum(),
            'total_volume': df['total_volume'].sum(),
            'avg_volatility': np.nanmean(df['volatility']),  # Handle NaN values
            'volume_anomalies': df['volume_anomaly'].sum(),
            'price_anomalies': df['price_anomaly'].sum(),
            'timestamp': datetime.now()
        }
        
        # Add tier-specific metrics if tiers are present
        if 'tier' in df.columns:
            for tier in df['tier'].unique():
                tier_data = df[df['tier'] == tier]
                summary[f'tier_{tier}_market_cap'] = tier_data['market_cap'].sum()
                summary[f'tier_{tier}_volume'] = tier_data['total_volume'].sum()
                
        return summary

    async def process_streaming_data(self, 
                                   data_stream: List[Dict],
                                   batch_size: int = 100) -> pd.DataFrame:
        """
        Processes streaming market data in batches.
        
        Parameters:
            data_stream (List[Dict]): Stream of market data
            batch_size (int): Size of processing batches
            
        Returns:
            pd.DataFrame: Processed streaming data
        """
        processed_batches = []
        current_batch = []
        
        for data_point in data_stream:
            current_batch.append(data_point)
            
            if len(current_batch) >= batch_size:
                # Process batch
                batch_df = pd.DataFrame(current_batch)
                processed_batch = self.prepare_for_analysis(batch_df)
                processed_batches.append(processed_batch)
                current_batch = []
                
        # Process remaining data
        if current_batch:
            batch_df = pd.DataFrame(current_batch)
            processed_batch = self.prepare_for_analysis(batch_df)
            processed_batches.append(processed_batch)
            
        return pd.concat(processed_batches, ignore_index=True)

    def export_processed_data(self, 
                            df: pd.DataFrame,
                            export_path: str,
                            format: str = 'csv') -> None:
        """
        Exports processed data to specified format.
        
        Parameters:
            df (pd.DataFrame): Processed data to export
            export_path (str): Path for export file
            format (str): Export format ('csv' or 'parquet')
        """
        try:
            if format.lower() == 'csv':
                df.to_csv(export_path, index=False)
            elif format.lower() == 'parquet':
                df.to_parquet(export_path, index=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
            logger.info(f"Successfully exported data to {export_path}")
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise
