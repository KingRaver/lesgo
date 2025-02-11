import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.analysis.rotation_detector import RotationDetector, RotationSignal

@pytest.fixture
def sample_market_data():
    """Create sample market data for testing"""
    # Create timestamp range
    dates = pd.date_range(start='2025-01-01', periods=10, freq='D')
    
    # Generate sample data
    data = []
    for date in dates:
        # Create entries for different market cap tiers
        for i in range(20):  # 20 coins
            data.append({
                'id': f'coin_{i}',
                'symbol': f'COIN{i}',
                'timestamp': date,
                'market_cap': 10_000_000_000 / (i + 1),  # Descending market caps
                'total_volume': 1_000_000_000 / (i + 1),
                'current_price': 1000 / (i + 1),
                'price_change_percentage_24h': np.random.normal(0, 5),
                'volume_to_mcap': np.random.uniform(0.05, 0.15)
            })
    
    return pd.DataFrame(data)

@pytest.fixture
def detector():
    """Create RotationDetector instance"""
    return RotationDetector()

def test_identify_tiers(detector, sample_market_data):
    """Test tier identification functionality"""
    tiered_data = detector.identify_tiers(sample_market_data)
    
    # Check if tiers are assigned
    assert 'tier' in tiered_data.columns
    
    # Check if we have the expected number of tiers
    unique_tiers = tiered_data['tier'].unique()
    assert len(unique_tiers) == 4
    
    # Check if tiers are properly ordered (0 should be highest market cap)
    highest_mcap_tier = tiered_data.nlargest(1, 'market_cap')['tier'].iloc[0]
    assert highest_mcap_tier == 0

def test_calculate_tier_metrics(detector, sample_market_data):
    """Test tier metrics calculation"""
    tiered_data = detector.identify_tiers(sample_market_data)
    tier_metrics = detector.calculate_tier_metrics(tiered_data)
    
    # Check if metrics exist for each tier
    for tier in range(4):
        assert tier in tier_metrics
        assert 'avg_volume' in tier_metrics[tier]
        assert 'avg_mcap' in tier_metrics[tier]
        assert 'volatility' in tier_metrics[tier]

def test_detect_volume_anomalies(detector, sample_market_data):
    """Test volume anomaly detection"""
    tiered_data = detector.identify_tiers(sample_market_data)
    anomalies = detector.detect_volume_anomalies(tiered_data)
    
    # Check if anomalies are detected for each tier
    assert len(anomalies) == 4
    assert all(isinstance(v, (int, float)) for v in anomalies.values())

def test_calculate_tier_correlations(detector, sample_market_data):
    """Test tier correlation calculation"""
    tiered_data = detector.identify_tiers(sample_market_data)
    correlations = detector.calculate_tier_correlations(tiered_data)
    
    # Check correlation matrix properties
    assert correlations.shape == (4, 4)  # 4x4 matrix for 4 tiers
    assert (correlations.values[range(4), range(4)] == 1.0).all()  # Diagonal should be 1.0
    assert (correlations >= -1.0).all().all() and (correlations <= 1.0).all().all()

def test_generate_rotation_signals(detector, sample_market_data):
    """Test rotation signal generation"""
    signals = detector.generate_rotation_signals(sample_market_data)
    
    # Check if signals are generated
    assert isinstance(signals, list)
    
    # If signals are generated, check their properties
    for signal in signals:
        assert isinstance(signal, RotationSignal)
        assert 0 <= signal.from_tier <= 3
        assert 0 <= signal.to_tier <= 3
        assert 0 <= signal.confidence <= 1
        assert isinstance(signal.timestamp, datetime)

def test_signal_confidence_threshold(detector, sample_market_data):
    """Test if signals meet minimum confidence threshold"""
    signals = detector.generate_rotation_signals(sample_market_data)
    
    for signal in signals:
        assert signal.confidence >= detector.min_confidence

def test_invalid_data_handling(detector):
    """Test handling of invalid input data"""
    # Empty DataFrame
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError):
        detector.identify_tiers(empty_df)
    
    # Missing required columns
    invalid_df = pd.DataFrame({
        'id': ['coin_1'],
        'timestamp': [datetime.now()]
    })
    with pytest.raises(ValueError):
        detector.identify_tiers(invalid_df)

def test_tier_stability(detector, sample_market_data):
    """Test stability of tier assignments across time periods"""
    # Split data into two time periods
    mid_point = sample_market_data['timestamp'].median()
    period1 = sample_market_data[sample_market_data['timestamp'] < mid_point]
    period2 = sample_market_data[sample_market_data['timestamp'] >= mid_point]
    
    # Get tier assignments for both periods
    tiers1 = detector.identify_tiers(period1)
    tiers2 = detector.identify_tiers(period2)
    
    # Check if high market cap coins remain in top tier
    top_coins = tiers1[tiers1['tier'] == 0]['id'].unique()
    top_coins2 = tiers2[tiers2['tier'] == 0]['id'].unique()
    
    # Should have some overlap in top tier
    assert len(set(top_coins) & set(top_coins2)) > 0

@pytest.mark.parametrize("threshold", [0.5, 0.7, 0.9])
def test_different_confidence_thresholds(detector, sample_market_data, threshold):
    """Test signal generation with different confidence thresholds"""
    detector.min_confidence = threshold
    signals = detector.generate_rotation_signals(sample_market_data)
    
    # All signals should meet or exceed the threshold
    assert all(signal.confidence >= threshold for signal in signals)

def test_performance_large_dataset():
    """Test performance with larger dataset"""
    # Generate large dataset
    large_data = []
    for i in range(100):  # 100 days
        for j in range(200):  # 200 coins
            large_data.append({
                'id': f'coin_{j}',
                'symbol': f'COIN{j}',
                'timestamp': datetime.now() - timedelta(days=i),
                'market_cap': 10_000_000_000 / (j + 1),
                'total_volume': 1_000_000_000 / (j + 1),
                'current_price': 1000 / (j + 1),
                'price_change_percentage_24h': np.random.normal(0, 5),
                'volume_to_mcap': np.random.uniform(0.05, 0.15)
            })
    
    large_df = pd.DataFrame(large_data)
    detector = RotationDetector()
    
    # Test processing time
    import time
    start_time = time.time()
    signals = detector.generate_rotation_signals(large_df)
    processing_time = time.time() - start_time
    
    # Should process in reasonable time (adjust threshold as needed)
    assert processing_time < 30  # seconds

if __name__ == '__main__':
    pytest.main([__file__])
