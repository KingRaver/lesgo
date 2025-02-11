import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..config.settings import ANALYSIS_PARAMS

@dataclass
class SmartMoneySignal:
    timestamp: datetime
    coin_id: str
    signal_type: str
    strength: float
    metrics: Dict[str, float]

class SmartMoneyAnalyzer:
    def __init__(self, lookback_periods: int = 14):
        self.lookback_periods = lookback_periods
        self.min_confidence = ANALYSIS_PARAMS['min_confidence']

    def calculate_accumulation_distribution(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Accumulation/Distribution Line
        
        Parameters:
            df (pd.DataFrame): Price and volume data with high, low, close columns
            
        Returns:
            pd.Series: A/D Line values
        """
        # Money Flow Multiplier
        mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mfm = mfm.replace([np.inf, -np.inf], 0)
        
        # Money Flow Volume
        mfv = mfm * df['volume']
        
        # Accumulation/Distribution Line
        ad_line = mfv.cumsum()
        return ad_line

    def calculate_on_balance_volume(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV)
        
        Parameters:
            df (pd.DataFrame): Price and volume data
            
        Returns:
            pd.Series: OBV values
        """
        price_change = df['close'].diff()
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['volume'].iloc[0]
        
        for i in range(1, len(df)):
            if price_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif price_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
                
        return obv

    def detect_large_transactions(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect unusually large transactions
        
        Parameters:
            df (pd.DataFrame): Trading data
            
        Returns:
            pd.Series: Binary indicator of large transactions
        """
        # Calculate average transaction size
        avg_transaction = df['volume'] / df['market_cap']
        
        # Define threshold for large transactions (2 standard deviations)
        threshold = avg_transaction.mean() + (2 * avg_transaction.std())
        
        return (avg_transaction > threshold).astype(float)

    def calculate_smart_money_flow(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Smart Money Flow Index
        
        Parameters:
            df (pd.DataFrame): Market data
            
        Returns:
            pd.Series: Smart Money Flow values
        """
        # Get components
        ad_line = self.calculate_accumulation_distribution(df)
        obv = self.calculate_on_balance_volume(df)
        large_tx = self.detect_large_transactions(df)
        
        # Normalize components
        ad_norm = (ad_line - ad_line.mean()) / ad_line.std()
        obv_norm = (obv - obv.mean()) / obv.std()
        
        # Combine indicators with weights
        smart_money_flow = (0.4 * ad_norm + 0.4 * obv_norm + 0.2 * large_tx)
        return smart_money_flow

    def detect_accumulation_distribution_patterns(self, df: pd.DataFrame) -> List[SmartMoneySignal]:
        """
        Detect accumulation/distribution patterns
        
        Parameters:
            df (pd.DataFrame): Market data
            
        Returns:
            List[SmartMoneySignal]: Detected smart money signals
        """
        signals = []
        smart_money_flow = self.calculate_smart_money_flow(df)
        
        # Look for significant changes in smart money flow
        flow_change = smart_money_flow.diff(self.lookback_periods)
        flow_std = smart_money_flow.rolling(self.lookback_periods).std()
        
        # Generate signals for significant movements
        for i in range(self.lookback_periods, len(df)):
            flow_zscore = flow_change.iloc[i] / flow_std.iloc[i]
            
            if abs(flow_zscore) > 2:  # Significant movement
                signal_type = 'accumulation' if flow_zscore > 0 else 'distribution'
                strength = abs(flow_zscore) / 4  # Normalize to 0-1 range
                
                signals.append(SmartMoneySignal(
                    timestamp=df.index[i],
                    coin_id=df['coin_id'].iloc[i],
                    signal_type=signal_type,
                    strength=float(strength),
                    metrics={
                        'smart_money_flow': float(smart_money_flow.iloc[i]),
                        'flow_change': float(flow_change.iloc[i]),
                        'flow_zscore': float(flow_zscore)
                    }
                ))
        
        return signals

    def analyze_volume_profile(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze volume profile for smart money characteristics
        
        Parameters:
            df (pd.DataFrame): Market data
            
        Returns:
            Dict[str, float]: Volume profile metrics
        """
        metrics = {
            'large_tx_ratio': float(self.detect_large_transactions(df).mean()),
            'volume_concentration': float(df['volume'].std() / df['volume'].mean()),
            'smart_money_flow_strength': float(self.calculate_smart_money_flow(df).iloc[-1])
        }
        
        return metrics
