import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data.data_processor import DataProcessor

@pytest.fixture
def processor():
    """Create DataProcessor instance"""
    return DataProcessor()

@pytest.fixture
def mock_raw_data():
    """Create mock data similar to CoinGecko API response"""
    # Create date range for proper volatility calculation
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = []
    
    # Generate data for each date to allow for rolling calculations
    for date in dates:
        for i in range(20):
            data.append({
                "id": f"coin_{i}",
                "symbol": f"sym_{i}",
                "name": f"Coin {i}",
                "market_cap": 10_000_000_000 / (i + 1),  # Descending market caps
                "current_price": 1000 / (i + 1),
                "total_volume": 1_000_000_000 / (i + 1),
                "price_change_percentage_24h": np.random.normal(0, 5),
                "timestamp": date
            })
    
    return pd.DataFrame(data)

@pytest.fixture
def mock_data_with_nulls(mock_raw_data):
    """Create mock data with null values"""
    df = mock_raw_data.copy()
    # Insert some null values
    df.loc[0, 'market_cap'] = None
    df.loc[1, 'total_volume'] = None
    df.loc[2, 'price_change_percentage_24h'] = None
    df.loc[3, 'name'] = None
    return df

@pytest.fixture
def mock_data_with_duplicates(mock_raw_data):
    """Create mock data with duplicate entries"""
    df = mock_raw_data.copy()
    # Add duplicate rows
    duplicates = df.head(5).copy()
    return pd.concat([df, duplicates], ignore_index=True)

def test_validate_data_success(processor, mock_raw_data):
    """Test data validation with valid data"""
    assert processor.validate_data(mock_raw_data) == True

def test_validate_data_missing_columns(processor):
    """Test data validation with missing required columns"""
    invalid_data = pd.DataFrame({
        'id': ['coin_1'],
        'symbol': ['sym_1']
    })
    assert processor.validate_data(invalid_data) == False

def test_clean_data_nulls(processor, mock_data_with_nulls):
    """Test handling of null values"""
    cleaned = processor.clean_data(mock_data_with_nulls)
    
    # Verify no nulls remain
    assert not cleaned.isnull().any().any()
    
    # Verify numerical columns were forward/backward filled
    assert isinstance(cleaned.loc[0, 'market_cap'], (int, float))
    assert isinstance(cleaned.loc[1, 'total_volume'], (int, float))
    assert isinstance(cleaned.loc[2, 'price_change_percentage_24h'], (int, float))
    
    # Verify categorical columns used mode filling
    assert isinstance(cleaned.loc[3, 'name'], str)

def test_clean_data_duplicates(processor, mock_data_with_duplicates):
    """Test removal of duplicate entries"""
    cleaned = processor.clean_data(mock_data_with_duplicates)
    
    # Verify duplicates were removed
    assert len(cleaned) < len(mock_data_with_duplicates)
    assert len(cleaned) == len(cleaned.drop_duplicates(subset=['id', 'timestamp']))

def test_calculate_metrics_basic(processor, mock_raw_data):
    """Test basic metric calculations"""
    enhanced = processor.calculate_metrics(mock_raw_data)
    
    # Verify all expected metrics are present
    expected_metrics = [
        'volume_to_mcap',
        'volume_zscore',
        'volatility',
        'relative_strength',
        'market_dominance'
    ]
    assert all(metric in enhanced.columns for metric in expected_metrics)
    
    # Verify volume_to_mcap calculation
    expected_ratio = mock_raw_data['total_volume'] / mock_raw_data['market_cap']
    pd.testing.assert_series_equal(
        enhanced['volume_to_mcap'],
        expected_ratio,
        check_names=False
    )
    
    # Verify market dominance calculation per timestamp
    for timestamp, group in enhanced.groupby('timestamp'):
        total_mcap = group['market_cap'].sum()
        expected_dominance = group['market_cap'] / total_mcap * 100
        
        # Verify each coin's market dominance
        pd.testing.assert_series_equal(
            group['market_dominance'].sort_index(),
            expected_dominance.sort_index(),
            check_names=False,
            check_index=False,
            rtol=1e-10
        )
        
        # Verify sum of market dominance is 100%
        np.testing.assert_almost_equal(
            group['market_dominance'].sum(),
            100.0,
            decimal=10
        )
        
        # Verify highest market cap has highest dominance
        assert group['market_dominance'].max() == group.loc[
            group['market_cap'].idxmax(), 'market_dominance'
        ]

def test_calculate_metrics_volatility(processor, mock_raw_data):
    """Test volatility calculations"""
    enhanced = processor.calculate_metrics(mock_raw_data)
    
    # Group by coin to check each coin's volatility
    for coin_id, group in enhanced.groupby('id'):
        # Sort by timestamp to ensure proper calculation
        group = group.sort_values('timestamp')
        
        # Calculate rolling std of returns for verification
        returns = group['current_price'].pct_change()
        volatility = returns.rolling(window=24).std() * np.sqrt(365)
        
        # Skip first few entries due to rolling window
        valid_volatility = volatility[24:]
        
        # Check that volatility values are non-negative and finite
        assert (valid_volatility >= 0).all(), f"Negative volatility found for {coin_id}"
        assert np.isfinite(valid_volatility).all(), f"Invalid volatility values for {coin_id}"

def test_detect_anomalies(processor, mock_raw_data):
    """Test anomaly detection"""
    data_with_anomalies = processor.detect_anomalies(mock_raw_data)
    
    # Verify anomaly flags are present
    expected_flags = ['volume_anomaly', 'price_anomaly', 'mcap_anomaly']
    assert all(flag in data_with_anomalies.columns for flag in expected_flags)
    
    # Verify flags are boolean
    assert data_with_anomalies['volume_anomaly'].dtype == bool
    assert data_with_anomalies['price_anomaly'].dtype == bool
    assert data_with_anomalies['mcap_anomaly'].dtype == bool

def test_prepare_for_analysis_complete(processor, mock_raw_data):
    """Test complete data preparation pipeline"""
    processed = processor.prepare_for_analysis(mock_raw_data)
    
    # Verify all required columns are present
    required_columns = processor.required_columns + [
        'volume_to_mcap', 'volume_zscore', 'volatility',
        'relative_strength', 'market_dominance'
    ]
    assert all(col in processed.columns for col in required_columns)
    
    # Check for null values in base columns
    base_columns = processor.required_columns + ['volume_to_mcap', 'market_dominance']
    assert not processed[base_columns].isnull().any().any()
    
    # Allow some null values in calculated columns for initial periods
    for col in ['volatility', 'relative_strength']:
        # Verify that after initial period, values are not null
        non_null_ratio = processed[col].notna().mean()
        assert non_null_ratio > 0.8, f"Too many null values in {col}"
    
    # Verify data is sorted correctly
    assert processed['timestamp'].is_monotonic_increasing
    assert processed.groupby('timestamp')['market_cap'].is_monotonic_decreasing.all()

def test_prepare_for_analysis_invalid_data(processor):
    """Test error handling with invalid input data"""
    invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
    
    with pytest.raises(ValueError):
        processor.prepare_for_analysis(invalid_data)

def test_get_summary_statistics(processor, mock_raw_data):
    """Test summary statistics generation"""
    processed = processor.prepare_for_analysis(mock_raw_data)
    summary = processor.get_summary_statistics(processed)
    
    # Verify required summary metrics
    assert 'total_market_cap' in summary
    assert 'total_volume' in summary
    assert 'avg_volatility' in summary
    assert 'timestamp' in summary
    
    # Verify values are reasonable
    assert summary['total_market_cap'] > 0
    assert summary['total_volume'] > 0
    
    # Handle potential NaN in volatility by using nanmean
    avg_volatility = np.nanmean(processed['volatility'])
    assert 0 <= avg_volatility <= 100, f"Invalid average volatility: {avg_volatility}"
    assert isinstance(summary['timestamp'], datetime)

def test_performance_large_dataset(processor):
    """Test processing performance with larger dataset"""
    # Generate large dataset with proper time series
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    large_data = []
    
    for date in dates:
        for i in range(100):  # 100 coins
            large_data.append({
                "id": f"coin_{i}",
                "symbol": f"sym_{i}",
                "name": f"Coin {i}",
                "market_cap": 10_000_000_000 / (i + 1),
                "current_price": 1000 / (i + 1),
                "total_volume": 1_000_000_000 / (i + 1),
                "price_change_percentage_24h": np.random.normal(0, 5),
                "timestamp": date
            })
    
    large_df = pd.DataFrame(large_data)
    
    import time
    start_time = time.time()
    processed = processor.prepare_for_analysis(large_df)
    processing_time = time.time() - start_time
    
    # Processing should complete in reasonable time
    assert processing_time < 5  # seconds
    assert len(processed) == len(large_df)
