import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..config.settings import ANALYSIS_PARAMS, TIER_PARAMS

@dataclass
class RotationSignal:
    timestamp: datetime
    from_tier: int
    to_tier: int
    confidence: float
    signal_type: str
    metrics: Dict[str, float]

class RotationDetector:
    def __init__(self, lookback_periods: int = 30):
        self.lookback_periods = lookback_periods
        self.volume_threshold = ANALYSIS_PARAMS['volume_threshold']
        self.correlation_threshold = ANALYSIS_PARAMS['correlation_threshold']
        self.min_confidence = ANALYSIS_PARAMS['min_confidence']

    def identify_tiers(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        Identify market tiers based on market cap and other metrics
        
        Parameters:
            market_data (pd.DataFrame): Market data with required metrics
            
        Returns:
            pd.DataFrame: Market data with tier assignments
        """
        df = market_data.copy()
        
        # Calculate tier boundaries based on market cap
        mcap_log = np.log10(df['market_cap'])
        tier_boundaries = np.percentile(mcap_log, [25, 50, 75])
        
        # Assign tiers (0 = highest, 3 = lowest)
        df['tier'] = 3  # Default to lowest tier
        for i, boundary in enumerate(reversed(tier_boundaries)):
            df.loc[mcap_log >= boundary, 'tier'] = i
            
        return df

    def calculate_tier_metrics(self, tiered_data: pd.DataFrame) -> Dict[int, Dict]:
        """
        Calculate key metrics for each tier
        
        Parameters:
            tiered_data (pd.DataFrame): Market data with tier assignments
            
        Returns:
            Dict[int, Dict]: Metrics for each tier
        """
        tier_metrics = {}
        
        for tier in range(4):
            tier_data = tiered_data[tiered_data['tier'] == tier]
            
            metrics = {
                'avg_volume': tier_data['total_volume'].mean(),
                'avg_mcap': tier_data['market_cap'].mean(),
                'volatility': tier_data['price_change_percentage_24h'].std(),
                'volume_mcap_ratio': (tier_data['total_volume'] / tier_data['market_cap']).mean(),
                'assets_count': len(tier_data)
            }
            
            tier_metrics[tier] = metrics
            
        return tier_metrics

    def detect_volume_anomalies(self, tiered_data: pd.DataFrame) -> Dict[int, float]:
        """
        Detect unusual volume patterns in each tier
        
        Parameters:
            tiered_data (pd.DataFrame): Market data with tier assignments
            
        Returns:
            Dict[int, float]: Volume anomaly scores by tier
        """
        anomalies = {}
        
        for tier in range(4):
            tier_data = tiered_data[tiered_data['tier'] == tier]
            
            if not tier_data.empty:
                # Calculate volume Z-scores
                volume_zscore = stats.zscore(tier_data['total_volume'])
                anomalies[tier] = float(np.mean(volume_zscore))
            else:
                anomalies[tier] = 0.0
                
        return anomalies

    def calculate_tier_correlations(self, tiered_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate price correlations between tiers
        
        Parameters:
            tiered_data (pd.DataFrame): Market data with tier assignments
            
        Returns:
            pd.DataFrame: Correlation matrix between tiers
        """
        correlations = pd.DataFrame(index=range(4), columns=range(4))
        
        for tier1 in range(4):
            for tier2 in range(4):
                if tier1 != tier2:
                    tier1_returns = tiered_data[tiered_data['tier'] == tier1]['price_change_percentage_24h']
                    tier2_returns = tiered_data[tiered_data['tier'] == tier2]['price_change_percentage_24h']
                    
                    if not tier1_returns.empty and not tier2_returns.empty:
                        correlation = tier1_returns.corr(tier2_returns)
                        correlations.loc[tier1, tier2] = correlation
                else:
                    correlations.loc[tier1, tier2] = 1.0
                    
        return correlations

    def generate_rotation_signals(self, market_data: pd.DataFrame) -> List[RotationSignal]:
        """
        Generate rotation signals based on market data analysis
        
        Parameters:
            market_data (pd.DataFrame): Market data to analyze
            
        Returns:
            List[RotationSignal]: Detected rotation signals
        """
        signals = []
        
        # Identify tiers and calculate metrics
        tiered_data = self.identify_tiers(market_data)
        tier_metrics = self.calculate_tier_metrics(tiered_data)
        volume_anomalies = self.detect_volume_anomalies(tiered_data)
        correlations = self.calculate_tier_correlations(tiered_data)
        
        # Detect rotations between tiers
        for from_tier in range(4):
            for to_tier in range(4):
                if from_tier != to_tier:
                    # Calculate confidence factors
                    volume_factor = volume_anomalies[to_tier] - volume_anomalies[from_tier]
                    correlation_factor = correlations.loc[from_tier, to_tier]
                    relative_strength = (
                        tier_metrics[to_tier]['volume_mcap_ratio'] / 
                        tier_metrics[from_tier]['volume_mcap_ratio']
                    )
                    
                    # Calculate overall confidence
                    confidence = np.mean([
                        volume_factor,
                        correlation_factor,
                        relative_strength
                    ])
                    
                    # Generate signal if confidence threshold is met
                    if confidence > self.min_confidence:
                        signals.append(RotationSignal(
                            timestamp=datetime.now(),
                            from_tier=from_tier,
                            to_tier=to_tier,
                            confidence=float(confidence),
                            signal_type='tier_rotation',
                            metrics={
                                'volume_factor': float(volume_factor),
                                'correlation': float(correlation_factor),
                                'relative_strength': float(relative_strength)
                            }
                        ))
        
        return signals
